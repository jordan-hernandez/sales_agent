# Guía de pgvector - Búsqueda Semántica

El sistema ahora implementa **búsqueda semántica avanzada** usando pgvector para PostgreSQL, permitiendo búsquedas inteligentes basadas en significado, no solo palabras clave.

## ¿Qué es pgvector?

**pgvector** es una extensión de PostgreSQL que permite:
- ✅ **Almacenar vectores de embeddings** directamente en la base de datos
- ✅ **Búsquedas de similitud ultra-rápidas** con índices especializados
- ✅ **Operadores vectoriales nativos** (cosine, L2, inner product)
- ✅ **Escalabilidad** para millones de vectores

## Arquitectura Implementada

### **1. Modelos de Base de Datos con Vectores**

```sql
-- Embeddings de productos para búsqueda semántica
product_embeddings:
  - product_id: FK a products
  - content: texto combinado (nombre + descripción + categoría)
  - embedding: vector[384] (sentence-transformers) o vector[1536] (OpenAI)
  - similarity search: <=> operator

-- Memoria de conversaciones con embeddings
conversation_memories:
  - customer_phone: identificador del cliente
  - memory_type: 'preference', 'order_history', 'complaint'
  - content + summary: contenido de la memoria
  - embedding: vector para búsqueda semántica
  - importance_score: relevancia de la memoria

-- Base de conocimientos con vectores
knowledge_base:
  - question + answer: preguntas frecuentes
  - category: tipo de conocimiento
  - embedding: vector del contenido
  - usage_count: estadísticas de uso

-- Logs de búsquedas para analytics
search_logs:
  - query: búsqueda realizada
  - embedding: vector de la query
  - results_found: número de resultados
  - search_time_ms: tiempo de respuesta
```

### **2. Modelos de Embeddings**

**Opción 1: Sentence Transformers (Recomendado para MVP)**
```python
Model: "sentence-transformers/all-MiniLM-L6-v2"
- Dimensiones: 384
- Velocidad: ~50ms por embedding
- Costo: GRATIS (local)
- Calidad: Excelente para español
```

**Opción 2: OpenAI Embeddings (Producción)**
```python
Model: "text-embedding-ada-002"  
- Dimensiones: 1536
- Velocidad: ~200ms por embedding
- Costo: $0.0001 por 1K tokens
- Calidad: Superior
```

## Búsquedas Semánticas Implementadas

### **1. Búsqueda de Productos Inteligente**

**Problema resuelto**: Cliente dice "algo vegetariano" y encuentra productos sin esa palabra exacta.

```python
# Cliente: "Quiero algo vegetariano y saludable"
# Encuentra: Patacones con Guacamole, Arepa de Queso
# Aunque no contengan la palabra "vegetariano"

results = vector_search_service.search_products_semantic(
    query="algo vegetariano y saludable",
    restaurant_id=1,
    limit=5,
    similarity_threshold=0.3
)
```

**Ejemplos de búsquedas inteligentes**:
- 🔍 `"algo barato"` → encuentra productos bajo $10,000
- 🔍 `"comida típica"` → encuentra Bandeja Paisa, Sancocho
- 🔍 `"para compartir"` → encuentra platos grandes
- 🔍 `"sin carne"` → encuentra opciones vegetarianas
- 🔍 `"algo refrescante"` → encuentra bebidas y postres fríos

### **2. Base de Conocimientos Inteligente**

**Problema resuelto**: Cliente pregunta de formas diferentes y obtiene la respuesta correcta.

```python
# Cliente: "¿Hasta qué hora atienden?"
# Encuentra: FAQ sobre horarios de atención
# Aunque la pregunta registrada sea "¿Cuál es el horario?"

knowledge = vector_search_service.search_knowledge_base(
    query="hasta que hora atienden",
    restaurant_id=1
)
```

**Ejemplos de conocimiento inteligente**:
- 🤖 `"cuánto demoran"` → encuentra info de tiempos de entrega
- 🤖 `"aceptan tarjeta"` → encuentra info de métodos de pago  
- 🤖 `"tienen vegano"` → encuentra info de opciones vegetarianas
- 🤖 `"dónde están ubicados"` → encuentra dirección del restaurante

### **3. Memoria de Conversaciones Personalizada**

**Problema resuelto**: El agente recuerda preferencias y contexto del cliente.

```python
# Sistema recuerda: "Juan siempre pide sin cebolla"
# Próxima vez: "Para Juan, ¿el pollo sin cebolla como siempre?"

memories = vector_search_service.search_conversation_memory(
    query="preferencias del cliente",
    customer_phone="+573001234567",
    restaurant_id=1
)
```

**Tipos de memoria**:
- 🧠 **Preferencias**: "Sin cebolla", "Extra picante", "Sin gluten"
- 🧠 **Historial**: "Siempre pide bandeja paisa los viernes"
- 🧠 **Quejas**: "Se quejó de demora en entrega anterior"
- 🧠 **Cumplidos**: "Le gustó mucho el sancocho"

## API Endpoints de Búsqueda Semántica

### **Crear Embeddings**
```bash
POST /api/v1/vectors/embeddings/products/1
# Genera embeddings para todos los productos del restaurante

Response:
{
  "created": 15,
  "updated": 0, 
  "errors": 0
}
```

### **Búsqueda Semántica de Productos**
```bash
POST /api/v1/vectors/search/products
{
  "query": "algo vegetariano y barato",
  "restaurant_id": 1,
  "limit": 5,
  "similarity_threshold": 0.3
}

Response:
{
  "query": "algo vegetariano y barato",
  "results": [
    {
      "product_id": 3,
      "name": "Arepa de Queso",
      "price": 6000,
      "similarity_score": 0.847,
      "category": "entradas"
    }
  ],
  "search_time_ms": 45,
  "total_results": 1
}
```

### **Búsqueda en Base de Conocimientos**
```bash
POST /api/v1/vectors/search/knowledge
{
  "query": "cuanto demoran en entregar",
  "restaurant_id": 1
}

Response:
{
  "results": [
    {
      "question": "¿Cuál es el tiempo de entrega?",
      "answer": "Entregamos en 30-45 minutos en toda la ciudad",
      "similarity_score": 0.923,
      "category": "entrega"
    }
  ]
}
```

### **Crear Conocimiento**
```bash
POST /api/v1/vectors/knowledge/1
{
  "question": "¿Tienen opciones sin gluten?",
  "answer": "Sí, tenemos arepas de maíz y ensaladas que son naturalmente sin gluten.",
  "category": "menu_especial",
  "tags": ["sin gluten", "celíaco", "opciones especiales"]
}
```

### **Almacenar Memoria de Cliente**
```bash
POST /api/v1/vectors/memory/123
{
  "memory_type": "preference",
  "content": "Cliente Juan siempre pide la bandeja paisa sin morcilla",
  "summary": "Sin morcilla en bandeja paisa",
  "importance_score": 0.8
}
```

### **Analytics de Búsquedas**
```bash
GET /api/v1/vectors/analytics/1?days=7

Response:
{
  "analytics": {
    "common_queries": [
      {"query": "algo vegetariano", "count": 15, "avg_similarity": 0.782},
      {"query": "horario", "count": 12, "avg_similarity": 0.891}
    ],
    "performance": {
      "avg_search_time_ms": 45.2,
      "avg_embedding_time_ms": 52.1,
      "total_searches": 127
    }
  }
}
```

## Integración con el Agente Conversacional

### **Prompt Mejorado con Vectores**

Cuando el agente recibe una consulta, ahora:

1. **Genera embedding** de la consulta del usuario
2. **Busca productos relevantes** semánticamente  
3. **Busca conocimiento** relacionado en la base de datos
4. **Recupera memorias** específicas del cliente
5. **Genera prompt mejorado** con contexto relevante

```python
# Ejemplo de prompt mejorado:
"""
MENÚ DISPONIBLE:
[menú completo...]

🎯 PRODUCTOS MÁS RELEVANTES PARA ESTA CONSULTA:
• Arepa de Queso - $6,000 - Arepa tradicional rellena de queso (relevancia: 0.8)
• Patacones con Guacamole - $12,000 - Patacones con guacamole fresco (relevancia: 0.7)

📚 INFORMACIÓN RELEVANTE DEL RESTAURANTE:
P: ¿Tienen opciones vegetarianas?
R: Sí, tenemos arepas de queso, patacones con guacamole, y ensaladas frescas.

🧠 RECORDAR SOBRE ESTE CLIENTE:
• Sin cebolla en todos los pedidos (preferencia)

⚡ INSTRUCCIÓN ESPECIAL: Usa la información de relevancia semántica arriba para dar respuestas más precisas.
"""
```

## Configuración y Setup

### **1. Instalar pgvector en PostgreSQL**

```bash
# Ubuntu/Debian
sudo apt install postgresql-15-pgvector

# macOS con Homebrew  
brew install pgvector

# Docker
docker run --name postgres-vector \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  -d pgvector/pgvector:pg15
```

### **2. Habilitar Extensión**

```sql
-- Como superuser en PostgreSQL
CREATE EXTENSION IF NOT EXISTS vector;

-- Verificar instalación
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### **3. Ejecutar Migraciones**

```bash
# Aplicar migraciones de embeddings
alembic upgrade head

# O ejecutar manualmente:
psql -d sales_agent_db -f alembic/versions/add_embeddings_tables.py
```

### **4. Configurar Modelo de Embeddings**

```env
# Opción 1: Sentence Transformers (gratis, local)
# No requiere configuración adicional

# Opción 2: OpenAI Embeddings (pago, mejor calidad)  
OPENAI_API_KEY=sk-your_openai_api_key_here
```

### **5. Generar Embeddings Iniciales**

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/vectors/embeddings/products/1

# Via setup automático
curl -X POST http://localhost:8000/setup
```

## Rendimiento y Optimización

### **Índices de Rendimiento**
```sql
-- Índice para búsquedas por similitud coseno
CREATE INDEX product_embeddings_cosine_idx 
ON product_embeddings USING ivfflat (embedding vector_cosine_ops);

-- Índice para búsquedas L2  
CREATE INDEX product_embeddings_l2_idx
ON product_embeddings USING ivfflat (embedding vector_l2_ops);
```

### **Métricas de Rendimiento**
- **Generación de embedding**: 50-200ms
- **Búsqueda vectorial**: 10-50ms  
- **Búsqueda total**: 60-250ms
- **Escalabilidad**: +100K vectores sin degradación

### **Optimizaciones**
- **Cache de embeddings**: Para consultas frecuentes
- **Batch processing**: Para crear embeddings masivos
- **Límites de similitud**: Filtrar resultados poco relevantes
- **Índices especializados**: ivfflat para conjuntos grandes

## Casos de Uso Avanzados

### **1. Recomendaciones Personalizadas**
```python
# "Algo similar a lo que pedí la semana pasada"
last_order_items = get_last_order_items(customer_phone)
embedding = combine_embeddings([item.embedding for item in last_order_items])
recommendations = vector_search(embedding, exclude=last_order_items)
```

### **2. Búsqueda de Ingredientes**
```python
# "Sin lácteos" o "libre de gluten"
allergen_query = "sin lactosa sin gluten"
safe_products = search_products_semantic(allergen_query, filter_allergens=True)
```

### **3. Análisis de Sentimientos en Memorias**
```python
# Detectar clientes insatisfechos
negative_memories = search_memories("queja disgusto problema", sentiment="negative")
follow_up_customers = [m.customer_phone for m in negative_memories]
```

### **4. Clustering de Preferencias**
```python
# Agrupar clientes por preferencias similares
customer_embeddings = get_all_customer_preference_embeddings()
clusters = kmeans_clustering(customer_embeddings, n_clusters=5)
marketing_segments = assign_customers_to_segments(clusters)
```

## Monitoreo y Analytics

### **Dashboard de Vectores**
- **Número de embeddings**: Por restaurante y tipo
- **Consultas más comunes**: Top 10 búsquedas semánticas
- **Tiempo de respuesta**: Latencia P95, P99
- **Calidad de resultados**: Similarity scores promedio

### **Alertas Automáticas**
- **Baja similaridad**: Cuando las búsquedas no encuentran resultados relevantes
- **Rendimiento degradado**: Cuando las búsquedas toman >500ms
- **Memoria llena**: Cuando se almacenan demasiadas memorias por cliente

### **Métricas de Negocio**
- **Conversión mejorada**: % de consultas que terminan en pedido
- **Satisfacción del cliente**: Based on conversation sentiment
- **Eficiencia del agente**: Tiempo promedio para resolver consultas

## Próximas Mejoras

### **Implementación Inmediata**
- [ ] **Embeddings multilingües**: Soporte para inglés
- [ ] **Filtros de categoría**: Búsqueda semántica por tipo de producto
- [ ] **Reranking inteligente**: Combinar similitud semántica con popularidad
- [ ] **A/B testing**: Comparar respuestas con/sin búsqueda semántica

### **Mediano Plazo**  
- [ ] **Fine-tuning**: Entrenar modelo específico para comida colombiana
- [ ] **Embeddings de imágenes**: Búsqueda visual de platos
- [ ] **Temporal embeddings**: Considerar contexto temporal (hora, día)
- [ ] **Graph embeddings**: Relaciones entre productos, clientes, preferencias

### **Avanzado**
- [ ] **Federated search**: Búsqueda cross-restaurante
- [ ] **Real-time embeddings**: Actualización continua de vectores
- [ ] **Embedding compression**: Reducir dimensionalidad sin perder calidad
- [ ] **Hybrid search**: Combinar vectorial + keyword + filtros

¡El sistema de búsqueda semántica con pgvector está completamente implementado y listo para revolucionar la experiencia conversacional! 🚀🔍