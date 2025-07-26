#!/usr/bin/env python3
"""
Script para inicializar el MVP del Sales Agent
Este script configura la base de datos y datos de demostración
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from app.core.config import settings
from app.core.database import Base
from app.models.restaurant import Restaurant
from app.models.product import Product
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.order import Order, OrderItem
from app.services.menu_service import MenuService
from sqlalchemy.orm import sessionmaker


def create_database_tables():
    """Crear tablas de la base de datos"""
    print("🔧 Creando tablas de la base de datos...")
    engine = create_engine(settings.database_url)
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas exitosamente")
    return engine


def setup_demo_data(engine):
    """Configurar datos de demostración"""
    print("📦 Configurando datos de demostración...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Verificar si ya existe el restaurante demo
        existing_restaurant = db.query(Restaurant).filter(
            Restaurant.name == "Restaurante Demo"
        ).first()
        
        if existing_restaurant:
            print("⚠️  Los datos de demostración ya existen")
            return existing_restaurant.id
        
        # Crear restaurante demo
        restaurant = Restaurant(
            name="Restaurante Demo",
            description="Restaurante de demostración para el MVP",
            phone="+57 123 456 7890",
            config={
                "delivery_fee": 3000,
                "min_order": 15000,
                "delivery_time": "30-45 minutos",
                "welcome_message": "¡Bienvenido a nuestro restaurante! ¿En qué puedo ayudarte?"
            },
            active=True
        )
        db.add(restaurant)
        db.commit()
        db.refresh(restaurant)
        
        # Crear menú de muestra
        MenuService.create_sample_menu(db, restaurant.id)
        
        print(f"✅ Restaurante demo creado: ID {restaurant.id}")
        print(f"✅ Menú de muestra creado con productos colombianos")
        
        return restaurant.id
        
    except Exception as e:
        print(f"❌ Error configurando datos de demostración: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def print_instructions(restaurant_id):
    """Imprimir instrucciones para usar el MVP"""
    print("\n" + "="*60)
    print("🎉 MVP DEL SALES AGENT CONFIGURADO EXITOSAMENTE")
    print("="*60)
    
    print(f"\n📋 INFORMACIÓN DEL SISTEMA:")
    print(f"   • Restaurante ID: {restaurant_id}")
    print(f"   • Base de datos: Configurada")
    print(f"   • Menú: 15+ productos colombianos creados")
    
    print(f"\n🚀 PARA INICIAR EL SISTEMA:")
    print(f"   1. Backend API:")
    print(f"      python app/main.py")
    print(f"      o: uvicorn app.main:app --reload")
    print(f"   ")
    print(f"   2. Frontend Dashboard:")
    print(f"      cd frontend")
    print(f"      npm install && npm start")
    
    print(f"\n🤖 CONFIGURAR BOT DE TELEGRAM:")
    print(f"   1. Crear bot en @BotFather")
    print(f"   2. Agregar token al archivo .env:")
    print(f"      TELEGRAM_BOT_TOKEN=tu_token_aqui")
    print(f"   3. Reiniciar el backend")
    
    print(f"\n🌐 ACCEDER AL SISTEMA:")
    print(f"   • Dashboard: http://localhost:3000")
    print(f"   • API Docs: http://localhost:8000/docs")
    print(f"   • Health Check: http://localhost:8000/health")
    
    print(f"\n💳 CONFIGURAR PAGOS (OPCIONAL):")
    print(f"   1. Obtener access token de Mercado Pago")
    print(f"   2. Agregar al archivo .env:")
    print(f"      MERCADOPAGO_ACCESS_TOKEN=tu_token_aqui")
    
    print(f"\n📱 PROBAR EL BOT:")
    print(f"   1. Buscar tu bot en Telegram")
    print(f"   2. Enviar: /start")
    print(f"   3. Explorar menú y hacer pedidos de prueba")
    
    print(f"\n🎯 PRÓXIMOS PASOS:")
    print(f"   • Personalizar menú desde el dashboard")
    print(f"   • Configurar datos reales del restaurante")
    print(f"   • Probar flujo completo de pedidos")
    print(f"   • Configurar WhatsApp (Fase 2)")
    
    print("\n" + "="*60)


def main():
    """Función principal para configurar el MVP"""
    print("🚀 INICIALIZANDO MVP DEL SALES AGENT PARA RESTAURANTES")
    print("="*60)
    
    try:
        # Verificar configuración
        if not settings.database_url:
            print("❌ Error: DATABASE_URL no configurada en .env")
            return
        
        # Crear tablas
        engine = create_database_tables()
        
        # Configurar datos demo
        restaurant_id = setup_demo_data(engine)
        
        # Mostrar instrucciones
        print_instructions(restaurant_id)
        
    except Exception as e:
        print(f"❌ Error durante la configuración: {e}")
        print("💡 Verifica tu configuración de base de datos en .env")
        sys.exit(1)


if __name__ == "__main__":
    main()