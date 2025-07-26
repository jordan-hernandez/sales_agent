from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.services.menu_service import MenuService
from app.models.product import Product
from pydantic import BaseModel

router = APIRouter()


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    category: str
    available: bool
    image_url: str | None

    class Config:
        from_attributes = True


@router.get("/restaurant/{restaurant_id}/menu", response_model=List[ProductResponse])
def get_restaurant_menu(restaurant_id: int, db: Session = Depends(get_db)):
    """Get full menu for a restaurant"""
    products = MenuService.get_restaurant_menu(db, restaurant_id)
    return products


@router.get("/restaurant/{restaurant_id}/menu/categories")
def get_menu_categories(restaurant_id: int, db: Session = Depends(get_db)):
    """Get all categories for a restaurant"""
    categories = MenuService.get_categories(db, restaurant_id)
    return {"categories": categories}


@router.get("/restaurant/{restaurant_id}/menu/category/{category}", response_model=List[ProductResponse])
def get_menu_by_category(restaurant_id: int, category: str, db: Session = Depends(get_db)):
    """Get menu items by category"""
    products = MenuService.get_menu_by_category(db, restaurant_id, category)
    return products


@router.get("/restaurant/{restaurant_id}/menu/search", response_model=List[ProductResponse])
def search_menu(restaurant_id: int, q: str, db: Session = Depends(get_db)):
    """Search menu items"""
    if len(q) < 2:
        raise HTTPException(status_code=400, detail="Search term must be at least 2 characters")
    
    products = MenuService.search_products(db, restaurant_id, q)
    return products


@router.post("/restaurant/{restaurant_id}/menu/sample")
def create_sample_menu(restaurant_id: int, db: Session = Depends(get_db)):
    """Create sample menu for testing (MVP only)"""
    MenuService.create_sample_menu(db, restaurant_id)
    return {"message": "Sample menu created successfully"}