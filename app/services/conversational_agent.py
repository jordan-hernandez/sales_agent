import openai
import anthropic
from sqlalchemy.orm import Session
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.product import Product
from app.models.restaurant import Restaurant
from app.models.order import Order, OrderItem
from app.core.config import settings
from typing import Dict, Any, List, Optional
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ConversationalAgent:
    """AI-powered conversational agent for restaurant sales"""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        
        # Initialize available LLM clients
        if hasattr(settings, 'openai_api_key') and settings.openai_api_key:
            self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
            
        if hasattr(settings, 'anthropic_api_key') and settings.anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        
        # Default to simple responses if no LLM configured
        self.use_llm = bool(self.openai_client or self.anthropic_client)
        
    def generate_response(
        self, 
        user_message: str, 
        conversation: Conversation, 
        db: Session,
        restaurant_context: Optional[Dict] = None
    ) -> str:
        """Generate intelligent response using LLM or fallback to keyword matching"""
        
        if self.use_llm:
            return self._generate_llm_response(user_message, conversation, db, restaurant_context)
        else:
            return self._generate_simple_response(user_message)
    
    def _generate_llm_response(
        self, 
        user_message: str, 
        conversation: Conversation, 
        db: Session,
        restaurant_context: Optional[Dict] = None
    ) -> str:
        """Generate response using LLM"""
        
        try:
            # Build context with semantic search
            context = self._build_conversation_context(conversation, db, restaurant_context)
            
            # Enhance context with semantic search results
            context = self._enhance_context_with_semantic_search(
                user_message, conversation, db, context
            )
            
            # Create enhanced prompt with semantic results
            if context.get('semantic_products') or context.get('relevant_knowledge') or context.get('customer_memories'):
                prompt = self._create_enhanced_system_prompt(context)
            else:
                prompt = self._create_system_prompt(context)
            
            # Get conversation history
            recent_messages = self._get_recent_messages(conversation.id, db)
            
            # Generate response
            if self.openai_client:
                return self._generate_openai_response(prompt, recent_messages, user_message)
            elif self.anthropic_client:
                return self._generate_anthropic_response(prompt, recent_messages, user_message)
            else:
                return self._generate_simple_response(user_message)
                
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            # Rollback the database session to recover from error
            db.rollback()
            return self._generate_simple_response(user_message)
    
    def _build_conversation_context(
        self, 
        conversation: Conversation, 
        db: Session,
        restaurant_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Build comprehensive context for the conversation"""
        
        # Get restaurant info
        restaurant = db.query(Restaurant).filter(
            Restaurant.id == conversation.restaurant_id
        ).first()
        
        # Get available products by category (limit to avoid large prompts)
        products = db.query(Product).filter(
            Product.restaurant_id == conversation.restaurant_id,
            Product.available == True
        ).limit(20).all()  # Limit for prompt efficiency
        
        products_by_category = {}
        for product in products:
            if product.category not in products_by_category:
                products_by_category[product.category] = []
            products_by_category[product.category].append({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price
            })
        
        # Get current order if exists
        current_order = db.query(Order).filter(
            Order.conversation_id == conversation.id,
            Order.status.in_(['pending'])
        ).first()
        
        order_summary = None
        if current_order and current_order.items:
            order_summary = {
                'items': [
                    {
                        'name': item.product.name,
                        'quantity': item.quantity,
                        'unit_price': item.unit_price,
                        'total': item.quantity * item.unit_price
                    }
                    for item in current_order.items
                ],
                'total': current_order.total
            }
        
        return {
            'restaurant': {
                'name': restaurant.name if restaurant else 'Restaurante',
                'description': restaurant.description if restaurant else '',
                'config': restaurant.config if restaurant else {}
            },
            'products_by_category': products_by_category,
            'current_order': order_summary,
            'customer_name': conversation.customer_name,
            'conversation_context': conversation.context or {}
        }
    
    def _create_system_prompt(self, context: Dict[str, Any]) -> str:
        """Create comprehensive system prompt for the LLM"""
        
        restaurant = context['restaurant']
        products_by_category = context['products_by_category']
        current_order = context['current_order']
        customer_name = context['customer_name']
        
        prompt = f"""Eres un asistente virtual especializado en ventas para {restaurant['name']}, un restaurante colombiano. 

TU OBJETIVO PRINCIPAL: Ayudar al cliente a realizar pedidos de comida de manera amigable y eficiente.

INFORMACIÓN DEL RESTAURANTE:
- Nombre: {restaurant['name']}
- Descripción: {restaurant.get('description', 'Restaurante colombiano tradicional')}
- Horario: Lunes a Domingo, 10:00 AM - 10:00 PM
- Entrega: 30-45 minutos en toda la ciudad
- Costo de entrega: $3,000 COP

MENÚ DISPONIBLE:"""

        # Add products by category
        for category, products in products_by_category.items():
            prompt += f"\n\n--- {category.upper()} ---"
            for product in products:
                prompt += f"\n• {product['name']} - ${product['price']:,.0f}"
                if product['description']:
                    prompt += f"\n  {product['description']}"
        
        # Add current order info
        if current_order:
            prompt += f"\n\nPEDIDO ACTUAL DEL CLIENTE:"
            for item in current_order['items']:
                prompt += f"\n• {item['name']} x{item['quantity']} = ${item['total']:,.0f}"
            prompt += f"\nTotal actual: ${current_order['total']:,.0f}"
        else:
            prompt += f"\n\nEL CLIENTE AÚN NO TIENE PRODUCTOS EN SU PEDIDO."
        
        prompt += f"""

INSTRUCCIONES DE COMPORTAMIENTO:

1. PERSONALIZACIÓN:
   - Dirígete al cliente como "{customer_name}" cuando sea apropiado
   - Sé cálido, amigable y profesional
   - Usa el contexto colombiano naturalmente

2. PROCESO DE VENTA:
   - Saluda al cliente y presenta el restaurante
   - Pregunta por sus preferencias o antoja
   - Recomienda productos específicos del menú
   - Explica los productos cuando lo pidas
   - Ayuda a construir el pedido paso a paso
   - Confirma cada item agregado
   - Sugiere complementos apropiados

3. RECOMENDACIONES INTELIGENTES:
   - Si pide "algo típico": recomienda Bandeja Paisa o Sancocho
   - Si pregunta por entradas: sugiere empanadas o patacones
   - Si quiere bebidas: recomienda limonada de coco o jugos naturales
   - Para postres: sugiere tres leches o flan de coco
   - Siempre menciona el precio cuando recomiendes

4. RESPUESTAS A CONSULTAS:
   - Horarios: "Estamos abiertos todos los días de 10:00 AM a 10:00 PM"
   - Entrega: "Hacemos entregas en 30-45 minutos por $3,000 adicionales"
   - Precios: Siempre menciona precios específicos del menú
   - Disponibilidad: Solo ofrece productos que están en el menú actual

5. MANEJO DEL PEDIDO:
   - Usa frases como "perfecto, he agregado..." cuando confirmes items
   - Mantén un resumen claro del pedido
   - Sugiere cuando el pedido esté completo para proceder al pago
   - Pregunta por detalles de entrega si es necesario

6. TONO Y ESTILO:
   - Natural y conversacional
   - Entusiasta pero no agresivo
   - Usa emojis moderadamente (🍽️ 🥘 😊)
   - Evita ser repetitivo
   - Responde de manera concisa pero completa

7. LIMITACIONES:
   - NO agregues productos automáticamente al pedido
   - NO inventes productos que no están en el menú
   - NO prometas tiempos de entrega diferentes a 30-45 minutos
   - Si no sabes algo específico, ofrece contactar directamente

EJEMPLO DE CONVERSACIÓN IDEAL:
Cliente: "Hola, tengo hambre"
Tú: "¡Hola {customer_name}! 😊 ¿Qué antojo tienes hoy? Tenemos deliciosos platos típicos colombianos. ¿Te provoca algo contundente como una Bandeja Paisa ($28,000) o prefieres empezar con unas empanadas ($8,000)?"

RESPONDE SIEMPRE EN ESPAÑOL y mantén el foco en ayudar al cliente a completar su pedido de manera natural y eficiente."""

        return prompt
    
    def _get_recent_messages(self, conversation_id: int, db: Session, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation messages for context"""
        
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).limit(limit).all()
        
        # Reverse to get chronological order
        messages = list(reversed(messages))
        
        conversation_history = []
        for message in messages:
            role = "user" if message.is_from_customer else "assistant"
            conversation_history.append({
                "role": role,
                "content": message.content
            })
        
        return conversation_history
    
    def _generate_openai_response(
        self, 
        system_prompt: str, 
        conversation_history: List[Dict[str, str]], 
        user_message: str
    ) -> str:
        """Generate response using OpenAI GPT"""
        
        try:
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add conversation history
            messages.extend(conversation_history)
            
            # Add current message
            messages.append({"role": "user", "content": user_message})
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=300,
                temperature=0.7,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._generate_simple_response(user_message)
    
    def _generate_anthropic_response(
        self, 
        system_prompt: str, 
        conversation_history: List[Dict[str, str]], 
        user_message: str
    ) -> str:
        """Generate response using Anthropic Claude"""
        
        try:
            # Build conversation for Claude
            conversation_text = ""
            for msg in conversation_history:
                if msg["role"] == "user":
                    conversation_text += f"\n\nHuman: {msg['content']}"
                else:
                    conversation_text += f"\n\nAssistant: {msg['content']}"
            
            conversation_text += f"\n\nHuman: {user_message}\n\nAssistant:"
            
            full_prompt = system_prompt + conversation_text
            
            response = self.anthropic_client.completions.create(
                model="claude-3-haiku-20240307",
                prompt=full_prompt,
                max_tokens_to_sample=300,
                temperature=0.7
            )
            
            return response.completion.strip()
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return self._generate_simple_response(user_message)
    
    def _generate_simple_response(self, message: str) -> str:
        """Fallback to simple keyword-based responses"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['hola', 'buenas', 'hey', 'saludos']):
            return "¡Hola! Bienvenido a nuestro restaurante 😊 ¿En qué puedo ayudarte hoy? Puedes ver nuestro menú o hacer un pedido."
        
        elif any(word in message_lower for word in ['menu', 'menú', 'comida', 'productos', 'que tienen']):
            return "¡Perfecto! Tenemos deliciosos platos colombianos. Te recomiendo ver nuestro menú completo con el botón de abajo, o puedo recomendarte algo específico. ¿Qué tipo de comida te provoca?"
        
        elif any(word in message_lower for word in ['precio', 'costo', 'cuanto', 'vale', 'barato']):
            return "Nuestros precios son muy accesibles. Las entradas van desde $6,000, platos principales desde $24,000 y bebidas desde $4,000. ¿Te gustaría ver algo específico?"
        
        elif any(word in message_lower for word in ['entrega', 'domicilio', 'envio', 'llevar']):
            return "¡Claro! Hacemos entregas en toda la ciudad en 30-45 minutos. El costo de entrega es de $3,000. ¿Te gustaría hacer un pedido?"
        
        elif any(word in message_lower for word in ['horario', 'hora', 'abierto', 'cerrado']):
            return "Estamos abiertos todos los días de 10:00 AM a 10:00 PM. ¡Perfecto momento para hacer tu pedido!"
        
        elif any(word in message_lower for word in ['recomendacion', 'recomienda', 'mejor', 'tipico', 'tradicional']):
            return "¡Te recomiendo nuestra Bandeja Paisa ($28,000) - es nuestro plato estrella! También el Sancocho de Gallina ($25,000) está delicioso. ¿Cuál te llama más la atención?"
        
        elif any(word in message_lower for word in ['hambre', 'antojo', 'quiero comer']):
            return "¡Perfecto! ¿Qué tipo de antojo tienes? ¿Algo contundente como una bandeja paisa, o prefieres empezar con unas empanadas? También tenemos pescado fresco y pollo asado."
        
        else:
            return "Entiendo tu consulta 😊 Estoy aquí para ayudarte con tu pedido. ¿Te gustaría ver nuestro menú, que te recomiende algo, o tienes alguna pregunta específica?"
    
    def analyze_intent(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user intent and extract relevant information"""
        
        message_lower = message.lower()
        
        intent_analysis = {
            'intent': 'general_inquiry',
            'confidence': 0.5,
            'entities': {},
            'suggested_action': 'show_menu'
        }
        
        # Intent classification
        if any(word in message_lower for word in ['quiero', 'me das', 'agregar', 'pedir', 'ordenar']):
            intent_analysis['intent'] = 'order_request'
            intent_analysis['confidence'] = 0.8
            intent_analysis['suggested_action'] = 'help_with_order'
            
        elif any(word in message_lower for word in ['precio', 'costo', 'cuanto', 'vale']):
            intent_analysis['intent'] = 'price_inquiry'
            intent_analysis['confidence'] = 0.9
            intent_analysis['suggested_action'] = 'provide_pricing'
            
        elif any(word in message_lower for word in ['menu', 'menú', 'que tienen', 'opciones']):
            intent_analysis['intent'] = 'menu_request'
            intent_analysis['confidence'] = 0.9
            intent_analysis['suggested_action'] = 'show_menu'
            
        elif any(word in message_lower for word in ['recomendacion', 'recomienda', 'mejor']):
            intent_analysis['intent'] = 'recommendation_request'
            intent_analysis['confidence'] = 0.8
            intent_analysis['suggested_action'] = 'provide_recommendations'
        
        # Entity extraction (simple keyword matching)
        product_keywords = {
            'bandeja': 'Bandeja Paisa',
            'sancocho': 'Sancocho de Gallina',
            'empanada': 'Empanadas de Pollo',
            'pescado': 'Pescado a la Plancha',
            'pollo': 'Pollo Asado',
            'limonada': 'Limonada de Coco',
            'tres leches': 'Tres Leches'
        }
        
        for keyword, product_name in product_keywords.items():
            if keyword in message_lower:
                intent_analysis['entities']['mentioned_product'] = product_name
                intent_analysis['intent'] = 'product_inquiry'
                intent_analysis['confidence'] = 0.9
                break
        
        return intent_analysis
    
    def _enhance_context_with_semantic_search(
        self, 
        user_message: str, 
        conversation: Conversation, 
        db: Session, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance context with semantic search results"""
        
        try:
            from app.services.vector_search import vector_search_service
            
            enhanced_context = context.copy()
            
            # Semantic product search
            relevant_products = vector_search_service.search_products_semantic(
                user_message, 
                conversation.restaurant_id, 
                db, 
                limit=3
            )
            
            if relevant_products:
                enhanced_context['semantic_products'] = relevant_products
                logger.info(f"Found {len(relevant_products)} semantically relevant products")
            
            # Search knowledge base
            knowledge_items = vector_search_service.search_knowledge_base(
                user_message,
                conversation.restaurant_id,
                db,
                limit=2
            )
            
            if knowledge_items:
                enhanced_context['relevant_knowledge'] = knowledge_items
                logger.info(f"Found {len(knowledge_items)} relevant knowledge items")
            
            # Search conversation memory for this customer
            if conversation.customer_phone:
                memories = vector_search_service.search_conversation_memory(
                    user_message,
                    conversation.customer_phone,
                    conversation.restaurant_id,
                    db,
                    limit=2
                )
                
                if memories:
                    enhanced_context['customer_memories'] = memories
                    logger.info(f"Found {len(memories)} relevant customer memories")
            
            return enhanced_context
            
        except Exception as e:
            logger.error(f"Error enhancing context with semantic search: {e}")
            # Rollback the database session to recover from error
            db.rollback()
            return context  # Return original context without semantic enhancement
    
    def _create_enhanced_system_prompt(self, context: Dict[str, Any]) -> str:
        """Create enhanced system prompt with semantic search results"""
        
        base_prompt = self._create_system_prompt(context)
        
        # Add semantic search results to prompt
        if context.get('semantic_products'):
            base_prompt += "\n\n🎯 PRODUCTOS MÁS RELEVANTES PARA ESTA CONSULTA:"
            for product in context['semantic_products']:
                base_prompt += f"\n• {product['name']} - ${product['price']:,.0f}"
                if product['description']:
                    base_prompt += f" - {product['description']}"
                base_prompt += f" (relevancia: {product['similarity_score']:.1f})"
        
        if context.get('relevant_knowledge'):
            base_prompt += "\n\n📚 INFORMACIÓN RELEVANTE DEL RESTAURANTE:"
            for item in context['relevant_knowledge']:
                base_prompt += f"\nP: {item['question']}\nR: {item['answer']}"
        
        if context.get('customer_memories'):
            base_prompt += "\n\n🧠 RECORDAR SOBRE ESTE CLIENTE:"
            for memory in context['customer_memories']:
                base_prompt += f"\n• {memory['summary']} ({memory['memory_type']})"
        
        base_prompt += "\n\n⚡ INSTRUCCIÓN ESPECIAL: Usa la información de relevancia semántica arriba para dar respuestas más precisas y personalizadas."
        
        return base_prompt


# Global agent instance
conversational_agent = ConversationalAgent()