# Configuración con Supabase + pgvector

**Supabase** es la opción **RECOMENDADA** para este proyecto porque incluye pgvector preinstalado y optimizado para aplicaciones modernas.

## ¿Por qué Supabase?

✅ **pgvector preinstalado**: No necesitas configurar la extensión  
✅ **Interfaz web**: Dashboard visual para gestionar datos  
✅ **APIs automáticas**: RESTful + GraphQL generadas automáticamente  
✅ **Autenticación**: Sistema de auth integrado (futuro)  
✅ **Realtime**: Actualizaciones en tiempo real  
✅ **Gratis**: Tier gratuito generoso para desarrollo  
✅ **Escalable**: Hasta producción sin cambios  

## Setup Paso a Paso

### **1. Crear Proyecto en Supabase**

1. Ve a [supabase.com](https://supabase.com)
2. Crea una cuenta gratis
3. **"New Project"**
   - **Name**: `sales-agent-restaurant`
   - **Password**: Genera una contraseña segura
   - **Region**: Selecciona la más cercana (South America)
4. Espera ~2 minutos mientras se configura

### **2. Obtener Credenciales de Conexión**

En tu proyecto Supabase:

1. Ve a **Settings** → **Database**
2. Busca **"Connection string"** 
3. Selecciona **"URI"**
4. Copia la URL que se ve así:
```
postgresql://postgres:[YOUR-PASSWORD]@db.abcdefghijklmnop.supabase.co:5432/postgres
```

### **3. Configurar Variables de Entorno**

Edita tu archivo `.env`:

```env
# Supabase Database Connection
DATABASE_URL=postgresql://postgres:[TU-PASSWORD]@db.[TU-PROJECT-REF].supabase.co:5432/postgres

# Supabase Additional Info (optional for future features)
SUPABASE_URL=https://[TU-PROJECT-REF].supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# LLM APIs
OPENAI_API_KEY=sk-your_openai_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
```

### **4. Configurar pgvector en Supabase**

En Supabase, ve a **SQL Editor** y ejecuta:

```sql
-- Verificar que pgvector está disponible (ya debería estar)
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Probar funcionalidad vector
SELECT '[1,2,3]'::vector;
SELECT vector_dims('[1,2,3,4]'::vector);

-- Crear funciones optimizadas para búsqueda semántica
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
```

### **5. Ejecutar Migraciones**

```bash
# En tu terminal
cd sales_agent_simplified

# Instalar dependencias si no lo has hecho
pip install -r requirements.txt

# Ejecutar migraciones para crear tablas
alembic upgrade head
```

### **6. Inicializar Datos de Demostración**

```bash
# Ejecutar setup automático
curl -X POST http://localhost:8000/setup

# O desde Python
python -c "
import requests
response = requests.post('http://localhost:8000/setup')
print(response.json())
"
```

### **7. Verificar Funcionamiento**

En Supabase, ve a **Table Editor** y verifica que se crearon:

- ✅ `restaurants` (con 1 restaurante demo)
- ✅ `products` (con ~15 productos colombianos)  
- ✅ `product_embeddings` (con vectores generados)
- ✅ `conversations`
- ✅ `knowledge_base`
- ✅ `conversation_memories`
- ✅ `search_logs`

## Configuración Avanzada

### **Índices de Rendimiento**

Para mejorar la velocidad de búsqueda, ejecuta en **SQL Editor**:

```sql
-- Crear índices vectoriales para búsquedas rápidas
CREATE INDEX IF NOT EXISTS product_embeddings_embedding_idx 
ON product_embeddings USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS knowledge_base_embedding_idx 
ON knowledge_base USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 50);

CREATE INDEX IF NOT EXISTS conversation_memories_embedding_idx 
ON conversation_memories USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 50);

-- Índices regulares para consultas frecuentes
CREATE INDEX IF NOT EXISTS product_embeddings_restaurant_id_idx 
ON product_embeddings(restaurant_id);

CREATE INDEX IF NOT EXISTS conversation_memories_customer_phone_idx 
ON conversation_memories(customer_phone);

CREATE INDEX IF NOT EXISTS search_logs_restaurant_id_created_idx 
ON search_logs(restaurant_id, created_at);
```

### **Row Level Security (RLS)**

Para seguridad en producción:

```sql
-- Habilitar RLS en tablas sensibles
ALTER TABLE conversation_memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE search_logs ENABLE ROW LEVEL SECURITY;

-- Crear políticas de acceso (ajustar según tu caso)
CREATE POLICY "Allow restaurant access to own data" 
ON conversation_memories 
FOR ALL 
USING (restaurant_id IN (SELECT id FROM restaurants WHERE active = true));
```

### **Funciones de Analytics**

```sql
-- Función para obtener estadísticas de búsqueda
CREATE OR REPLACE FUNCTION get_search_analytics(
  restaurant_id_param integer,
  days_back integer DEFAULT 7
)
RETURNS TABLE (
  total_searches bigint,
  avg_search_time numeric,
  most_common_query text,
  query_count bigint
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  WITH search_stats AS (
    SELECT 
      COUNT(*) as total,
      AVG(search_time_ms) as avg_time
    FROM search_logs 
    WHERE restaurant_id = restaurant_id_param 
      AND created_at > NOW() - INTERVAL '%s days'
  ),
  top_query AS (
    SELECT query, COUNT(*) as count
    FROM search_logs 
    WHERE restaurant_id = restaurant_id_param
      AND created_at > NOW() - INTERVAL '%s days'
    GROUP BY query
    ORDER BY count DESC
    LIMIT 1
  )
  SELECT 
    s.total,
    s.avg_time,
    t.query,
    t.count
  FROM search_stats s
  CROSS JOIN top_query t;
END;
$$;
```

## Testing de Funcionalidad

### **1. Test de Conexión**

```python
# test_supabase.py
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cursor = conn.cursor()
    
    # Test básico
    cursor.execute("SELECT version();")
    print("✅ Conexión exitosa:", cursor.fetchone()[0])
    
    # Test pgvector
    cursor.execute("SELECT '[1,2,3]'::vector;")
    print("✅ pgvector funcionando:", cursor.fetchone()[0])
    
    conn.close()
    
except Exception as e:
    print("❌ Error:", e)
```

### **2. Test de Embeddings**

```bash
# Test crear embeddings
curl -X POST "http://localhost:8000/api/v1/vectors/embeddings/products/1"

# Respuesta esperada:
# {"created": 15, "updated": 0, "errors": 0}
```

### **3. Test de Búsqueda Semántica**

```bash
# Test búsqueda de productos
curl -X POST "http://localhost:8000/api/v1/vectors/search/products" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "algo vegetariano y barato",
    "restaurant_id": 1,
    "similarity_threshold": 0.3
  }'

# Respuesta esperada:
# {
#   "results": [
#     {
#       "product_id": 3,
#       "name": "Arepa de Queso", 
#       "price": 6000,
#       "similarity_score": 0.842
#     }
#   ]
# }
```

## Monitoring y Analytics en Supabase

### **Dashboard de Supabase**

1. **Database**: Ver todas las tablas y datos
2. **Auth**: Usuarios (para futuras funciones)
3. **Storage**: Archivos (para imágenes de productos)
4. **API**: Documentación automática de endpoints
5. **Logs**: Consultas SQL y errores
6. **Settings**: Configuración y límites

### **Consultas Útiles**

```sql
-- Ver embeddings creados
SELECT 
  restaurant_id,
  COUNT(*) as total_embeddings,
  AVG(LENGTH(embedding)) as avg_embedding_size
FROM product_embeddings 
GROUP BY restaurant_id;

-- Top búsquedas
SELECT 
  query,
  COUNT(*) as frequency,
  AVG(search_time_ms) as avg_time
FROM search_logs 
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY query
ORDER BY frequency DESC
LIMIT 10;

-- Productos más buscados
SELECT 
  p.name,
  COUNT(*) as search_count
FROM search_logs sl
JOIN product_embeddings pe ON sl.restaurant_id = pe.restaurant_id
JOIN products p ON pe.product_id = p.id
WHERE sl.search_type = 'products'
GROUP BY p.name
ORDER BY search_count DESC;
```

## Límites y Costos

### **Tier Gratuito de Supabase**
- ✅ **Database**: 500MB
- ✅ **Bandwidth**: 5GB
- ✅ **API requests**: 50K/mes
- ✅ **Auth users**: 50K
- ✅ **Storage**: 1GB

### **Para Producción**
- **Pro Plan**: $25/mes
  - 8GB Database
  - 250GB Bandwidth
  - 500K API requests
  - Backups diarios

### **Optimización de Costos**
- **Embeddings**: ~1KB por producto (muy eficiente)
- **Búsquedas**: ~1ms promedio (ultra rápido)
- **Storage**: 1000 productos = ~1MB de embeddings

## Troubleshooting

### **Error: "extension vector does not exist"**
```sql
-- Ejecutar en SQL Editor de Supabase
CREATE EXTENSION IF NOT EXISTS vector;
```

### **Error: "function match_products does not exist"**
```sql
-- Ejecutar el script setup_supabase.sql completo
```

### **Error de conexión**
- Verificar que la URL tiene la contraseña correcta
- Verificar que el proyecto esté activo en Supabase
- Revisar que no haya espacios en la URL

### **Búsquedas lentas**
```sql
-- Crear índices vectoriales
CREATE INDEX product_embeddings_embedding_idx 
ON product_embeddings USING ivfflat (embedding vector_cosine_ops);
```

### **Embeddings no se crean**
- Verificar que sentence-transformers esté instalado
- Revisar logs: problemas de memoria o dependencias
- Probar con OpenAI embeddings como alternativa

## Siguiente Paso: Producción

1. **Upgrade a Pro Plan**: Cuando necesites más capacidad
2. **Configurar Backups**: Automáticos en Pro
3. **Add Custom Domain**: Para APIs propias  
4. **Enable RLS**: Seguridad row-level
5. **Monitor Performance**: Dashboard de métricas

**¡Supabase + pgvector está listo para revolucionar tu agente conversacional! 🚀**