from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.vector_search import vector_search_service
from app.models.restaurant import Restaurant
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

router = APIRouter()


class EmbeddingStats(BaseModel):
    created: int
    updated: int
    errors: int


class SemanticSearchRequest(BaseModel):
    query: str
    restaurant_id: int
    limit: int = 5
    similarity_threshold: float = 0.3


class SemanticSearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    search_time_ms: int
    total_results: int


class KnowledgeBaseEntry(BaseModel):
    question: str
    answer: str
    category: str
    tags: List[str]


class ConversationMemoryEntry(BaseModel):
    memory_type: str  # 'preference', 'order_history', 'complaint', 'compliment'
    content: str
    summary: str
    importance_score: float = 1.0


@router.post("/embeddings/products/{restaurant_id}", response_model=EmbeddingStats)
def create_product_embeddings(restaurant_id: int, db: Session = Depends(get_db)):
    """Generate embeddings for all products in a restaurant"""
    
    # Verify restaurant exists
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    try:
        stats = vector_search_service.create_product_embeddings(restaurant_id, db)
        return EmbeddingStats(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating embeddings: {str(e)}")


@router.post("/search/products", response_model=SemanticSearchResponse)
def search_products_semantic(request: SemanticSearchRequest, db: Session = Depends(get_db)):
    """Search products using semantic similarity"""
    
    # Verify restaurant exists
    restaurant = db.query(Restaurant).filter(Restaurant.id == request.restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    try:
        import time
        start_time = time.time()
        
        results = vector_search_service.search_products_semantic(
            request.query,
            request.restaurant_id,
            db,
            request.limit,
            request.similarity_threshold
        )
        
        search_time = int((time.time() - start_time) * 1000)
        
        return SemanticSearchResponse(
            query=request.query,
            results=results,
            search_time_ms=search_time,
            total_results=len(results)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in semantic search: {str(e)}")


@router.post("/search/knowledge", response_model=SemanticSearchResponse)
def search_knowledge_base(request: SemanticSearchRequest, db: Session = Depends(get_db)):
    """Search knowledge base using semantic similarity"""
    
    try:
        import time
        start_time = time.time()
        
        results = vector_search_service.search_knowledge_base(
            request.query,
            request.restaurant_id,
            db,
            request.limit,
            request.similarity_threshold
        )
        
        search_time = int((time.time() - start_time) * 1000)
        
        return SemanticSearchResponse(
            query=request.query,
            results=results,
            search_time_ms=search_time,
            total_results=len(results)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in knowledge search: {str(e)}")


@router.post("/knowledge/{restaurant_id}")
def create_knowledge_entry(
    restaurant_id: int, 
    entry: KnowledgeBaseEntry, 
    db: Session = Depends(get_db)
):
    """Create a knowledge base entry with embedding"""
    
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    try:
        success = vector_search_service.create_knowledge_base_entry(
            restaurant_id,
            entry.question,
            entry.answer,
            entry.category,
            entry.tags,
            db
        )
        
        if success:
            return {"message": "Knowledge base entry created successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create knowledge base entry")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating knowledge entry: {str(e)}")


@router.post("/memory/{conversation_id}")
def store_conversation_memory(
    conversation_id: int,
    memory: ConversationMemoryEntry,
    db: Session = Depends(get_db)
):
    """Store a conversation memory with embedding"""
    
    # Get conversation to verify it exists and get restaurant_id
    from app.models.conversation import Conversation
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    try:
        success = vector_search_service.store_conversation_memory(
            conversation_id,
            conversation.restaurant_id,
            conversation.customer_phone,
            memory.memory_type,
            memory.content,
            memory.summary,
            memory.importance_score,
            db
        )
        
        if success:
            return {"message": "Conversation memory stored successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to store memory")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error storing memory: {str(e)}")


@router.get("/analytics/{restaurant_id}")
def get_search_analytics(restaurant_id: int, days: int = 7, db: Session = Depends(get_db)):
    """Get search analytics for a restaurant"""
    
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    try:
        analytics = vector_search_service.get_search_analytics(restaurant_id, db, days)
        return {
            "restaurant_id": restaurant_id,
            "period_days": days,
            "analytics": analytics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting analytics: {str(e)}")


@router.get("/status")
def get_vector_search_status():
    """Get vector search service status"""
    
    return {
        "service_status": "active",
        "embedding_model": vector_search_service.model_name,
        "embedding_dimension": vector_search_service.embedding_dimension,
        "use_openai_embeddings": vector_search_service.use_openai_embeddings,
        "model_loaded": vector_search_service.embedding_model is not None,
        "supported_operations": [
            "product_embeddings",
            "semantic_search", 
            "knowledge_base",
            "conversation_memory",
            "analytics"
        ]
    }


@router.post("/test-embedding")
def test_embedding_generation(text: str):
    """Test embedding generation for debugging"""
    
    try:
        import time
        start_time = time.time()
        
        embedding = vector_search_service.get_embedding(text)
        generation_time = int((time.time() - start_time) * 1000)
        
        return {
            "text": text,
            "embedding_length": len(embedding),
            "embedding_sample": embedding[:5].tolist(),  # First 5 dimensions
            "generation_time_ms": generation_time,
            "model": vector_search_service.model_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating embedding: {str(e)}")


@router.post("/setup-demo-knowledge/{restaurant_id}")
def setup_demo_knowledge_base(restaurant_id: int, db: Session = Depends(get_db)):
    """Set up demo knowledge base entries for testing"""
    
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    demo_entries = [
        {
            "question": "¿Cuál es el horario de atención?",
            "answer": "Estamos abiertos de lunes a domingo de 10:00 AM a 10:00 PM.",
            "category": "horarios",
            "tags": ["horario", "abierto", "cerrado", "atención"]
        },
        {
            "question": "¿Hacen entregas a domicilio?",
            "answer": "Sí, hacemos entregas en toda la ciudad. El tiempo estimado es de 30-45 minutos y el costo es de $3,000.",
            "category": "entrega",
            "tags": ["domicilio", "entrega", "delivery", "envío"]
        },
        {
            "question": "¿Tienen opciones vegetarianas?",
            "answer": "Sí, tenemos varias opciones vegetarianas como arepas de queso, patacones con guacamole, y ensaladas frescas.",
            "category": "menu",
            "tags": ["vegetariano", "vegano", "opciones", "sin carne"]
        },
        {
            "question": "¿Cuáles son los métodos de pago?",
            "answer": "Aceptamos efectivo, tarjetas de crédito y débito, transferencias bancarias y pagos por Nequi o Daviplata.",
            "category": "pagos",
            "tags": ["pago", "tarjeta", "efectivo", "nequi", "daviplata"]
        },
        {
            "question": "¿Cuál es su plato más popular?",
            "answer": "Nuestra Bandeja Paisa es nuestro plato estrella. Es un plato tradicional muy completo que incluye frijoles, arroz, carne, chorizo y más.",
            "category": "menu",
            "tags": ["popular", "recomendado", "bandeja paisa", "tradicional"]
        }
    ]
    
    created_count = 0
    for entry in demo_entries:
        try:
            success = vector_search_service.create_knowledge_base_entry(
                restaurant_id,
                entry["question"],
                entry["answer"],
                entry["category"],
                entry["tags"],
                db
            )
            if success:
                created_count += 1
        except Exception as e:
            continue
    
    return {
        "message": f"Demo knowledge base setup completed",
        "entries_created": created_count,
        "total_entries": len(demo_entries)
    }