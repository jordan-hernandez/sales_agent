import pandas as pd
import PyPDF2
import openpyxl
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.restaurant import Restaurant
from app.core.database import get_db
from typing import List, Dict, Any, Optional
import re
import logging
from datetime import datetime
import io
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class InventorySyncService:
    """Service for synchronizing inventory from various sources"""
    
    def __init__(self):
        self.supported_formats = ['pdf', 'xlsx', 'xls', 'csv']
        self.required_columns = ['nombre', 'precio', 'categoria']  # Spanish column names
        self.optional_columns = ['descripcion', 'disponible', 'imagen']
    
    def sync_from_file(self, file_path: str, restaurant_id: int, db: Session) -> Dict[str, Any]:
        """Main method to sync inventory from file"""
        try:
            file_extension = Path(file_path).suffix.lower()[1:]  # Remove the dot
            
            if file_extension not in self.supported_formats:
                return {"error": f"Formato no soportado: {file_extension}"}
            
            # Extract data based on file type
            if file_extension == 'pdf':
                data = self._extract_from_pdf(file_path)
            elif file_extension in ['xlsx', 'xls']:
                data = self._extract_from_excel(file_path)
            elif file_extension == 'csv':
                data = self._extract_from_csv(file_path)
            
            if not data:
                return {"error": "No se pudieron extraer datos del archivo"}
            
            # Validate and process data
            validated_data = self._validate_data(data)
            if not validated_data:
                return {"error": "Los datos no tienen el formato correcto"}
            
            # Update database
            result = self._update_inventory(validated_data, restaurant_id, db)
            
            return {
                "success": True,
                "message": f"Sincronización completada",
                "stats": result
            }
            
        except Exception as e:
            logger.error(f"Error syncing from file {file_path}: {e}")
            return {"error": f"Error durante la sincronización: {str(e)}"}
    
    def _extract_from_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract menu data from PDF"""
        try:
            products = []
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page in pdf_reader.pages:
                    text += page.extract_text()
                
                # Parse menu items using regex patterns
                # Pattern for: "Product Name - Description $Price"
                pattern = r'([A-Za-záéíóúñÁÉÍÓÚÑ\s]+)\s*[-–]\s*([^$]+)\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)'
                matches = re.findall(pattern, text)
                
                for match in matches:
                    name = match[0].strip()
                    description = match[1].strip()
                    price_str = match[2].replace('.', '').replace(',', '.')
                    
                    try:
                        price = float(price_str)
                        products.append({
                            'nombre': name,
                            'descripcion': description,
                            'precio': price,
                            'categoria': self._guess_category(name, description),
                            'disponible': True
                        })
                    except ValueError:
                        continue
                
                # Alternative pattern for simpler format: "Product Name $Price"
                if not products:
                    pattern2 = r'([A-Za-záéíóúñÁÉÍÓÚÑ\s]+)\s*\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)'
                    matches2 = re.findall(pattern2, text)
                    
                    for match in matches2:
                        name = match[0].strip()
                        price_str = match[1].replace('.', '').replace(',', '.')
                        
                        try:
                            price = float(price_str)
                            products.append({
                                'nombre': name,
                                'descripcion': '',
                                'precio': price,
                                'categoria': self._guess_category(name, ''),
                                'disponible': True
                            })
                        except ValueError:
                            continue
            
            return products
            
        except Exception as e:
            logger.error(f"Error extracting from PDF: {e}")
            return []
    
    def _extract_from_excel(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract menu data from Excel file"""
        try:
            # Try different sheet names and encodings
            possible_sheets = [0, 'Menu', 'Menú', 'Products', 'Productos', 'Inventory', 'Inventario']
            
            df = None
            for sheet in possible_sheets:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet)
                    if not df.empty:
                        break
                except:
                    continue
            
            if df is None or df.empty:
                return []
            
            # Normalize column names
            df.columns = df.columns.str.lower().str.strip()
            
            # Map common column variations
            column_mapping = {
                'name': 'nombre',
                'product': 'nombre',
                'producto': 'nombre',
                'item': 'nombre',
                'price': 'precio',
                'cost': 'precio',
                'costo': 'precio',
                'valor': 'precio',
                'category': 'categoria',
                'categoría': 'categoria',
                'tipo': 'categoria',
                'description': 'descripcion',
                'descripción': 'descripcion',
                'desc': 'descripcion',
                'available': 'disponible',
                'disponible': 'disponible',
                'activo': 'disponible',
                'stock': 'disponible'
            }
            
            # Rename columns
            df = df.rename(columns=column_mapping)
            
            # Convert to list of dictionaries
            products = []
            for _, row in df.iterrows():
                if pd.isna(row.get('nombre')) or pd.isna(row.get('precio')):
                    continue
                
                product = {
                    'nombre': str(row['nombre']).strip(),
                    'precio': self._parse_price(row['precio']),
                    'categoria': str(row.get('categoria', '')).strip().lower() or self._guess_category(str(row['nombre']), ''),
                    'descripcion': str(row.get('descripcion', '')).strip(),
                    'disponible': self._parse_boolean(row.get('disponible', True))
                }
                
                if product['precio'] > 0:
                    products.append(product)
            
            return products
            
        except Exception as e:
            logger.error(f"Error extracting from Excel: {e}")
            return []
    
    def _extract_from_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract menu data from CSV file"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except:
                    continue
            
            if df is None:
                return []
            
            # Use same processing as Excel
            return self._extract_from_excel_df(df)
            
        except Exception as e:
            logger.error(f"Error extracting from CSV: {e}")
            return []
    
    def _extract_from_excel_df(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Helper method to process DataFrame (shared between Excel and CSV)"""
        # Normalize column names
        df.columns = df.columns.str.lower().str.strip()
        
        # Map common column variations
        column_mapping = {
            'name': 'nombre',
            'product': 'nombre',
            'producto': 'nombre',
            'item': 'nombre',
            'price': 'precio',
            'cost': 'precio',
            'costo': 'precio',
            'valor': 'precio',
            'category': 'categoria',
            'categoría': 'categoria',
            'tipo': 'categoria',
            'description': 'descripcion',
            'descripción': 'descripcion',
            'desc': 'descripcion',
            'available': 'disponible',
            'disponible': 'disponible',
            'activo': 'disponible',
            'stock': 'disponible'
        }
        
        # Rename columns
        df = df.rename(columns=column_mapping)
        
        # Convert to list of dictionaries
        products = []
        for _, row in df.iterrows():
            if pd.isna(row.get('nombre')) or pd.isna(row.get('precio')):
                continue
            
            product = {
                'nombre': str(row['nombre']).strip(),
                'precio': self._parse_price(row['precio']),
                'categoria': str(row.get('categoria', '')).strip().lower() or self._guess_category(str(row['nombre']), ''),
                'descripcion': str(row.get('descripcion', '')).strip(),
                'disponible': self._parse_boolean(row.get('disponible', True))
            }
            
            if product['precio'] > 0:
                products.append(product)
        
        return products
    
    def _validate_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate extracted data"""
        validated = []
        
        for item in data:
            if not item.get('nombre') or not item.get('precio'):
                continue
                
            # Ensure required fields
            validated_item = {
                'nombre': str(item['nombre']).strip()[:200],  # Limit length
                'precio': max(0, float(item['precio'])),
                'categoria': str(item.get('categoria', 'general')).strip().lower()[:50],
                'descripcion': str(item.get('descripcion', '')).strip()[:500],
                'disponible': bool(item.get('disponible', True))
            }
            
            validated.append(validated_item)
        
        return validated
    
    def _update_inventory(self, products: List[Dict[str, Any]], restaurant_id: int, db: Session) -> Dict[str, int]:
        """Update database with new inventory"""
        stats = {'created': 0, 'updated': 0, 'errors': 0}
        
        try:
            for product_data in products:
                try:
                    # Check if product already exists
                    existing_product = db.query(Product).filter(
                        Product.restaurant_id == restaurant_id,
                        Product.name.ilike(f"%{product_data['nombre']}%")
                    ).first()
                    
                    if existing_product:
                        # Update existing product
                        existing_product.description = product_data['descripcion']
                        existing_product.price = product_data['precio']
                        existing_product.category = product_data['categoria']
                        existing_product.available = product_data['disponible']
                        stats['updated'] += 1
                    else:
                        # Create new product
                        new_product = Product(
                            restaurant_id=restaurant_id,
                            name=product_data['nombre'],
                            description=product_data['descripcion'],
                            price=product_data['precio'],
                            category=product_data['categoria'],
                            available=product_data['disponible']
                        )
                        db.add(new_product)
                        stats['created'] += 1
                
                except Exception as e:
                    logger.error(f"Error processing product {product_data.get('nombre', 'unknown')}: {e}")
                    stats['errors'] += 1
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating inventory: {e}")
            db.rollback()
            raise
        
        return stats
    
    def _parse_price(self, price_value) -> float:
        """Parse price from various formats"""
        if pd.isna(price_value):
            return 0.0
        
        # Convert to string and clean
        price_str = str(price_value).strip()
        
        # Remove currency symbols and common separators
        price_str = re.sub(r'[$€£¥₹₩₪₱₡₫₦₨₵₴₽₾₸₼₺₷₹]', '', price_str)
        price_str = re.sub(r'[,.](?=\d{3})', '', price_str)  # Remove thousands separators
        price_str = price_str.replace(',', '.')  # Replace decimal comma with dot
        
        try:
            return float(price_str)
        except ValueError:
            return 0.0
    
    def _parse_boolean(self, value) -> bool:
        """Parse boolean from various formats"""
        if pd.isna(value):
            return True
        
        if isinstance(value, bool):
            return value
        
        value_str = str(value).lower().strip()
        return value_str not in ['false', 'no', '0', 'inactive', 'inactivo', 'unavailable']
    
    def _guess_category(self, name: str, description: str) -> str:
        """Guess category based on product name and description"""
        text = f"{name} {description}".lower()
        
        # Colombian food categories
        if any(word in text for word in ['empanada', 'arepa', 'patacon', 'chicharron']):
            return 'entradas'
        elif any(word in text for word in ['bandeja', 'sancocho', 'pescado', 'pollo', 'carne', 'arroz']):
            return 'platos principales'
        elif any(word in text for word in ['jugo', 'gaseosa', 'agua', 'limonada', 'cafe', 'té']):
            return 'bebidas'
        elif any(word in text for word in ['postre', 'torta', 'flan', 'helado', 'brownie', 'tres leches']):
            return 'postres'
        elif any(word in text for word in ['sopa', 'crema', 'consomé']):
            return 'sopas'
        else:
            return 'general'
    
    def sync_from_google_sheets(self, spreadsheet_id: str, range_name: str, restaurant_id: int, db: Session, credentials_path: str) -> Dict[str, Any]:
        """Sync inventory from Google Sheets"""
        try:
            # Load credentials
            if not os.path.exists(credentials_path):
                return {"error": "Archivo de credenciales no encontrado"}
            
            creds = Credentials.from_authorized_user_file(credentials_path)
            service = build('sheets', 'v4', credentials=creds)
            
            # Get data from sheet
            sheet = service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return {"error": "No se encontraron datos en la hoja"}
            
            # Convert to DataFrame
            df = pd.DataFrame(values[1:], columns=values[0])  # First row as headers
            
            # Process using existing Excel logic
            products = self._extract_from_excel_df(df)
            
            if not products:
                return {"error": "No se pudieron procesar los datos"}
            
            # Validate and update
            validated_data = self._validate_data(products)
            result = self._update_inventory(validated_data, restaurant_id, db)
            
            return {
                "success": True,
                "message": "Sincronización desde Google Sheets completada",
                "stats": result
            }
            
        except Exception as e:
            logger.error(f"Error syncing from Google Sheets: {e}")
            return {"error": f"Error sincronizando desde Google Sheets: {str(e)}"}


# Global instance
inventory_sync_service = InventorySyncService()