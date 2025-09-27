from telegram import Bot
from database import db
import logging

async def check_bot_admin(bot: Bot, channel_id: int):
    """Check if bot is admin in channel"""
    try:
        bot_member = await bot.get_chat_member(channel_id, bot.id)
        return bot_member.status in ['administrator', 'creator']
    except Exception as e:
        logging.error(f"Error checking bot admin status: {e}")
        return False

async def check_user_admin(bot: Bot, channel_id: int, user_id: int):
    """Check if user is admin in channel"""
    try:
        user_member = await bot.get_chat_member(channel_id, user_id)
        return user_member.status in ['administrator', 'creator']
    except Exception as e:
        logging.error(f"Error checking user admin status: {e}")
        return False

async def format_post_with_ad(text: str, user_id: int):
    """Add advertisement to user post if not premium"""
    user = await db.get_user(user_id)
    if user and user.get('is_premium', False):
        return text
    
    ad = await db.get_active_ad()
    if not ad:
        return text
    
    ad_text = f"\n\n━━━━━━━━━━━━━━━━\n📢 {ad['title']}\n{ad['description']}"
    return text + ad_text

def create_post_markup(button_text: str = None, button_url: str = None, ad_button: dict = None):
    """Create inline keyboard for post"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = []
    
    # Add user's button if provided
    if button_text and button_url:
        keyboard.append([InlineKeyboardButton(button_text, url=button_url)])
    
    # Add ad button if exists and user is not premium
    if ad_button:
        keyboard.append([InlineKeyboardButton(ad_button['text'], url=ad_button['url'])])
    
    return InlineKeyboardMarkup(keyboard) if keyboard else None
