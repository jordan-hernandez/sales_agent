from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.order import Order
from app.services.payment_service import payment_service
from pydantic import BaseModel

router = APIRouter()


class PaymentPreferenceRequest(BaseModel):
    order_id: int


class PaymentPreferenceResponse(BaseModel):
    preference_id: str | None
    payment_url: str
    order_id: int


@router.post("/create-preference", response_model=PaymentPreferenceResponse)
def create_payment_preference(request: PaymentPreferenceRequest, db: Session = Depends(get_db)):
    """Create payment preference for an order"""
    order = db.query(Order).filter(Order.id == request.order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # For MVP, create a mock payment preference
    result = payment_service.create_payment_preference(order)
    
    if "error" in result:
        # Fallback to simple payment link for MVP
        payment_url = payment_service.create_simple_payment_link(order)
        return PaymentPreferenceResponse(
            preference_id=None,
            payment_url=payment_url,
            order_id=order.id
        )
    else:
        return PaymentPreferenceResponse(
            preference_id=result.get("preference_id"),
            payment_url=result.get("init_point", result.get("sandbox_init_point")),
            order_id=order.id
        )


@router.post("/webhook")
async def payment_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Mercado Pago webhook notifications"""
    try:
        notification_data = await request.json()
        payment_service.process_webhook_notification(notification_data, db)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/success")
def payment_success(payment_id: str = None, status: str = None, external_reference: str = None, db: Session = Depends(get_db)):
    """Handle successful payment redirect"""
    if external_reference:
        order = db.query(Order).filter(Order.id == int(external_reference)).first()
        if order:
            payment_service.simulate_payment_success(order, db)
            return {"message": "Payment successful", "order_id": order.id}
    
    return {"message": "Payment processed"}


@router.get("/failure")
def payment_failure(payment_id: str = None, status: str = None, external_reference: str = None):
    """Handle failed payment redirect"""
    return {"message": "Payment failed", "order_id": external_reference}


@router.get("/pending")
def payment_pending(payment_id: str = None, status: str = None, external_reference: str = None):
    """Handle pending payment redirect"""
    return {"message": "Payment pending", "order_id": external_reference}


@router.post("/simulate-payment/{order_id}")
def simulate_payment(order_id: int, db: Session = Depends(get_db)):
    """Simulate payment for MVP testing"""
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    payment_service.simulate_payment_success(order, db)
    return {"message": f"Payment simulated successfully for order {order_id}"}