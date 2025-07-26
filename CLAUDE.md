# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a conversational sales agent MVP for restaurants with Telegram bot integration, semantic search capabilities using pgvector, and a React admin dashboard. The system allows customers to place orders through natural conversation while providing restaurant owners with a web-based management interface.

## Common Development Commands

### Backend Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server (auto-reload enabled)
python app/main.py
# Alternative: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Database migrations
alembic revision --autogenerate -m "Migration description"
alembic upgrade head

# Test database connection
python test_connection.py
```

### Frontend Development
```bash
cd frontend
npm install
npm start  # Runs on port 3000, proxies to backend on 8000
npm run build
npm test
```

### Setup and Initialization
```bash
# Copy environment configuration
cp .env.example .env

# Create demo data (restaurant, menu, products)
# POST to /setup endpoint or run:
python setup_demo_data.py
```

## Architecture Overview

### Backend Structure (FastAPI)
- **`app/main.py`**: Application entry point with FastAPI app initialization
- **`app/core/`**: Configuration (`config.py`) and database setup (`database.py`)
- **`app/models/`**: SQLAlchemy models (Restaurant, Product, Order, Conversation, Message, Embeddings)
- **`app/services/`**: Business logic including:
  - `telegram_service.py`: Telegram bot with conversational flow
  - `conversational_agent.py`: AI agent using OpenAI/Anthropic APIs
  - `vector_search.py`: Semantic search using pgvector
  - `payment_service.py`: Mercado Pago integration
  - `menu_service.py`: Menu management and sample data creation
- **`app/api/v1/`**: RESTful API endpoints organized by domain

### Frontend Structure (React + TypeScript)
- **Material-UI**: Component library for consistent design
- **`src/components/`**: Dashboard, Orders, Menu, InventorySync, Layout
- **`src/services/api.ts`**: Centralized API client with TypeScript interfaces
- **Proxy configuration**: Frontend proxies API requests to backend on port 8000

### Database Architecture
- **PostgreSQL** with **pgvector** extension for semantic search
- **Supabase** recommended for cloud hosting (pgvector pre-installed)
- **Core entities**: restaurants → products → orders/order_items → conversations → messages
- **AI/ML tables**: product_embeddings, conversation_memories, knowledge_base, search_logs

## Key Integrations

### Telegram Bot
- Uses `python-telegram-bot` library
- Runs in background thread alongside FastAPI server
- Interactive menus with inline keyboards
- Conversation state management
- Payment flow integration

### AI/ML Components
- **OpenAI GPT-3.5-turbo** and **Anthropic Claude Haiku** for conversational AI
- **sentence-transformers** for local embeddings generation
- **pgvector** for efficient semantic search
- Fallback to keyword-based responses when LLM unavailable

### Payment Processing
- **Mercado Pago** integration for Colombian market
- Webhook handling for payment status updates
- Payment simulation endpoint for MVP testing

## Environment Configuration

Required environment variables:
```env
DATABASE_URL=postgresql://...              # Supabase connection URL preferred
TELEGRAM_BOT_TOKEN=...                     # From @BotFather
OPENAI_API_KEY=sk-...                      # For GPT-3.5-turbo
ANTHROPIC_API_KEY=sk-ant-...               # For Claude Haiku
MERCADOPAGO_ACCESS_TOKEN=...               # Payment processing
```

## Development Workflow

1. **Database Setup**: Configure Supabase or local PostgreSQL with pgvector
2. **Environment**: Copy `.env.example` to `.env` and configure credentials
3. **Migrations**: Run `alembic upgrade head` to create database schema
4. **Demo Data**: POST to `/setup` endpoint to create sample restaurant and menu
5. **Bot Configuration**: Set up Telegram bot token and webhook (if needed)
6. **Testing**: Use `/health` endpoint and Telegram bot for end-to-end testing

## API Architecture

- **Versioned APIs**: All endpoints under `/api/v1/` prefix
- **RESTful design**: Standard HTTP methods and status codes
- **CORS enabled**: For frontend-backend communication
- **Error handling**: Consistent error responses with proper HTTP status codes

## MVP Limitations

- Single restaurant support (multi-tenant architecture ready but not active)
- Basic authentication (no user management system)
- Limited payment methods (Mercado Pago only)
- Simple error logging (no comprehensive monitoring)

## Production Considerations

- Background processing via threads (Telegram bot, scheduler)
- Database connection pooling via SQLAlchemy
- Environment-based configuration management
- Migration system for schema changes
- Webhook support for external integrations