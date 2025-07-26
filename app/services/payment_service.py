import mercadopago
from app.core.config import settings
from app.models.order import Order, PaymentStatus
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self):
        if settings.mercadopago_access_token:
            self.sdk = mercadopago.SDK(settings.mercadopago_access_token)
        else:
            self.sdk = None
            logger.warning("Mercado Pago access token not configured")

    def create_payment_preference(self, order: Order) -> Dict[str, Any]:
        """Create payment preference for Mercado Pago"""
        if not self.sdk:
            return {"error": "Payment service not configured"}

        try:
            # Build items for the preference
            items = []
            for item in order.items:
                items.append({
                    "id": str(item.product_id),
                    "title": item.product.name,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "currency_id": "COP"
                })

            # Add delivery fee if applicable
            if order.delivery_fee > 0:
                items.append({
                    "id": "delivery",
                    "title": "Costo de entrega",
                    "quantity": 1,
                    "unit_price": float(order.delivery_fee),
                    "currency_id": "COP"
                })

            preference_data = {
                "items": items,
                "payer": {
                    "name": order.customer_name,
                    "phone": {
                        "number": order.customer_phone
                    }
                },
                "payment_methods": {
                    "excluded_payment_methods": [],
                    "excluded_payment_types": [],
                    "installments": 12
                },
                "back_urls": {
                    "success": f"{settings.api_v1_str}/payments/success",
                    "failure": f"{settings.api_v1_str}/payments/failure",
                    "pending": f"{settings.api_v1_str}/payments/pending"
                },
                "auto_return": "approved",
                "external_reference": str(order.id),
                "statement_descriptor": "RESTAURANTE DEMO",
                "notification_url": f"{settings.api_v1_str}/payments/webhook"
            }

            result = self.sdk.preference().create(preference_data)
            
            if result["status"] == 201:
                return {
                    "preference_id": result["response"]["id"],
                    "init_point": result["response"]["init_point"],
                    "sandbox_init_point": result["response"]["sandbox_init_point"]
                }
            else:
                logger.error(f"Error creating payment preference: {result}")
                return {"error": "Failed to create payment preference"}
                
        except Exception as e:
            logger.error(f"Exception creating payment preference: {e}")
            return {"error": str(e)}

    def process_webhook_notification(self, notification_data: Dict[str, Any], db: Session):
        """Process Mercado Pago webhook notification"""
        if not self.sdk:
            logger.error("Payment service not configured")
            return

        try:
            notification_type = notification_data.get("type")
            
            if notification_type == "payment":
                payment_id = notification_data.get("data", {}).get("id")
                
                if payment_id:
                    payment_info = self.sdk.payment().get(payment_id)
                    
                    if payment_info["status"] == 200:
                        payment = payment_info["response"]
                        order_id = payment.get("external_reference")
                        
                        if order_id:
                            order = db.query(Order).filter(Order.id == int(order_id)).first()
                            
                            if order:
                                self.update_order_payment_status(order, payment, db)
                                
        except Exception as e:
            logger.error(f"Error processing webhook notification: {e}")

    def update_order_payment_status(self, order: Order, payment_data: Dict[str, Any], db: Session):
        """Update order payment status based on Mercado Pago response"""
        try:
            payment_status = payment_data.get("status")
            
            if payment_status == "approved":
                order.payment_status = PaymentStatus.PAID
                order.payment_id = str(payment_data.get("id"))
                order.payment_method = payment_data.get("payment_method_id")
                
            elif payment_status in ["rejected", "cancelled"]:
                order.payment_status = PaymentStatus.FAILED
                
            elif payment_status in ["pending", "in_process"]:
                order.payment_status = PaymentStatus.PENDING
                
            db.commit()
            logger.info(f"Order {order.id} payment status updated to {order.payment_status}")
            
        except Exception as e:
            logger.error(f"Error updating order payment status: {e}")

    def create_simple_payment_link(self, order: Order) -> str:
        """Create a simple payment link for MVP (mock implementation)"""
        # For MVP, return a mock payment link
        # In production, this would create actual payment links
        base_url = "https://checkout.mercadopago.com.co"
        return f"{base_url}/checkout/v1/redirect?pref_id=mock_preference_{order.id}"

    def simulate_payment_success(self, order: Order, db: Session):
        """Simulate successful payment for MVP testing"""
        order.payment_status = PaymentStatus.PAID
        order.payment_id = f"mock_payment_{order.id}"
        order.payment_method = "credit_card"
        db.commit()
        logger.info(f"Simulated payment success for order {order.id}")


# Global instance
payment_service = PaymentService()