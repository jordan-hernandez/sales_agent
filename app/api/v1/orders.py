from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.conversation import Conversation
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    notes: str | None

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    customer_name: str
    customer_phone: str
    delivery_address: str | None
    subtotal: float
    delivery_fee: float
    total: float
    status: OrderStatus
    payment_status: PaymentStatus
    created_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True


@router.get("/restaurant/{restaurant_id}/orders", response_model=List[OrderResponse])
def get_restaurant_orders(restaurant_id: int, db: Session = Depends(get_db)):
    """Get all orders for a restaurant"""
    orders = db.query(Order).filter(Order.restaurant_id == restaurant_id).all()
    
    # Transform orders to include product names
    result = []
    for order in orders:
        order_dict = {
            "id": order.id,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "delivery_address": order.delivery_address,
            "subtotal": order.subtotal,
            "delivery_fee": order.delivery_fee,
            "total": order.total,
            "status": order.status,
            "payment_status": order.payment_status,
            "created_at": order.created_at,
            "items": []
        }
        
        for item in order.items:
            order_dict["items"].append({
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product.name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "notes": item.notes
            })
        
        result.append(order_dict)
    
    return result


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    """Get specific order details"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order_dict = {
        "id": order.id,
        "customer_name": order.customer_name,
        "customer_phone": order.customer_phone,
        "delivery_address": order.delivery_address,
        "subtotal": order.subtotal,
        "delivery_fee": order.delivery_fee,
        "total": order.total,
        "status": order.status,
        "payment_status": order.payment_status,
        "created_at": order.created_at,
        "items": []
    }
    
    for item in order.items:
        order_dict["items"].append({
            "id": item.id,
            "product_id": item.product_id,
            "product_name": item.product.name,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "notes": item.notes
        })
    
    return order_dict


class UpdateOrderStatusRequest(BaseModel):
    status: OrderStatus


@router.patch("/orders/{order_id}/status")
def update_order_status(order_id: int, request: UpdateOrderStatusRequest, db: Session = Depends(get_db)):
    """Update order status"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.status = request.status
    db.commit()
    
    return {"message": f"Order status updated to {request.status}"}