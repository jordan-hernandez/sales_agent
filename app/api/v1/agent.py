from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.conversational_agent import conversational_agent
from app.models.conversation import Conversation, ConversationStatus
from app.models.restaurant import Restaurant
from pydantic import BaseModel
from typing import Dict, Any, Optional

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    restaurant_id: int
    customer_name: str = "Cliente"
    chat_id: str = "web_test"


class ChatResponse(BaseModel):
    response: str
    intent_analysis: Optional[Dict[str, Any]] = None
    conversation_id: int
    restaurant_context: Optional[Dict[str, Any]] = None


class AgentConfigResponse(BaseModel):
    llm_enabled: bool
    available_models: list
    current_model: str
    response_length: int
    temperature: float


@router.post("/chat", response_model=ChatResponse)
def chat_with_agent(request: ChatRequest, db: Session = Depends(get_db)):
    """Test chat with the conversational agent"""
    
    # Verify restaurant exists
    restaurant = db.query(Restaurant).filter(Restaurant.id == request.restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    # Get or create test conversation
    conversation = db.query(Conversation).filter(
        Conversation.chat_id == request.chat_id,
        Conversation.restaurant_id == request.restaurant_id,
        Conversation.status == ConversationStatus.ACTIVE
    ).first()
    
    if not conversation:
        conversation = Conversation(
            restaurant_id=request.restaurant_id,
            customer_phone=request.chat_id,
            customer_name=request.customer_name,
            platform="web",
            chat_id=request.chat_id,
            status=ConversationStatus.ACTIVE
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    # Generate response
    try:
        response = conversational_agent.generate_response(
            request.message, 
            conversation, 
            db
        )
        
        # Analyze intent
        context = conversational_agent._build_conversation_context(conversation, db)
        intent_analysis = conversational_agent.analyze_intent(request.message, context)
        
        return ChatResponse(
            response=response,
            intent_analysis=intent_analysis,
            conversation_id=conversation.id,
            restaurant_context={
                "restaurant_name": restaurant.name,
                "available_products": len(context.get('products_by_category', {})),
                "current_order_items": len(context.get('current_order', {}).get('items', []))
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")


@router.get("/config", response_model=AgentConfigResponse)
def get_agent_config():
    """Get agent configuration and capabilities"""
    
    available_models = []
    current_model = "keyword_matching"
    llm_enabled = False
    
    if conversational_agent.openai_client:
        available_models.append("openai_gpt-3.5-turbo")
        current_model = "openai_gpt-3.5-turbo"
        llm_enabled = True
        
    if conversational_agent.anthropic_client:
        available_models.append("anthropic_claude-3-haiku")
        if not llm_enabled:  # If no OpenAI, use Anthropic as primary
            current_model = "anthropic_claude-3-haiku"
        llm_enabled = True
    
    if not available_models:
        available_models = ["keyword_matching_fallback"]
    
    return AgentConfigResponse(
        llm_enabled=llm_enabled,
        available_models=available_models,
        current_model=current_model,
        response_length=300,
        temperature=0.7
    )


@router.post("/analyze-intent")
def analyze_message_intent(request: ChatRequest, db: Session = Depends(get_db)):
    """Analyze the intent of a user message"""
    
    # Get restaurant context
    restaurant = db.query(Restaurant).filter(Restaurant.id == request.restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    # Create minimal context for intent analysis
    conversation = db.query(Conversation).filter(
        Conversation.chat_id == request.chat_id,
        Conversation.restaurant_id == request.restaurant_id
    ).first()
    
    if conversation:
        context = conversational_agent._build_conversation_context(conversation, db)
    else:
        context = {"restaurant": {"name": restaurant.name}}
    
    # Analyze intent
    intent_analysis = conversational_agent.analyze_intent(request.message, context)
    
    return {
        "message": request.message,
        "intent_analysis": intent_analysis,
        "restaurant": restaurant.name
    }


@router.get("/conversation/{conversation_id}/history")
def get_conversation_history(conversation_id: int, db: Session = Depends(get_db)):
    """Get conversation history for analysis"""
    
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = conversational_agent._get_recent_messages(conversation_id, db, limit=20)
    
    return {
        "conversation_id": conversation_id,
        "customer": conversation.customer_name,
        "platform": conversation.platform,
        "status": conversation.status,
        "messages": messages,
        "context": conversation.context or {}
    }


@router.post("/test-prompts")
def test_different_prompts():
    """Test different conversation scenarios"""
    
    test_scenarios = [
        {
            "scenario": "greeting",
            "message": "Hola, buenas tardes",
            "expected_intent": "greeting",
            "description": "Customer greets the bot"
        },
        {
            "scenario": "menu_request", 
            "message": "¿Qué tienen de menú?",
            "expected_intent": "menu_request",
            "description": "Customer asks for menu"
        },
        {
            "scenario": "product_order",
            "message": "Quiero una bandeja paisa",
            "expected_intent": "order_request", 
            "description": "Customer wants to order specific product"
        },
        {
            "scenario": "price_inquiry",
            "message": "¿Cuánto cuesta el pescado?",
            "expected_intent": "price_inquiry",
            "description": "Customer asks for price"
        },
        {
            "scenario": "recommendation_request",
            "message": "¿Qué me recomiendas?",
            "expected_intent": "recommendation_request",
            "description": "Customer asks for recommendations"
        },
        {
            "scenario": "delivery_inquiry",
            "message": "¿Hacen domicilios?",
            "expected_intent": "delivery_inquiry", 
            "description": "Customer asks about delivery"
        }
    ]
    
    return {
        "test_scenarios": test_scenarios,
        "instructions": "Use POST /agent/chat with these messages to test responses",
        "llm_status": "enabled" if conversational_agent.use_llm else "disabled - using keyword fallback"
    }