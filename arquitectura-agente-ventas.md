# Arquitectura del Agente de Ventas para Restaurantes

## Visión General
Sistema conversacional de ventas end-to-end para restaurantes en Colombia, con integración principal en WhatsApp y funcionalidades completas desde el primer contacto hasta el procesamiento de pagos.

## Arquitectura del Sistema

### 1. Frontend (React)
```
├── components/
│   ├── Dashboard/
│   │   ├── OrderManagement.tsx
│   │   ├── InventoryView.tsx
│   │   └── SalesAnalytics.tsx
│   ├── Configuration/
│   │   ├── MenuEditor.tsx
│   │   ├── AgentSettings.tsx
│   │   └── PaymentConfig.tsx
│   └── Chat/
│       ├── ConversationView.tsx
│       └── AgentResponsePreview.tsx
├── services/
│   ├── api.ts
│   ├── websocket.ts
│   └── auth.ts
└── utils/
    ├── formatters.ts
    └── validators.ts
```

### 2. Backend (FastAPI)
```
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── chat/
│   │   │   │   ├── whatsapp.py
│   │   │   │   └── telegram.py
│   │   │   ├── orders/
│   │   │   │   └── orders.py
│   │   │   ├── inventory/
│   │   │   │   └── sync.py
│   │   │   ├── payments/
│   │   │   │   └── processing.py
│   │   │   └── agent/
│   │   │       └── conversation.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── models/
│   │   ├── user.py
│   │   ├── order.py
│   │   ├── product.py
│   │   └── conversation.py
│   ├── services/
│   │   ├── agent_service.py
│   │   ├── whatsapp_service.py
│   │   ├── telegram_service.py
│   │   ├── inventory_sync.py
│   │   └── payment_service.py
│   └── utils/
│       ├── file_processors.py
│       └── nlp_utils.py
```

## Componentes Principales

### 1. Canales de Comunicación

#### WhatsApp Business API (Producción)
- **Meta Business API**: Integración oficial para mensajería empresarial
- **Webhooks**: Recepción en tiempo real de mensajes
- **Templates**: Mensajes pre-aprobados para notificaciones
- **Media Support**: Imágenes de menú, recibos

#### Telegram Bot API (Desarrollo/Pruebas)
- **Bot Framework**: Implementación inicial más rápida
- **Inline Keyboards**: Menús interactivos
- **File Upload**: Soporte para archivos de inventario

### 2. Agente Conversacional

#### Motor de IA
```python
# Estructura del agente
class SalesAgent:
    - intent_recognition: Clasificación de intenciones del cliente
    - context_management: Manejo del estado de la conversación
    - menu_recommendation: Sugerencias personalizadas
    - order_processing: Gestión del pedido
    - payment_coordination: Coordinación de pagos
```

#### Flujos de Conversación
1. **Saludo y Menú**: Presentación y mostrar opciones
2. **Consultas**: Responder sobre productos, precios, disponibilidad
3. **Pedido**: Agregar items, modificar cantidades
4. **Confirmación**: Revisar pedido, datos de entrega
5. **Pago**: Procesar transacción
6. **Seguimiento**: Confirmación y estado del pedido

### 3. Sincronización de Inventario

#### Fuentes de Datos
- **PDFs**: Extracción con PyPDF2/pdfplumber
- **Excel/CSV**: Pandas para procesamiento
- **Google Sheets**: API de Google Sheets
- **Sincronización**: Automática por horarios/manual

#### Procesamiento
```python
class InventorySync:
    - pdf_extractor: Extrae datos de menús en PDF
    - excel_processor: Procesa hojas de cálculo
    - sheets_connector: Conecta con Google Sheets
    - data_validator: Valida consistencia de datos
    - inventory_updater: Actualiza base de datos
```

### 4. Procesamiento de Pagos

#### Integraciones Locales (Colombia)
- **Mercado Pago**: Principal para Colombia
- **PayU**: Alternativa robusta
- **Nequi/Daviplata**: Billeteras digitales populares
- **PSE**: Pagos directos desde bancos

#### Flujo de Pago
1. Cliente confirma pedido
2. Agente genera link de pago
3. Redirección a pasarela
4. Confirmación automática
5. Actualización de estado del pedido

### 5. Base de Datos

#### Esquema Principal
```sql
-- Restaurantes
restaurants (id, name, config, whatsapp_number, active)

-- Productos
products (id, restaurant_id, name, description, price, available, category)

-- Conversaciones
conversations (id, customer_phone, restaurant_id, status, context, created_at)

-- Pedidos
orders (id, conversation_id, items, total, status, payment_status, delivery_info)

-- Pagos
payments (id, order_id, amount, provider, transaction_id, status)
```

## Tecnologías y Herramientas

### Backend
- **FastAPI**: Framework web moderno y rápido
- **SQLAlchemy**: ORM para base de datos
- **PostgreSQL**: Base de datos principal
- **Redis**: Cache y gestión de sesiones
- **Celery**: Tareas asíncronas (sincronización)

### Frontend
- **React 18**: Framework frontend
- **TypeScript**: Tipado estático
- **Material-UI/Tailwind**: UI components
- **React Query**: Gestión de estado del servidor
- **WebSockets**: Comunicación en tiempo real

### IA y Procesamiento
- **OpenAI API/Anthropic**: Motor conversacional
- **spaCy/NLTK**: Procesamiento de lenguaje natural
- **Pandas**: Manipulación de datos
- **PyPDF2**: Extracción de PDFs

### Integraciones
- **WhatsApp Business API**: Mensajería principal
- **Telegram Bot API**: Canal alternativo
- **Google Sheets API**: Sincronización de inventario
- **Mercado Pago SDK**: Procesamiento de pagos

## Flujo de Implementación

### Fase 1: MVP con Telegram
1. Bot básico de Telegram
2. Menu estático en base de datos
3. Proceso de pedido simple
4. Integración básica de pagos

### Fase 2: Agente Inteligente
1. Implementar motor de IA
2. Gestión de contexto conversacional
3. Recomendaciones personalizadas
4. Manejo de consultas complejas

### Fase 3: WhatsApp Production
1. Integración con WhatsApp Business
2. Templates de mensajes
3. Soporte multimedia
4. Escalabilidad

### Fase 4: Sincronización Avanzada
1. Procesamiento de PDFs/Excel
2. Integración con Google Sheets
3. Sincronización automática
4. Validación de datos

### Fase 5: Optimización
1. Analytics y métricas
2. A/B testing de respuestas
3. Optimización de performance
4. Escalabilidad horizontal

## Consideraciones de Seguridad

- **Autenticación**: JWT tokens para dashboard
- **Webhook Security**: Verificación de firmas
- **Data Privacy**: Encriptación de datos sensibles
- **PCI Compliance**: Para procesamiento de pagos
- **Rate Limiting**: Prevención de abuso

## Métricas y Monitoreo

- **Conversiones**: Tasa de pedidos completados
- **Tiempo de Respuesta**: Latencia del agente
- **Satisfacción**: Feedback de clientes
- **Disponibilidad**: Uptime del sistema
- **Errores**: Logging y alertas

## Escalabilidad

- **Microservicios**: Separación por funcionalidad
- **Load Balancing**: Distribución de carga
- **Database Sharding**: Para múltiples restaurantes
- **CDN**: Para contenido estático
- **Auto-scaling**: Basado en demanda