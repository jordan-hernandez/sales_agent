from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.inventory_sync import inventory_sync_service
from app.models.restaurant import Restaurant
from pydantic import BaseModel
from typing import List, Optional
import tempfile
import os
import shutil
from pathlib import Path

router = APIRouter()


class SyncResult(BaseModel):
    success: bool
    message: str
    stats: Optional[dict] = None
    error: Optional[str] = None


class GoogleSheetsSyncRequest(BaseModel):
    spreadsheet_id: str
    range_name: str = "A:Z"  # Default range
    restaurant_id: int


@router.post("/upload-file/{restaurant_id}", response_model=SyncResult)
async def upload_and_sync_inventory(
    restaurant_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and sync inventory from PDF/Excel/CSV file"""
    
    # Verify restaurant exists
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    # Validate file type
    allowed_extensions = {'.pdf', '.xlsx', '.xls', '.csv'}
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Save uploaded file temporarily
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_file_path = tmp_file.name
        
        # Process the file
        result = inventory_sync_service.sync_from_file(tmp_file_path, restaurant_id, db)
        
        # Clean up temporary file
        os.unlink(tmp_file_path)
        
        return SyncResult(**result)
        
    except Exception as e:
        # Clean up temporary file if it exists
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.post("/sync-google-sheets", response_model=SyncResult)
def sync_from_google_sheets(
    request: GoogleSheetsSyncRequest,
    credentials_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Sync inventory from Google Sheets"""
    
    # Verify restaurant exists
    restaurant = db.query(Restaurant).filter(Restaurant.id == request.restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    # Validate credentials file
    if not credentials_file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Credentials file must be JSON")
    
    try:
        # Save credentials temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_creds:
            shutil.copyfileobj(credentials_file.file, tmp_creds)
            tmp_creds_path = tmp_creds.name
        
        # Process Google Sheets
        result = inventory_sync_service.sync_from_google_sheets(
            request.spreadsheet_id,
            request.range_name,
            request.restaurant_id,
            db,
            tmp_creds_path
        )
        
        # Clean up credentials file
        os.unlink(tmp_creds_path)
        
        return SyncResult(**result)
        
    except Exception as e:
        # Clean up credentials file if it exists
        if 'tmp_creds_path' in locals():
            try:
                os.unlink(tmp_creds_path)
            except:
                pass
        
        raise HTTPException(status_code=500, detail=f"Error syncing from Google Sheets: {str(e)}")


@router.get("/sync-history/{restaurant_id}")
def get_sync_history(restaurant_id: int, db: Session = Depends(get_db)):
    """Get synchronization history for a restaurant"""
    
    # Verify restaurant exists
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    # For MVP, return a simple message
    # In a full implementation, you'd store sync logs in the database
    return {
        "message": "Sync history feature not implemented in MVP",
        "restaurant_id": restaurant_id,
        "last_sync": None
    }


@router.get("/supported-formats")
def get_supported_formats():
    """Get list of supported file formats for inventory sync"""
    return {
        "formats": [
            {
                "extension": ".pdf",
                "description": "PDF files with menu data",
                "example_format": "Product Name - Description $Price"
            },
            {
                "extension": ".xlsx",
                "description": "Excel files with columns: nombre, precio, categoria",
                "example_format": "Spreadsheet with headers"
            },
            {
                "extension": ".xls",
                "description": "Legacy Excel files",
                "example_format": "Spreadsheet with headers"
            },
            {
                "extension": ".csv",
                "description": "CSV files with columns: nombre, precio, categoria",
                "example_format": "Comma-separated values"
            }
        ],
        "required_columns": ["nombre", "precio"],
        "optional_columns": ["categoria", "descripcion", "disponible"],
        "google_sheets": {
            "supported": True,
            "requirements": "Google Sheets API credentials JSON file"
        }
    }


@router.post("/create-sample-files/{restaurant_id}")
def create_sample_files(restaurant_id: int, db: Session = Depends(get_db)):
    """Create sample files for testing inventory sync"""
    
    # Verify restaurant exists
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    # Create sample data
    sample_data = [
        {
            "nombre": "Empanadas de Pollo",
            "descripcion": "Deliciosas empanadas caseras rellenas de pollo",
            "precio": 8000,
            "categoria": "entradas",
            "disponible": True
        },
        {
            "nombre": "Bandeja Paisa",
            "descripcion": "Plato tradicional con frijoles, arroz, carne, chorizo",
            "precio": 28000,
            "categoria": "platos principales",
            "disponible": True
        },
        {
            "nombre": "Limonada de Coco",
            "descripcion": "Refrescante bebida con coco",
            "precio": 8000,
            "categoria": "bebidas",
            "disponible": True
        }
    ]
    
    return {
        "message": "Sample data for testing",
        "csv_format": "nombre,descripcion,precio,categoria,disponible",
        "sample_data": sample_data,
        "instructions": {
            "pdf": "Create a PDF with format: 'Product Name - Description $Price'",
            "excel": "Create Excel with columns: nombre, descripcion, precio, categoria, disponible",
            "csv": "Create CSV with same columns as Excel",
            "google_sheets": "Create Google Sheet with same structure and share with service account"
        }
    }