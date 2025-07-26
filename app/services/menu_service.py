from sqlalchemy.orm import Session
from app.models.restaurant import Restaurant
from app.models.product import Product
from typing import List, Optional


class MenuService:
    @staticmethod
    def get_restaurant_menu(db: Session, restaurant_id: int) -> List[Product]:
        """Get all available products for a restaurant"""
        return db.query(Product).filter(
            Product.restaurant_id == restaurant_id,
            Product.available == True
        ).all()

    @staticmethod
    def get_menu_by_category(db: Session, restaurant_id: int, category: str) -> List[Product]:
        """Get products by category for a restaurant"""
        return db.query(Product).filter(
            Product.restaurant_id == restaurant_id,
            Product.category == category,
            Product.available == True
        ).all()

    @staticmethod
    def get_categories(db: Session, restaurant_id: int) -> List[str]:
        """Get all categories for a restaurant"""
        categories = db.query(Product.category).filter(
            Product.restaurant_id == restaurant_id,
            Product.available == True
        ).distinct().all()
        return [cat[0] for cat in categories]

    @staticmethod
    def search_products(db: Session, restaurant_id: int, search_term: str) -> List[Product]:
        """Search products by name or description"""
        return db.query(Product).filter(
            Product.restaurant_id == restaurant_id,
            Product.available == True,
            (Product.name.ilike(f"%{search_term}%") | 
             Product.description.ilike(f"%{search_term}%"))
        ).all()

    @staticmethod
    def create_sample_menu(db: Session, restaurant_id: int):
        """Create sample menu for MVP testing"""
        sample_products = [
            # Entradas
            {
                "name": "Empanadas de Pollo",
                "description": "Deliciosas empanadas caseras rellenas de pollo y verduras",
                "price": 8000,
                "category": "entradas"
            },
            {
                "name": "Patacones con Guacamole",
                "description": "Patacones crujientes acompañados de guacamole fresco",
                "price": 12000,
                "category": "entradas"
            },
            {
                "name": "Arepa de Queso",
                "description": "Arepa tradicional rellena de queso campesino",
                "price": 6000,
                "category": "entradas"
            },
            
            # Platos Principales
            {
                "name": "Bandeja Paisa",
                "description": "Bandeja tradicional con frijoles, arroz, carne molida, chorizo, morcilla, chicharrón, arepa y aguacate",
                "price": 28000,
                "category": "platos principales"
            },
            {
                "name": "Sancocho de Gallina",
                "description": "Sancocho tradicional con gallina criolla y vegetales frescos",
                "price": 25000,
                "category": "platos principales"
            },
            {
                "name": "Pescado a la Plancha",
                "description": "Filete de pescado fresco a la plancha con arroz con coco y patacones",
                "price": 32000,
                "category": "platos principales"
            },
            {
                "name": "Pollo Asado",
                "description": "Pollo entero asado con papas criollas y ensalada",
                "price": 24000,
                "category": "platos principales"
            },
            
            # Bebidas
            {
                "name": "Limonada de Coco",
                "description": "Refrescante limonada con coco rallado",
                "price": 8000,
                "category": "bebidas"
            },
            {
                "name": "Agua de Panela con Limón",
                "description": "Bebida tradicional colombiana",
                "price": 5000,
                "category": "bebidas"
            },
            {
                "name": "Jugo Natural",
                "description": "Jugos de frutas frescas (mango, mora, lulo, maracuyá)",
                "price": 9000,
                "category": "bebidas"
            },
            {
                "name": "Gaseosa",
                "description": "Coca Cola, Sprite, Fanta",
                "price": 4000,
                "category": "bebidas"
            },
            
            # Postres
            {
                "name": "Tres Leches",
                "description": "Torta tres leches casera",
                "price": 8000,
                "category": "postres"
            },
            {
                "name": "Flan de Coco",
                "description": "Flan tradicional con sabor a coco",
                "price": 7000,
                "category": "postres"
            },
            {
                "name": "Brownie con Helado",
                "description": "Brownie de chocolate con helado de vainilla",
                "price": 10000,
                "category": "postres"
            }
        ]

        for product_data in sample_products:
            existing_product = db.query(Product).filter(
                Product.restaurant_id == restaurant_id,
                Product.name == product_data["name"]
            ).first()
            
            if not existing_product:
                product = Product(
                    restaurant_id=restaurant_id,
                    **product_data
                )
                db.add(product)
        
        db.commit()