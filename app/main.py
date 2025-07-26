from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db, engine
from app.models.restaurant import Restaurant
from app.models.product import Product
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.order import Order, OrderItem
from app.api.v1 import menu, orders, payments, inventory, sync_schedule, agent, vectors
from app.services.menu_service import MenuService
from app.core.database import Base
import asyncio
import threading

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.project_name,
    version="1.0.0",
    description="Sales Agent API for Restaurants"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(menu.router, prefix=f"{settings.api_v1_str}/menu", tags=["menu"])
app.include_router(orders.router, prefix=f"{settings.api_v1_str}/orders", tags=["orders"])
app.include_router(payments.router, prefix=f"{settings.api_v1_str}/payments", tags=["payments"])
app.include_router(inventory.router, prefix=f"{settings.api_v1_str}/inventory", tags=["inventory"])
app.include_router(sync_schedule.router, prefix=f"{settings.api_v1_str}/sync", tags=["sync-schedule"])
app.include_router(agent.router, prefix=f"{settings.api_v1_str}/agent", tags=["conversational-agent"])
app.include_router(vectors.router, prefix=f"{settings.api_v1_str}/vectors", tags=["vector-search"])


@app.get("/")
def read_root():
    return {"message": "Sales Agent API for Restaurants", "version": "1.0.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/setup")
def setup_demo_data(db: Session = Depends(get_db)):
    """Setup demo restaurant and sample menu for MVP testing"""
    
    # Check if demo restaurant already exists
    restaurant = db.query(Restaurant).filter(Restaurant.name == "Restaurante Demo").first()
    
    if not restaurant:
        # Create demo restaurant
        restaurant = Restaurant(
            name="Restaurante Demo",
            description="Restaurante de demostración para el MVP",
            phone="+57 123 456 7890",
            config={
                "delivery_fee": 3000,
                "min_order": 15000,
                "delivery_time": "30-45 minutos"
            },
            active=True
        )
        db.add(restaurant)
        db.commit()
        db.refresh(restaurant)
        
        # Create sample menu
        MenuService.create_sample_menu(db, restaurant.id)
        
        # Create embeddings for the sample menu
        try:
            from app.services.vector_search import vector_search_service
            embedding_stats = vector_search_service.create_product_embeddings(restaurant.id, db)
            print(f"Created embeddings: {embedding_stats}")
        except Exception as e:
            print(f"Warning: Could not create embeddings: {e}")
        
        return {
            "message": "Demo data created successfully",
            "restaurant_id": restaurant.id,
            "restaurant_name": restaurant.name,
            "embeddings_created": True
        }
    else:
        return {
            "message": "Demo data already exists",
            "restaurant_id": restaurant.id,
            "restaurant_name": restaurant.name
        }


def start_telegram_bot():
    """Start Telegram bot in a separate thread"""
    import asyncio
    try:
        from app.services.telegram_service import telegram_bot
        if settings.telegram_bot_token:
            # Create new event loop for the thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            telegram_bot.run()
        else:
            print("Telegram bot token not configured. Bot will not start.")
    except Exception as e:
        print(f"Error starting Telegram bot: {e}")


def start_inventory_scheduler():
    """Start inventory scheduler in a separate thread"""
    try:
        from app.services.scheduler import inventory_scheduler
        inventory_scheduler.start()
        print("Inventory scheduler started")
    except Exception as e:
        print(f"Error starting inventory scheduler: {e}")


@app.on_event("startup")
async def startup_event():
    """Start services on application startup"""
    print(f"Starting {settings.project_name}...")
    
    # Start Telegram bot in background thread if token is configured
    if settings.telegram_bot_token and settings.telegram_bot_token != "":
        bot_thread = threading.Thread(target=start_telegram_bot, daemon=True)
        bot_thread.start()
        print("Telegram bot started in background")
    else:
        print("Telegram bot token not configured. Set TELEGRAM_BOT_TOKEN in .env file to enable bot.")
    
    # Start inventory scheduler
    scheduler_thread = threading.Thread(target=start_inventory_scheduler, daemon=True)
    scheduler_thread.start()
    print("Inventory scheduler started in background")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )