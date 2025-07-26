# Agente Conversacional Inteligente

El sistema ahora incluye un agente conversacional avanzado que usa modelos de lenguaje (LLM) para mantener conversaciones naturales con los clientes.

## ¿Qué Modelo LLM se Usa?

### **Opción 1: OpenAI GPT-3.5-turbo** ⭐ (Recomendado)
```env
OPENAI_API_KEY=sk-your_openai_api_key_here
```
- **Modelo**: `gpt-3.5-turbo`
- **Ventajas**: Respuestas más naturales, mejor comprensión del contexto
- **Costo**: ~$0.002 por conversación promedio
- **Respuesta típica**: 2-3 segundos

### **Opción 2: Anthropic Claude Haiku**
```env
ANTHROPIC_API_KEY=sk-ant-your_anthropic_api_key_here
```
- **Modelo**: `claude-3-haiku-20240307`
- **Ventajas**: Muy rápido, económico, buena calidad
- **Costo**: ~$0.001 por conversación promedio
- **Respuesta típica**: 1-2 segundos

### **Fallback: Sistema de Keywords** 🔄
- **Cuando**: No hay API keys configuradas
- **Función**: Respuestas predefinidas basadas en palabras clave
- **Ventajas**: Gratis, rápido, funciona offline
- **Limitaciones**: Menos natural, respuestas limitadas

## Prompt del Sistema (Contexto)

### **Prompt Principal del Agente:**

```text
Eres un asistente virtual especializado en ventas para [RESTAURANTE], un restaurante colombiano.

TU OBJETIVO PRINCIPAL: Ayudar al cliente a realizar pedidos de comida de manera amigable y eficiente.

INFORMACIÓN DEL RESTAURANTE:
- Nombre: [Restaurante Demo]
- Descripción: Restaurante colombiano tradicional
- Horario: Lunes a Domingo, 10:00 AM - 10:00 PM
- Entrega: 30-45 minutos en toda la ciudad
- Costo de entrega: $3,000 COP

MENÚ DISPONIBLE:
--- ENTRADAS ---
• Empanadas de Pollo - $8,000
  Deliciosas empanadas caseras rellenas de pollo y verduras
• Patacones con Guacamole - $12,000
  Patacones crujientes acompañados de guacamole fresco
• Arepa de Queso - $6,000
  Arepa tradicional rellena de queso campesino

--- PLATOS PRINCIPALES ---
• Bandeja Paisa - $28,000
  Bandeja tradicional con frijoles, arroz, carne molida, chorizo...
• Sancocho de Gallina - $25,000
  Sancocho tradicional con gallina criolla y vegetales frescos
...

PEDIDO ACTUAL DEL CLIENTE:
[Dinámico - se actualiza con cada interacción]

INSTRUCCIONES DE COMPORTAMIENTO:
1. PERSONALIZACIÓN:
   - Dirígete al cliente por su nombre
   - Sé cálido, amigable y profesional
   - Usa el contexto colombiano naturalmente

2. PROCESO DE VENTA:
   - Saluda al cliente y presenta el restaurante
   - Pregunta por sus preferencias
   - Recomienda productos específicos del menú
   - Ayuda a construir el pedido paso a paso
   - Sugiere complementos apropiados

3. RECOMENDACIONES INTELIGENTES:
   - Si pide "algo típico": recomienda Bandeja Paisa
   - Para entradas: sugiere empanadas o patacones
   - Para bebidas: recomienda limonada de coco
   - Siempre menciona precios

4. TONO Y ESTILO:
   - Natural y conversacional
   - Entusiasta pero no agresivo
   - Usa emojis moderadamente (🍽️ 🥘 😊)
   - Responde de manera concisa pero completa
```

### **Contexto Dinámico:**

El agente recibe información en tiempo real sobre:
- **Menú actualizado**: Productos disponibles con precios actuales
- **Pedido actual**: Items en el carrito del cliente
- **Historial de conversación**: Últimos 10 mensajes para contexto
- **Información del cliente**: Nombre, preferencias anteriores
- **Estado del restaurante**: Horarios, políticas de entrega

## Flujo de Conversación

### **1. Análisis de Intención (Intent Analysis)**
```python
intent_analysis = {
    'intent': 'order_request',        # Tipo de intención
    'confidence': 0.8,                # Confianza (0-1)
    'entities': {                     # Entidades extraídas
        'mentioned_product': 'Bandeja Paisa'
    },
    'suggested_action': 'help_with_order'  # Acción sugerida
}
```

**Intenciones Reconocidas:**
- `greeting` - Saludo inicial
- `menu_request` - Solicitud de menú
- `order_request` - Quiere hacer pedido
- `price_inquiry` - Pregunta por precios
- `recommendation_request` - Pide recomendaciones
- `delivery_inquiry` - Pregunta por entrega
- `product_inquiry` - Pregunta por producto específico

### **2. Gestión de Contexto**
```python
context = {
    'restaurant': {
        'name': 'Restaurante Demo',
        'description': 'Restaurante colombiano tradicional',
        'config': {'delivery_fee': 3000, 'delivery_time': '30-45 minutos'}
    },
    'products_by_category': {
        'entradas': [...],
        'platos principales': [...],
        'bebidas': [...],
        'postres': [...]
    },
    'current_order': {
        'items': [...],
        'total': 28000
    },
    'customer_name': 'Juan',
    'conversation_context': {}
}
```

### **3. Generación de Respuesta**

**Con LLM:**
1. Construye prompt con contexto completo
2. Incluye historial de conversación
3. Envía a OpenAI/Anthropic
4. Procesa respuesta y la devuelve

**Sin LLM (Fallback):**
1. Analiza keywords en el mensaje
2. Selecciona respuesta predefinida
3. Personaliza con contexto básico

## API Endpoints para Conversación

### **Chat Directo con el Agente**
```bash
POST /api/v1/agent/chat
{
  "message": "Hola, ¿qué me recomiendas?",
  "restaurant_id": 1,
  "customer_name": "Juan",
  "chat_id": "web_test"
}

# Respuesta
{
  "response": "¡Hola Juan! 😊 Te recomiendo nuestra estrella: la Bandeja Paisa ($28,000). Es un plato completísimo con frijoles, arroz, carne, chorizo y más. ¿Te provoca algo contundente así o prefieres algo más ligero?",
  "intent_analysis": {
    "intent": "recommendation_request",
    "confidence": 0.8,
    "suggested_action": "provide_recommendations"
  },
  "conversation_id": 123
}
```

### **Análisis de Intención**
```bash
POST /api/v1/agent/analyze-intent
{
  "message": "Quiero una bandeja paisa",
  "restaurant_id": 1
}

# Respuesta
{
  "intent_analysis": {
    "intent": "order_request",
    "confidence": 0.9,
    "entities": {
      "mentioned_product": "Bandeja Paisa"
    },
    "suggested_action": "help_with_order"
  }
}
```

### **Configuración del Agente**
```bash
GET /api/v1/agent/config

# Respuesta
{
  "llm_enabled": true,
  "available_models": ["openai_gpt-3.5-turbo"],
  "current_model": "openai_gpt-3.5-turbo",
  "response_length": 300,
  "temperature": 0.7
}
```

### **Historial de Conversación**
```bash
GET /api/v1/agent/conversation/123/history

# Respuesta
{
  "conversation_id": 123,
  "customer": "Juan",
  "platform": "telegram",
  "messages": [
    {"role": "user", "content": "Hola"},
    {"role": "assistant", "content": "¡Hola Juan! ¿En qué puedo ayudarte?"},
    {"role": "user", "content": "¿Qué me recomiendas?"},
    {"role": "assistant", "content": "Te recomiendo..."}
  ]
}
```

## Ejemplos de Conversaciones

### **Conversación Típica de Pedido:**

```
👤 Cliente: "Hola, tengo mucha hambre"

🤖 Bot: "¡Hola! 😊 ¿Qué antojo tienes hoy? Tenemos deliciosos platos típicos colombianos. ¿Te provoca algo contundente como una Bandeja Paisa ($28,000) o prefieres empezar con unas empanadas ($8,000)?"

👤 Cliente: "¿Qué trae la bandeja paisa?"

🤖 Bot: "¡Excelente elección! La Bandeja Paisa ($28,000) es nuestro plato estrella e incluye: frijoles, arroz blanco, carne molida, chorizo, morcilla, chicharrón, arepa, aguacate y plátano maduro. Es súper completa y deliciosa 🥘"

👤 Cliente: "Perfecto, quiero una"

🤖 Bot: "¡Perfecto! He agregado una Bandeja Paisa ($28,000) a tu pedido 👍 ¿Te gustaría agregar algo para tomar? Tenemos limonada de coco ($8,000) que va perfecta con la bandeja."

👤 Cliente: "Sí, agrega la limonada"

🤖 Bot: "¡Excelente! Tu pedido queda así:
• Bandeja Paisa x1 = $28,000
• Limonada de Coco x1 = $8,000
**Total: $36,000**

¿Confirmas el pedido para proceder con el pago? 🛒"
```

### **Manejo de Consultas de Precios:**

```
👤 Cliente: "¿Cuánto cuestan las empanadas?"

🤖 Bot: "Las Empanadas de Pollo cuestan $8,000 y vienen rellenas de pollo y verduras caseras. ¡Están deliciosas! 😋 ¿Te gustaría agregarlas a tu pedido?"

👤 Cliente: "¿Y qué más hay de entradas?"

🤖 Bot: "Tenemos varias entradas deliciosas:
• Empanadas de Pollo - $8,000
• Patacones con Guacamole - $12,000  
• Arepa de Queso - $6,000

¿Cuál te llama más la atención? Los patacones con guacamole son muy populares 🥑"
```

## Configuración y Personalización

### **1. Configurar API Keys**

**Para OpenAI:**
1. Ve a [platform.openai.com](https://platform.openai.com)
2. Crea una API key
3. Agrégala al archivo `.env`:
```env
OPENAI_API_KEY=sk-your_openai_api_key_here
```

**Para Anthropic:**
1. Ve a [console.anthropic.com](https://console.anthropic.com)
2. Crea una API key
3. Agrégala al archivo `.env`:
```env
ANTHROPIC_API_KEY=sk-ant-your_anthropic_api_key_here
```

### **2. Personalizar el Prompt**

El prompt se construye dinámicamente en `conversational_agent.py`:

```python
def _create_system_prompt(self, context: Dict[str, Any]) -> str:
    # Personaliza aquí el comportamiento del agente
    prompt = f"""Eres un asistente virtual para {restaurant['name']}...
    
    PERSONALIZACIÓN ESPECÍFICA:
    - Tono: [Formal/Informal/Amigable]
    - Especialidad: [Comida colombiana/Internacional/etc]
    - Estrategia de venta: [Sugestiva/Directa/Consultiva]
    """
```

### **3. Configurar Respuestas Específicas**

```python
# En _generate_simple_response() para fallbacks
if 'menu vegano' in message_lower:
    return "Aunque somos especialistas en comida tradicional, tenemos opciones vegetarianas como..."
```

## Monitoreo y Análisis

### **Métricas del Agente:**
- **Tiempo de respuesta**: Promedio 2-3 segundos con LLM
- **Tasa de conversión**: % de conversaciones que terminan en pedido
- **Intenciones más comunes**: Estadísticas de tipos de consulta
- **Productos más mencionados**: Análisis de demanda

### **Logs del Sistema:**
```bash
# Conversaciones exitosas
INFO: LLM response generated for customer Juan in 2.3s

# Errores de API
ERROR: OpenAI API error: Rate limit exceeded

# Fallbacks activados  
WARNING: Using keyword fallback for customer Maria
```

### **Testing y Calidad:**
```bash
# Test scenarios disponibles
GET /api/v1/agent/test-prompts

# Respuesta con casos de prueba
{
  "test_scenarios": [
    {
      "scenario": "greeting",
      "message": "Hola, buenas tardes", 
      "expected_intent": "greeting"
    },
    {
      "scenario": "menu_request",
      "message": "¿Qué tienen de menú?",
      "expected_intent": "menu_request"
    }
  ]
}
```

## Costos y Rendimiento

### **Costos Estimados:**

**OpenAI GPT-3.5-turbo:**
- **Input**: $0.0015 / 1K tokens
- **Output**: $0.002 / 1K tokens
- **Conversación promedio**: ~300 tokens = $0.001
- **1000 conversaciones/mes**: ~$1 USD

**Anthropic Claude Haiku:**
- **Input**: $0.00025 / 1K tokens
- **Output**: $0.00125 / 1K tokens  
- **Conversación promedio**: ~250 tokens = $0.0005
- **1000 conversaciones/mes**: ~$0.50 USD

### **Optimizaciones:**
- **Cache de respuestas**: Para preguntas frecuentes
- **Límite de tokens**: Máximo 300 tokens por respuesta
- **Rate limiting**: Previene abuso y costos excesivos
- **Fallback inteligente**: Usa keywords para queries simples

## Próximas Mejoras

### **Planificadas:**
- [ ] **Memoria a largo plazo**: Recordar preferencias del cliente
- [ ] **Recomendaciones ML**: Basadas en historial de pedidos
- [ ] **Multiidioma**: Soporte para inglés y otros idiomas
- [ ] **Integración con WhatsApp**: Mismo agente en múltiples canales
- [ ] **A/B Testing**: Comparar diferentes prompts y modelos

### **Avanzadas:**
- [ ] **Fine-tuning**: Entrenar modelo específico para el restaurante
- [ ] **Integración con inventario**: "Disculpa, se nos acabó el pescado"
- [ ] **Análisis de sentimiento**: Detectar clientes insatisfechos
- [ ] **Escalación automática**: Transferir a humano cuando sea necesario

¡El agente conversacional está listo para mantener conversaciones naturales e inteligentes con tus clientes! 🤖💬