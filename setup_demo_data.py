#!/usr/bin/env python3
"""
Script para inicializar datos de demostración
"""
import requests
import json

def setup_demo_data():
    """Inicializar datos de demostración usando la API"""
    
    try:
        print("Inicializando datos de demostracion...")
        
        # URL del endpoint de setup
        setup_url = "http://localhost:8000/setup"
        
        print("Llamando al endpoint de setup...")
        response = requests.post(setup_url, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: Datos de demostracion creados!")
            print(f"Restaurante: {result.get('restaurant', {}).get('name', 'N/A')}")
            print(f"Productos: {len(result.get('products', []))} creados")
            print(f"Base de conocimiento: {len(result.get('knowledge_base', []))} entradas")
            return True
        else:
            print(f"ERROR: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("ERROR: No se puede conectar al servidor FastAPI")
        print("Necesitas iniciar el servidor primero:")
        print("  python app/main.py")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    if setup_demo_data():
        print("\n" + "="*50)
        print("SISTEMA LISTO PARA USAR!")
        print("="*50)
        print("1. Servidor FastAPI en: http://localhost:8000")
        print("2. Dashboard web en: http://localhost:3000") 
        print("3. Telegram bot configurado")
        print("4. Base de datos con datos de prueba")
    else:
        print("\nPrimero inicia el servidor FastAPI:")
        print("python app/main.py")