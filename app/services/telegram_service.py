from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.restaurant import Restaurant
from app.models.conversation import Conversation, ConversationStatus
from app.models.message import Message
from app.models.product import Product
from app.models.order import Order, OrderItem, OrderStatus
from app.core.config import settings
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self):
        self.application = Application.builder().token(settings.telegram_bot_token).build()
        self.setup_handlers()

    def setup_handlers(self):
        # Commands
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("menu", self.menu_command))
        self.application.add_handler(CommandHandler("pedido", self.order_command))
        
        # Callback queries (buttons)
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Messages
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        chat_id = str(update.effective_chat.id)
        
        # Get or create conversation
        db = next(get_db())
        conversation = self.get_or_create_conversation(db, chat_id, user.first_name)
        
        welcome_text = f"""¡Hola {user.first_name}! 👋

Bienvenido a nuestro sistema de pedidos. Soy tu asistente virtual y te ayudaré a realizar tu pedido.

¿Qué te gustaría hacer?"""

        keyboard = [
            [InlineKeyboardButton("🍽️ Ver Menú", callback_data="show_menu")],
            [InlineKeyboardButton("📞 Contactar", callback_data="contact")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
        
        # Save message
        self.save_message(db, conversation.id, welcome_text, False)
        db.close()

    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /menu command"""
        await self.show_menu(update, context)

    async def order_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /pedido command"""
        await self.show_current_order(update, context)

    async def show_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, category=None):
        """Show restaurant menu"""
        db = next(get_db())
        
        # Get default restaurant (for MVP)
        restaurant = db.query(Restaurant).first()
        if not restaurant:
            await update.effective_message.reply_text("No hay restaurantes disponibles en este momento.")
            db.close()
            return

        # Get products
        query = db.query(Product).filter(Product.restaurant_id == restaurant.id, Product.available == True)
        if category:
            query = query.filter(Product.category == category)
        
        products = query.all()
        
        if not products:
            await update.effective_message.reply_text("No hay productos disponibles en este momento.")
            db.close()
            return

        # Group by category
        categories = {}
        for product in products:
            if product.category not in categories:
                categories[product.category] = []
            categories[product.category].append(product)

        # Show categories or products
        if not category:
            # Show categories
            text = f"🍽️ **{restaurant.name}**\n\nSelecciona una categoría:"
            keyboard = []
            for cat_name in categories.keys():
                keyboard.append([InlineKeyboardButton(f"{cat_name.title()}", callback_data=f"category_{cat_name}")])
            keyboard.append([InlineKeyboardButton("🛒 Ver Pedido Actual", callback_data="show_order")])
        else:
            # Show products in category
            text = f"🍽️ **{category.title()}**\n\n"
            keyboard = []
            
            for product in categories.get(category, []):
                text += f"**{product.name}**\n"
                text += f"{product.description}\n" if product.description else ""
                text += f"💰 ${product.price:,.0f}\n\n"
                
                keyboard.append([InlineKeyboardButton(
                    f"➕ Agregar {product.name}", 
                    callback_data=f"add_product_{product.id}"
                )])
            
            keyboard.append([InlineKeyboardButton("⬅️ Volver al Menú", callback_data="show_menu")])
            keyboard.append([InlineKeyboardButton("🛒 Ver Pedido", callback_data="show_order")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.effective_message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
        db.close()

    async def show_current_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current order"""
        chat_id = str(update.effective_chat.id)
        db = next(get_db())
        
        # Get current conversation and order
        conversation = db.query(Conversation).filter(
            Conversation.chat_id == chat_id,
            Conversation.status == ConversationStatus.ACTIVE
        ).first()
        
        if not conversation:
            await update.effective_message.reply_text("No tienes una conversación activa.")
            db.close()
            return

        # Get current order
        order = db.query(Order).filter(
            Order.conversation_id == conversation.id,
            Order.status == OrderStatus.PENDING
        ).first()

        if not order or not order.items:
            text = "🛒 Tu pedido está vacío\n\n¿Qué te gustaría ordenar?"
            keyboard = [[InlineKeyboardButton("🍽️ Ver Menú", callback_data="show_menu")]]
        else:
            text = f"🛒 **Tu Pedido Actual:**\n\n"
            total = 0
            
            for item in order.items:
                item_total = item.quantity * item.unit_price
                total += item_total
                text += f"• {item.product.name} x{item.quantity}\n"
                text += f"  ${item.unit_price:,.0f} c/u = ${item_total:,.0f}\n\n"
            
            text += f"**Total: ${total:,.0f}**"
            
            keyboard = [
                [InlineKeyboardButton("➕ Agregar más productos", callback_data="show_menu")],
                [InlineKeyboardButton("✅ Confirmar Pedido", callback_data="confirm_order")],
                [InlineKeyboardButton("🗑️ Limpiar Pedido", callback_data="clear_order")]
            ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.effective_message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
        db.close()

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "show_menu":
            await self.show_menu(update, context)
        elif data.startswith("category_"):
            category = data.replace("category_", "")
            await self.show_menu(update, context, category)
        elif data.startswith("add_product_"):
            product_id = int(data.replace("add_product_", ""))
            await self.add_product_to_order(update, context, product_id)
        elif data == "show_order":
            await self.show_current_order(update, context)
        elif data == "confirm_order":
            await self.confirm_order(update, context)
        elif data == "clear_order":
            await self.clear_order(update, context)
        elif data == "contact":
            await self.show_contact_info(update, context)

    async def add_product_to_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE, product_id: int):
        """Add product to order"""
        chat_id = str(update.effective_chat.id)
        user = update.effective_user
        db = next(get_db())
        
        # Get product
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            await update.callback_query.edit_message_text("Producto no encontrado.")
            db.close()
            return

        # Get or create conversation
        conversation = self.get_or_create_conversation(db, chat_id, user.first_name)
        
        # Get or create order
        order = db.query(Order).filter(
            Order.conversation_id == conversation.id,
            Order.status == OrderStatus.PENDING
        ).first()
        
        if not order:
            order = Order(
                restaurant_id=product.restaurant_id,
                conversation_id=conversation.id,
                customer_name=user.first_name,
                customer_phone=user.username or chat_id
            )
            db.add(order)
            db.flush()

        # Check if product already in order
        existing_item = None
        for item in order.items:
            if item.product_id == product_id:
                existing_item = item
                break

        if existing_item:
            existing_item.quantity += 1
        else:
            order_item = OrderItem(
                order_id=order.id,
                product_id=product_id,
                quantity=1,
                unit_price=product.price
            )
            db.add(order_item)

        # Update order total
        total = sum(item.quantity * item.unit_price for item in order.items)
        order.total = total
        order.subtotal = total  # For MVP, no delivery fee
        
        db.commit()
        
        text = f"✅ **{product.name}** agregado al pedido!\n\n¿Qué más te gustaría hacer?"
        keyboard = [
            [InlineKeyboardButton("🛒 Ver Pedido", callback_data="show_order")],
            [InlineKeyboardButton("🍽️ Seguir Comprando", callback_data="show_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        db.close()

    async def confirm_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm order and proceed to payment"""
        chat_id = str(update.effective_chat.id)
        db = next(get_db())
        
        conversation = db.query(Conversation).filter(
            Conversation.chat_id == chat_id,
            Conversation.status == ConversationStatus.ACTIVE
        ).first()
        
        if not conversation:
            await update.callback_query.edit_message_text("No se encontró la conversación.")
            db.close()
            return

        order = db.query(Order).filter(
            Order.conversation_id == conversation.id,
            Order.status == OrderStatus.PENDING
        ).first()

        if not order or not order.items:
            await update.callback_query.edit_message_text("No hay productos en el pedido.")
            db.close()
            return

        # For MVP - simple confirmation without actual payment integration
        order.status = OrderStatus.CONFIRMED
        db.commit()

        text = f"""✅ **¡Pedido Confirmado!**

**Resumen del pedido:**
"""
        for item in order.items:
            text += f"• {item.product.name} x{item.quantity} = ${item.quantity * item.unit_price:,.0f}\n"
        
        text += f"\n**Total: ${order.total:,.0f}**\n\n"
        text += "Te contactaremos pronto para coordinar la entrega. ¡Gracias por tu pedido!"

        await update.callback_query.edit_message_text(text, parse_mode='Markdown')
        db.close()

    async def clear_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Clear current order"""
        chat_id = str(update.effective_chat.id)
        db = next(get_db())
        
        conversation = db.query(Conversation).filter(
            Conversation.chat_id == chat_id,
            Conversation.status == ConversationStatus.ACTIVE
        ).first()
        
        if conversation:
            order = db.query(Order).filter(
                Order.conversation_id == conversation.id,
                Order.status == OrderStatus.PENDING
            ).first()
            
            if order:
                db.delete(order)
                db.commit()

        text = "🗑️ Pedido eliminado.\n\n¿Te gustaría empezar un nuevo pedido?"
        keyboard = [[InlineKeyboardButton("🍽️ Ver Menú", callback_data="show_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        db.close()

    async def show_contact_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show contact information"""
        text = """📞 **Información de Contacto**

🕒 Horario de atención:
Lunes a Domingo: 10:00 AM - 10:00 PM

📱 WhatsApp: +57 123 456 7890
📧 Email: pedidos@restaurante.com

🚚 Realizamos entregas en toda la ciudad
⏱️ Tiempo de entrega: 30-45 minutos"""

        keyboard = [[InlineKeyboardButton("🍽️ Ver Menú", callback_data="show_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.effective_message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        user_message = update.message.text
        user = update.effective_user
        chat_id = str(update.effective_chat.id)
        
        db = next(get_db())
        conversation = self.get_or_create_conversation(db, chat_id, user.first_name)
        
        # Save user message
        self.save_message(db, conversation.id, user_message, True)
        
        try:
            # Generate intelligent response using LLM agent
            from app.services.conversational_agent import conversational_agent
            response = conversational_agent.generate_response(user_message, conversation, db)
            
            # Save bot response
            self.save_message(db, conversation.id, response, False)
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # Rollback the transaction to recover from error
            db.rollback()
            response = self.generate_response(user_message)
        
        # Create buttons
        keyboard = [
            [InlineKeyboardButton("🍽️ Ver Menú", callback_data="show_menu")],
            [InlineKeyboardButton("🛒 Ver Pedido", callback_data="show_order")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(response, reply_markup=reply_markup)
        db.close()

    def generate_response(self, message: str) -> str:
        """Generate response based on user message (simple keyword matching for MVP)"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['hola', 'buenas', 'hey', 'saludos']):
            return "¡Hola! ¿En qué puedo ayudarte hoy? Puedes ver nuestro menú o hacer un pedido."
        
        elif any(word in message_lower for word in ['menu', 'menú', 'comida', 'productos']):
            return "¡Perfecto! Te muestro nuestro menú. Usa el botón de abajo para verlo."
        
        elif any(word in message_lower for word in ['precio', 'costo', 'cuanto', 'vale']):
            return "Los precios varían según el producto. Te invito a revisar nuestro menú completo."
        
        elif any(word in message_lower for word in ['entrega', 'domicilio', 'envio']):
            return "¡Claro! Realizamos entregas en toda la ciudad. El tiempo estimado es de 30-45 minutos."
        
        elif any(word in message_lower for word in ['horario', 'hora', 'abierto']):
            return "Estamos abiertos de Lunes a Domingo de 10:00 AM a 10:00 PM."
        
        else:
            return "Entiendo tu consulta. ¿Te gustaría ver nuestro menú o necesitas ayuda con algo específico?"

    def get_or_create_conversation(self, db: Session, chat_id: str, customer_name: str) -> Conversation:
        """Get existing conversation or create new one"""
        conversation = db.query(Conversation).filter(
            Conversation.chat_id == chat_id,
            Conversation.status == ConversationStatus.ACTIVE
        ).first()
        
        if not conversation:
            # Get default restaurant
            restaurant = db.query(Restaurant).first()
            if not restaurant:
                # Create default restaurant for MVP
                restaurant = Restaurant(
                    name="Restaurante Demo",
                    description="Restaurante de demostración",
                    phone="+57 123 456 7890",
                    active=True
                )
                db.add(restaurant)
                db.flush()
            
            conversation = Conversation(
                restaurant_id=restaurant.id,
                customer_phone=chat_id,
                customer_name=customer_name,
                platform="telegram",
                chat_id=chat_id,
                status=ConversationStatus.ACTIVE
            )
            db.add(conversation)
            db.commit()
        
        return conversation

    def save_message(self, db: Session, conversation_id: int, content: str, is_from_customer: bool):
        """Save message to database"""
        message = Message(
            conversation_id=conversation_id,
            content=content,
            is_from_customer=is_from_customer
        )
        db.add(message)
        db.commit()

    def run(self):
        """Start the bot"""
        logger.info("Starting Telegram bot...")
        self.application.run_polling()


# Initialize bot instance
telegram_bot = TelegramBot()