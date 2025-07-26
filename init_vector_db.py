#!/usr/bin/env python3
"""
Script para inicializar completamente la base de datos vectorial en Supabase
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def init_vector_database():
    """Inicializar la base de datos vectorial completa"""
    
    # Credenciales de conexión
    USER = os.getenv("user") or "postgres.sjsazxoavgthocoseqag"
    PASSWORD = os.getenv("password") or "Physics1991*"
    HOST = os.getenv("host") or "aws-0-sa-east-1.pooler.supabase.com"
    PORT = os.getenv("port") or "6543"
    DBNAME = os.getenv("dbname") or "postgres"
    
    # Si no tenemos las variables individuales, usar DATABASE_URL
    if not all([USER, PASSWORD, HOST, PORT, DBNAME]):
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            print("ERROR: No database connection info found")
            return False
    
    try:
        # Conectar usando variables individuales o DATABASE_URL
        if all([USER, PASSWORD, HOST, PORT, DBNAME]):
            connection = psycopg2.connect(
                user=USER,
                password=PASSWORD,
                host=HOST,
                port=PORT,
                dbname=DBNAME,
                sslmode='require'
            )
        else:
            connection = psycopg2.connect(os.getenv("DATABASE_URL"))
            
        cursor = connection.cursor()
        
        print("✓ Conectado a Supabase")
        
        # 1. Habilitar pgvector
        print("1. Habilitando extensión pgvector...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("✓ pgvector habilitado")
        
        # 2. Verificar instalación
        print("2. Verificando pgvector...")
        cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        result = cursor.fetchone()
        if result:
            print("✓ pgvector confirmado")
        else:
            print("✗ pgvector no encontrado")
            return False
        
        # 3. Test básico de vectores
        print("3. Probando operaciones vectoriales...")
        cursor.execute("SELECT '[1,2,3]'::vector;")
        test_vector = cursor.fetchone()[0]
        print(f"✓ Test vector: {test_vector}")
        
        cursor.execute("SELECT vector_dims('[1,2,3,4]'::vector);")
        dims = cursor.fetchone()[0]
        print(f"✓ Dimensiones: {dims}")
        
        # 4. Crear función de búsqueda de productos
        print("4. Creando función match_products...")
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
        print("✓ Función match_products creada")
        
        # 5. Crear función de búsqueda de conocimiento
        print("5. Creando función match_knowledge...")
        cursor.execute("""
        CREATE OR REPLACE FUNCTION match_knowledge(
          query_embedding vector(384),
          restaurant_id_param integer,
          match_threshold float DEFAULT 0.4,
          match_count int DEFAULT 3
        )
        RETURNS TABLE (
          id integer,
          question text,
          answer text,
          category text,
          similarity float
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
          RETURN QUERY
          SELECT
            kb.id,
            kb.question,
            kb.answer,
            kb.category,
            1 - (kb.embedding <=> query_embedding) as similarity
          FROM knowledge_base kb
          WHERE kb.restaurant_id = restaurant_id_param
            AND kb.active = true
            AND 1 - (kb.embedding <=> query_embedding) > match_threshold
          ORDER BY kb.embedding <=> query_embedding
          LIMIT match_count;
        END;
        $$;
        """)
        print("✓ Función match_knowledge creada")
        
        # 6. Crear función de memorias
        print("6. Creando función match_memories...")
        cursor.execute("""
        CREATE OR REPLACE FUNCTION match_memories(
          query_embedding vector(384),
          customer_phone_param text,
          restaurant_id_param integer,
          match_count int DEFAULT 3
        )
        RETURNS TABLE (
          id integer,
          memory_type text,
          content text,
          summary text,
          importance_score real,
          similarity float,
          created_at timestamptz
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
          RETURN QUERY
          SELECT
            cm.id,
            cm.memory_type,
            cm.content,
            cm.summary,
            cm.importance_score,
            1 - (cm.embedding <=> query_embedding) as similarity,
            cm.created_at
          FROM conversation_memories cm
          WHERE cm.customer_phone = customer_phone_param
            AND cm.restaurant_id = restaurant_id_param
          ORDER BY 
            cm.importance_score DESC,
            cm.embedding <=> query_embedding,
            cm.created_at DESC
          LIMIT match_count;
        END;
        $$;
        """)
        print("✓ Función match_memories creada")
        
        # 7. Confirmar todo
        connection.commit()
        cursor.close()
        connection.close()
        
        print("\n" + "="*50)
        print("🎉 SUPABASE VECTOR DB INICIALIZADA CORRECTAMENTE!")
        print("="*50)
        print("✓ pgvector habilitado")
        print("✓ Funciones de búsqueda creadas")
        print("✓ Sistema listo para embeddings")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = init_vector_database()
    
    if success:
        print("\nSiguientes pasos:")
        print("1. Crear tablas vectoriales: python create_tables.py")
        print("2. Inicializar datos demo: python setup_demo_data.py")
        print("3. Iniciar servidor: python app/main.py")
    else:
        print("\nInicialización fallida. Revisa la conexión a Supabase.")