# Sales Agent MVP para Restaurantes

Sistema de ventas conversacional para restaurantes con integración de Telegram, gestión de menús y procesamiento de pedidos.

## Características del MVP

- 🤖 **Bot de Telegram**: Interfaz conversacional para clientes
- 🍽️ **Gestión de Menú**: Administración de productos y categorías
- 📋 **Procesamiento de Pedidos**: Flujo completo desde orden hasta confirmación
- 💳 **Integración de Pagos**: Soporte básico para Mercado Pago
- 📊 **Dashboard Web**: Panel administrativo con React
- 🔍 **Búsqueda Semántica**: pgvector + Supabase para IA avanzada

## Estructura del Proyecto

```
sales_agent_simplified/
├── app/                          # Backend FastAPI
│   ├── api/v1/                   # Endpoints de la API
│   ├── core/                     # Configuración y base de datos
│   ├── models/                   # Modelos SQLAlchemy
│   ├── services/                 # Lógica de negocio
│   └── main.py                   # Aplicación principal
├── frontend/                     # Frontend React
│   ├── src/components/           # Componentes React
│   └── src/services/             # Servicios de API
├── alembic/                      # Migraciones de base de datos
└── requirements.txt              # Dependencias Python
```

## Instalación y Configuración

### 1. Clonar y Configurar Backend

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
```

### 2. Configurar Base de Datos (Supabase Recomendado)

**Opción A: Supabase (Recomendado - pgvector preinstalado)**

1. Crear proyecto en [supabase.com](https://supabase.com)
2. Obtener URL de conexión
3. Editar `.env`:

```env
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
TELEGRAM_BOT_TOKEN=tu_token_de_telegram_bot
OPENAI_API_KEY=tu_openai_api_key  # Para búsqueda semántica avanzada
```

**Opción B: PostgreSQL Local**

```env
DATABASE_URL=postgresql://usuario:password@localhost/sales_agent_db
REDIS_URL=redis://localhost:6379
```

### 3. Crear Base de Datos

```bash
# Crear migraciones iniciales
alembic revision --autogenerate -m "Initial migration"

# Aplicar migraciones
alembic upgrade head
```

### 4. Configurar Bot de Telegram

1. Crear bot en @BotFather de Telegram
2. Copiar el token al archivo `.env`
3. Configurar webhooks si es necesario

### 5. Ejecutar Backend

```bash
# Modo desarrollo
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# O directamente
python app/main.py
```

### 6. Configurar Frontend

```bash
cd frontend
npm install
npm start
```

## Uso del Sistema

### 1. Configuración Inicial

1. Visita `http://localhost:3000` para acceder al dashboard
2. Haz clic en "Configurar Datos de Demostración" para crear:
   - Restaurante de prueba
   - Menú de muestra con productos colombianos
3. Verifica que el bot de Telegram esté funcionando

### 2. Probar el Bot de Telegram

1. Busca tu bot en Telegram (usando el username que configuraste)
2. Envía `/start` para iniciar la conversación
3. Explora las opciones:
   - Ver menú por categorías
   - Agregar productos al pedido
   - Confirmar pedido
   - Simular proceso de pago

### 3. Monitorear desde el Dashboard

1. **Dashboard**: Estadísticas en tiempo real de pedidos y ventas
2. **Pedidos**: Gestión completa de órdenes y cambio de estados
3. **Menú**: Visualización de productos y categorías

## API Endpoints

### Menú
- `GET /api/v1/menu/restaurant/{id}/menu` - Obtener menú completo
- `GET /api/v1/menu/restaurant/{id}/menu/categories` - Obtener categorías
- `POST /api/v1/menu/restaurant/{id}/menu/sample` - Crear menú de muestra

### Pedidos
- `GET /api/v1/orders/restaurant/{id}/orders` - Obtener pedidos del restaurante
- `GET /api/v1/orders/orders/{id}` - Obtener pedido específico
- `PATCH /api/v1/orders/orders/{id}/status` - Actualizar estado del pedido

### Pagos
- `POST /api/v1/payments/create-preference` - Crear preferencia de pago
- `POST /api/v1/payments/webhook` - Webhook de Mercado Pago
- `POST /api/v1/payments/simulate-payment/{id}` - Simular pago (MVP)

### Sistema
- `POST /setup` - Configurar datos de demostración
- `GET /health` - Estado del sistema

## Flujo de Pedido

1. **Cliente inicia conversación** en Telegram con `/start`
2. **Bot presenta menú** organizado por categorías
3. **Cliente selecciona productos** usando botones interactivos
4. **Bot confirma pedido** mostrando resumen y total
5. **Sistema genera link de pago** (Mercado Pago o simulado)
6. **Cliente completa pago** y recibe confirmación
7. **Restaurante gestiona pedido** desde el dashboard web

## Características Implementadas

### Bot Conversacional
- ✅ Saludo personalizado y menú principal
- ✅ Navegación por categorías de productos
- ✅ Carrito de compras interactivo
- ✅ Confirmación de pedidos
- ✅ Respuestas automáticas a consultas comunes
- ✅ Gestión de contexto de conversación

### Backend API
- ✅ Modelos de datos completos (Restaurant, Product, Order, Conversation)
- ✅ Endpoints RESTful para todas las operaciones
- ✅ Integración básica con Mercado Pago
- ✅ Sistema de notificaciones webhook
- ✅ Configuración por variables de entorno

### Dashboard Web
- ✅ Estadísticas en tiempo real
- ✅ Gestión de pedidos con cambio de estados
- ✅ Visualización del menú por categorías
- ✅ Interfaz responsive con Material-UI

## Próximas Mejoras (Roadmap)

### Fase 2: Agente Inteligente
- [ ] Integración con OpenAI/Anthropic para respuestas más naturales
- [ ] Recomendaciones personalizadas de productos
- [ ] Manejo avanzado de contexto conversacional
- [ ] Soporte para múltiples idiomas

### Fase 3: WhatsApp Production
- [ ] Integración con WhatsApp Business API
- [ ] Templates de mensajes aprobados
- [ ] Soporte para multimedia (imágenes, audio)
- [ ] Escalabilidad para múltiples restaurantes

### Fase 4: Funcionalidades Avanzadas
- [ ] Sincronización automática desde PDFs/Excel/Sheets
- [ ] Sistema de notificaciones push
- [ ] Analytics avanzados y reportes
- [ ] Integración con sistemas POS existentes

## Tecnologías Utilizadas

### Backend
- **FastAPI**: Framework web moderno y rápido
- **SQLAlchemy**: ORM para base de datos
- **PostgreSQL**: Base de datos relacional
- **python-telegram-bot**: Librería para bot de Telegram
- **Mercado Pago SDK**: Procesamiento de pagos

### Frontend
- **React 18**: Framework frontend
- **TypeScript**: Tipado estático
- **Material-UI**: Componentes de interfaz
- **Axios**: Cliente HTTP

### Base de Datos
- **PostgreSQL**: Base de datos principal
- **Alembic**: Migraciones de esquema
- **Redis**: Cache y sesiones (futuro)

## Soporte y Contribución

Para reportar problemas o solicitar funcionalidades:
1. Crear issue en el repositorio
2. Incluir detalles del error y pasos para reproducir
3. Especificar versión del sistema operativo y Python

## Licencia

Este proyecto está desarrollado para uso interno y demostración del MVP.