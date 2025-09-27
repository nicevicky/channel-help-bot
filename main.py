import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, PreCheckoutQueryHandler, filters
from config import BOT_TOKEN, MAIN_ADMIN_ID
from database import db
from handlers.user import user_handler
from handlers.admin import admin_handler
from handlers.payment import payment_handler
from utils.keyboards import main_menu_keyboard, admin_menu_keyboard

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def help_command(update, context):
    """Help command"""
    help_text = """
🤖 **Channel Post Helper Bot**

**Commands:**
/start - Start the bot
/addchannel <@channel> - Add channel to your list
/help - Show this help message

**Features:**
📝 Create formatted posts with links
🖼️ Support for photos, videos, documents
🔘 Add custom inline buttons
📢 Manage multiple channels
⭐ Premium features available

**How to use:**
1. Add this bot as admin to your channel
2. Use /addchannel @yourchannel to register it
3. Use "Create Post" to start posting

**Premium Benefits:**
• Remove ads from your posts
• Priority support
• Advanced features

Need help? Contact: @YourSupportUsername
    """
    
    keyboard = main_menu_keyboard()
    if update.effective_user.id == MAIN_ADMIN_ID:
        keyboard = admin_menu_keyboard()
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            help_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            help_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )

async def main_menu(update, context):
    """Return to main menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    keyboard = admin_menu_keyboard() if user_id == MAIN_ADMIN_ID else main_menu_keyboard()
    
    await query.edit_message_text(
        "🏠 **Main Menu**\n\nChoose an option:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def handle_text_messages(update, context):
    """Handle text messages for various steps"""
    user_id = update.effective_user.id
    
    # Check if user is in post creation process
    if hasattr(user_handler, 'user_data') and user_id in user_handler.user_data:
        await user_handler.handle_content(update, context)
        return
    
    # Check if user is in button text/url input
    if hasattr(user_handler, 'user_data') and user_id in user_handler.user_data:
        step = user_handler.user_data[user_id].get("step")
        if step == "waiting_button_text":
            await user_handler.handle_button_text(update, context)
            return
        elif step == "waiting_button_url":
            await user_handler.handle_button_url(update, context)
            return
    
    # Check if admin is creating ad
    if hasattr(admin_handler, 'admin_data') and user_id in admin_handler.admin_data:
        await admin_handler.handle_ad_creation(update, context)
        return
    
    # Default response
    await update.message.reply_text(
        "👋 Hi! Use the menu buttons to interact with the bot.",
        reply_markup=main_menu_keyboard() if user_id != MAIN_ADMIN_ID else admin_menu_keyboard()
    )

async def handle_media_messages(update, context):
    """Handle photo/video/document messages"""
    user_id = update.effective_user.id
    
    # Check if user is in post creation process
    if hasattr(user_handler, 'user_data') and user_id in user_handler.user_data:
        await user_handler.handle_content(update, context)
        return
    
    # Check if admin is creating ad
    if hasattr(admin_handler, 'admin_data') and user_id in admin_handler.admin_data:
        await admin_handler.handle_ad_creation(update, context)
        return

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", user_handler.start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("addchannel", user_handler.add_channel))
    application.add_handler(CommandHandler("upgrade", admin_handler.manual_upgrade))
    
    # Callback query handlers
    application.add_handler(CallbackQueryHandler(main_menu, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(help_command, pattern="^help$"))
    
    # User handlers
    application.add_handler(CallbackQueryHandler(user_handler.create_post_start, pattern="^create_post$"))
    application.add_handler(CallbackQueryHandler(user_handler.select_post_type, pattern="^post_"))
    application.add_handler(CallbackQueryHandler(user_handler.handle_button_choice, pattern="^(add_button|skip_button)$"))
    application.add_handler(CallbackQueryHandler(user_handler.handle_channel_selection, pattern="^select_channel_"))
    application.add_handler(CallbackQueryHandler(user_handler.confirm_send_post, pattern="^confirm_send$"))
    application.add_handler(CallbackQueryHandler(user_handler.cancel_post, pattern="^cancel_post$"))
    application.add_handler(CallbackQueryHandler(user_handler.my_channels, pattern="^my_channels$"))
    
    # Payment handlers
    application.add_handler(CallbackQueryHandler(payment_handler.upgrade_menu, pattern="^upgrade_menu$"))
    application.add_handler(CallbackQueryHandler(payment_handler.pay_with_stars, pattern="^pay_stars$"))
    application.add_handler(CallbackQueryHandler(payment_handler.pay_with_crypto, pattern="^pay_(btc|eth)$"))
    application.add_handler(CallbackQueryHandler(payment_handler.pay_with_bank, pattern="^pay_bank$"))
    application.add_handler(CallbackQueryHandler(payment_handler.payment_sent, pattern="^payment_sent$"))
    
    # Admin handlers
    application.add_handler(CallbackQueryHandler(admin_handler.manage_ads, pattern="^manage_ads$"))
    application.add_handler(CallbackQueryHandler(admin_handler.create_ad_start, pattern="^create_ad$"))
    application.add_handler(CallbackQueryHandler(admin_handler.handle_ad_media_choice, pattern="^ad_(add_photo|skip_media)$"))
    application.add_handler(CallbackQueryHandler(admin_handler.handle_ad_button_choice, pattern="^ad_(add_button|skip_button)$"))
    application.add_handler(CallbackQueryHandler(admin_handler.view_current_ad, pattern="^view_current_ad$"))
    application.add_handler(CallbackQueryHandler(admin_handler.delete_current_ad, pattern="^delete_current_ad$"))
    application.add_handler(CallbackQueryHandler(admin_handler.user_stats, pattern="^user_stats$"))
    
    # Payment processing
    application.add_handler(PreCheckoutQueryHandler(payment_handler.handle_successful_payment))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, payment_handler.handle_successful_stars_payment))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, handle_media_messages))
    
    # Initialize database
    import asyncio
    asyncio.run(db.init_tables())
    
    # Start the bot
    logger.info("Bot started successfully!")
    application.run_polling(allowed_updates=["message", "callback_query", "pre_checkout_query"])

if __name__ == '__main__':
    main()
    # Check if user is in post creation process
    if hasattr(user_handler, 'user_data') and user_id in user_handler.user_data:
        await user_handler.handle_content(update, context)
        return
    
    # Check if admin is creating ad
    if hasattr(admin_handler, 'admin_data') and user_id in admin_handler.admin_data:
        await admin_handler.handle_ad_creation(update, context)
        return

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", user_handler.start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("addchannel", user_handler.add_channel))
    application.add_handler(CommandHandler("upgrade", admin_handler.manual_upgrade))
    
    # Callback query handlers
    application.add_handler(CallbackQueryHandler(main_menu, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(help_command, pattern="^help$"))
    
    # User handlers
    application.add_handler(CallbackQueryHandler(user_handler.create_post_start, pattern="^create_post$"))
    application.add_handler(CallbackQueryHandler(user_handler.select_post_type, pattern="^post_"))
    application.add_handler(CallbackQueryHandler(user_handler.handle_button_choice, pattern="^(add_button|skip_button)$"))
    application.add_handler(CallbackQueryHandler(user_handler.handle_channel_selection, pattern="^select_channel_"))
    application.add_handler(CallbackQueryHandler(user_handler.confirm_send_post, pattern="^confirm_send$"))
    application.add_handler(CallbackQueryHandler(user_handler.cancel_post, pattern="^cancel_post$"))
    application.add_handler(CallbackQueryHandler(user_handler.my_channels, pattern="^my_channels$"))
    
    # Payment handlers
    application.add_handler(CallbackQueryHandler(payment_handler.upgrade_menu, pattern="^upgrade_menu$"))
    application.add_handler(CallbackQueryHandler(payment_handler.pay_with_stars, pattern="^pay_stars$"))
    application.add_handler(CallbackQueryHandler(payment_handler.pay_with_crypto, pattern="^pay_(btc|eth)$"))
    application.add_handler(CallbackQueryHandler(payment_handler.pay_with_bank, pattern="^pay_bank$"))
    application.add_handler(CallbackQueryHandler(payment_handler.payment_sent, pattern="^payment_sent$"))
    
    # Admin handlers
    application.add_handler(CallbackQueryHandler(admin_handler.manage_ads, pattern="^manage_ads$"))
    application.add_handler(CallbackQueryHandler(admin_handler.create_ad_start, pattern="^create_ad$"))
    application.add_handler(CallbackQueryHandler(admin_handler.handle_ad_media_choice, pattern="^ad_(add_photo|skip_media)$"))
    application.add_handler(CallbackQueryHandler(admin_handler.handle_ad_button_choice, pattern="^ad_(add_button|skip_button)$"))
    application.add_handler(CallbackQueryHandler(admin_handler.view_current_ad, pattern="^view_current_ad$"))
    application.add_handler(CallbackQueryHandler(admin_handler.delete_current_ad, pattern="^delete_current_ad$"))
    application.add_handler(CallbackQueryHandler(admin_handler.user_stats, pattern="^user_stats$"))
    
    # Payment processing
    application.add_handler(PreCheckoutQueryHandler(payment_handler.handle_successful_payment))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, payment_handler.handle_successful_stars_payment))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.DOCUMENT, handle_media_messages))
    
    # Initialize database
    import asyncio
    asyncio.run(db.init_tables())
    
    # Start the bot
    logger.info("Bot started successfully!")
    application.run_polling(allowed_updates=["message", "callback_query", "pre_checkout_query"])

if __name__ == '__main__':
    main()
