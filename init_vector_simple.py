#!/usr/bin/env python3
"""
Script simple para inicializar pgvector en Supabase (compatible Windows)
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def init_pgvector():
    """Inicializar pgvector en Supabase"""
    
    try:
        # Usar DATABASE_URL directamente
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            print("ERROR: DATABASE_URL no encontrada en .env")
            return False
            
        print("Conectando a Supabase...")
        connection = psycopg2.connect(DATABASE_URL)
        cursor = connection.cursor()
        
        print("SUCCESS: Conectado a Supabase")
        
        # 1. Habilitar pgvector
        print("1. Habilitando pgvector...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("SUCCESS: pgvector habilitado")
        
        # 2. Verificar
        cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        result = cursor.fetchone()
        if result:
            print("SUCCESS: pgvector confirmado")
        else:
            print("ERROR: pgvector no encontrado")
            return False
        
        # 3. Test vectores
        print("2. Probando vectores...")
        cursor.execute("SELECT '[1,2,3]'::vector;")
        test_vector = cursor.fetchone()[0]
        print(f"SUCCESS: Vector test: {test_vector}")
        
        # 4. Función match_products
        print("3. Creando funciones de busqueda...")
        cursor.execute("""
        CREATE OR REPLACE FUNCTION match_products(
          query_embedding vector(384),
          restaurant_id_param integer,
          match_threshold float DEFAULT 0.3,
          match_count int DEFAULT 5
        )
        RETURNS TABLE (
          product_id integer,
          name text,
          description text,
          price real,
          category text,
          similarity float
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
          RETURN QUERY
          SELECT
            pe.product_id,
            p.name,
            p.description,
            p.price,
            p.category,
            1 - (pe.embedding <=> query_embedding) as similarity
          FROM product_embeddings pe
          JOIN products p ON pe.product_id = p.id
          WHERE pe.restaurant_id = restaurant_id_param
            AND p.available = true
            AND 1 - (pe.embedding <=> query_embedding) > match_threshold
          ORDER BY pe.embedding <=> query_embedding
          LIMIT match_count;
        END;
        $$;
        """)
        print("SUCCESS: Funcion match_products creada")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("\n" + "="*50)
        print("SUPABASE VECTOR DB LISTA!")
        print("="*50)
        print("pgvector: HABILITADO")
        print("Funciones: CREADAS")
        print("Estado: LISTO")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    if init_pgvector():
        print("\nProximo paso: python create_tables.py")
    else:
        print("\nFallo en la inicializacion")