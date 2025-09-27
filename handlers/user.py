from telegram import Update, Bot
from telegram.ext import ContextTypes
from database import db
from utils.keyboards import *
from utils.helpers import *
import logging

class UserHandler:
    def __init__(self):
        self.user_data = {}
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        user = update.effective_user
        await db.add_user(user.id, user.username)
        
        welcome_text = """
🤖 Welcome to Channel Post Helper Bot!

This bot helps you create and manage posts for your Telegram channels with advanced formatting options.

Features:
📝 Rich text formatting with links
🖼️ Photo, video, and document support
🔘 Custom inline buttons
📢 Multiple channel management
⭐ Premium features available

To get started, make sure to add this bot as an admin to your channels!
        """
        
        from config import MAIN_ADMIN_ID
        keyboard = admin_menu_keyboard() if user.id == MAIN_ADMIN_ID else main_menu_keyboard()
        
        await update.message.reply_text(welcome_text, reply_markup=keyboard)
    
    async def create_post_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start post creation process"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        channels = await db.get_user_channels(user_id)
        
        if not channels:
            await query.edit_message_text(
                "❌ You don't have any registered channels.\n\n"
                "Please add this bot as an admin to your channels first, then use /addchannel command.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
            )
            return
        
        await query.edit_message_text(
            "📝 Select post type:",
            reply_markup=post_type_keyboard()
        )
    
    async def select_post_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle post type selection"""
        query = update.callback_query
        await query.answer()
        
        post_type = query.data.replace("post_", "")
        user_id = query.from_user.id
        
        self.user_data[user_id] = {"post_type": post_type, "step": "waiting_content"}
        
        if post_type == "text":
            message = "📝 Send me your text message with formatting:\n\n" \
                     "You can use:\n" \
                     "• **bold text**\n" \
                     "• *italic text*\n" \
                     "• [link text](https://example.com)\n" \
                     "• `code text`\n\n" \
                     "Send your message:"
        elif post_type == "photo":
            message = "🖼️ Send me a photo with caption (optional):"
        elif post_type == "video":
            message = "🎥 Send me a video with caption (optional):"
        elif post_type == "document":
            message = "📄 Send me a document with caption (optional):"
        
        await query.edit_message_text(message)
    
    async def handle_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle content input"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_data or self.user_data[user_id].get("step") != "waiting_content":
            return
        
        post_data = self.user_data[user_id]
        
        if update.message.text and post_data["post_type"] == "text":
            post_data["text"] = update.message.text
            post_data["message_id"] = update.message.message_id
        elif update.message.photo and post_data["post_type"] == "photo":
            post_data["photo"] = update.message.photo[-1].file_id
            post_data["caption"] = update.message.caption or ""
            post_data["message_id"] = update.message.message_id
        elif update.message.video and post_data["post_type"] == "video":
            post_data["video"] = update.message.video.file_id
            post_data["caption"] = update.message.caption or ""
            post_data["message_id"] = update.message.message_id
        elif update.message.document and post_data["post_type"] == "document":
            post_data["document"] = update.message.document.file_id
            post_data["caption"] = update.message.caption or ""
            post_data["message_id"] = update.message.message_id
        else:
            await update.message.reply_text("❌ Please send the correct type of content.")
            return
        
        post_data["step"] = "waiting_button"
        
        keyboard = [
            [InlineKeyboardButton("➕ Add Button", callback_data="add_button")],
            [InlineKeyboardButton("⏭️ Skip Button", callback_data="skip_button")]
        ]
        
        await update.message.reply_text(
            "🔘 Do you want to add an inline button to your post?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def handle_button_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button addition choice"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if query.data == "add_button":
            self.user_data[user_id]["step"] = "waiting_button_text"
            await query.edit_message_text("📝 Send the button text:")
        elif query.data == "skip_button":
            await self.show_channel_selection(query, user_id)
    
    async def handle_button_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button text input"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_data or self.user_data[user_id].get("step") != "waiting_button_text":
            return
        
        self.user_data[user_id]["button_text"] = update.message.text
        self.user_data[user_id]["step"] = "waiting_button_url"
        
        await update.message.reply_text("🔗 Send the button URL:")
    
    async def handle_button_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button URL input"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_data or self.user_data[user_id].get("step") != "waiting_button_url":
            return
        
        url = update.message.text
        if not url.startswith(('http://', 'https://')):
            await update.message.reply_text("❌ Please provide a valid URL starting with http:// or https://")
            return
        
        self.user_data[user_id]["button_url"] = url
        await self.show_channel_selection_message(update, user_id)
    
    async def show_channel_selection_message(self, update: Update, user_id: int):
        """Show channel selection as new message"""
        channels = await db.get_user_channels(user_id)
        
        await update.message.reply_text(
            "📢 Select channel to post:",
            reply_markup=channel_selection_keyboard(channels)
        )
    
    async def show_channel_selection(self, query, user_id: int):
        """Show channel selection"""
        channels = await db.get_user_channels(user_id)
        
        await query.edit_message_text(
            "📢 Select channel to post:",
            reply_markup=channel_selection_keyboard(channels)
        )
    
    async def handle_channel_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle channel selection"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        channel_id = int(query.data.replace("select_channel_", ""))
        
        self.user_data[user_id]["channel_id"] = channel_id
        
        # Show preview
        await self.show_post_preview(query, user_id)
    
    async def show_post_preview(self, query, user_id: int):
        """Show post preview"""
        post_data = self.user_data[user_id]
        
        preview_text = "📋 **Post Preview:**\n\n"
        
        if post_data["post_type"] == "text":
            content = await format_post_with_ad(post_data["text"], user_id)
            preview_text += content
        else:
            caption = post_data.get("caption", "")
            content = await format_post_with_ad(caption, user_id)
            preview_text += f"[{post_data['post_type'].upper()}]\n{content}"
        
        # Add button info
        if post_data.get("button_text"):
            preview_text += f"\n\n🔘 Button: {post_data['button_text']}"
        
        await query.edit_message_text(
            preview_text,
            reply_markup=confirm_post_keyboard(),
            parse_mode='Markdown'
        )
    
    async def confirm_send_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm and send post"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        post_data = self.user_data.get(user_id)
        
        if not post_data:
            await query.edit_message_text("❌ Post data not found. Please start over.")
            return
        
        try:
            channel_id = post_data["channel_id"]
            bot = context.bot
            
            # Check if bot is still admin
            if not await check_bot_admin(bot, channel_id):
                await query.edit_message_text("❌ Bot is not admin in the selected channel.")
                return
            
            # Prepare content
            user = await db.get_user(user_id)
            is_premium = user.get('is_premium', False) if user else False
            
            # Get ad for non-premium users
            ad = await db.get_active_ad() if not is_premium else None
            
            # Create markup
            markup = None
            if post_data.get("button_text") or ad:
                ad_button = None
                if ad and ad.get('button_text') and ad.get('button_url'):
                    ad_button = {'text': ad['button_text'], 'url': ad['button_url']}
                
                markup = create_post_markup(
                    post_data.get("button_text"),
                    post_data.get("button_url"),
                    ad_button
                )
            
            # Send post based on type
            if post_data["post_type"] == "text":
                content = await format_post_with_ad(post_data["text"], user_id)
                await bot.send_message(
                    channel_id,
                    content,
                    reply_markup=markup,
                    parse_mode='Markdown'
                )
            elif post_data["post_type"] == "photo":
                caption = await format_post_with_ad(post_data.get("caption", ""), user_id)
                await bot.send_photo(
                    channel_id,
                    post_data["photo"],
                    caption=caption,
                    reply_markup=markup,
                    parse_mode='Markdown'
                )
            elif post_data["post_type"] == "video":
                caption = await format_post_with_ad(post_data.get("caption", ""), user_id)
                await bot.send_video(
                    channel_id,
                    post_data["video"],
                    caption=caption,
                    reply_markup=markup,
                    parse_mode='Markdown'
                )
            elif post_data["post_type"] == "document":
                caption = await format_post_with_ad(post_data.get("caption", ""), user_id)
                await bot.send_document(
                    channel_id,
                    post_data["document"],
                    caption=caption,
                    reply_markup=markup,
                    parse_mode='Markdown'
                )
            
            # Clean up user data
            del self.user_data[user_id]
            
            success_text = "✅ Post sent successfully!"
            if not is_premium and ad:
                success_text += "\n\n⭐ Upgrade to Premium to remove ads from your posts!"
            
            await query.edit_message_text(
                success_text,
                reply_markup=main_menu_keyboard()
            )
            
        except Exception as e:
            logging.error(f"Error sending post: {e}")
            await query.edit_message_text(
                f"❌ Error sending post: {str(e)}",
                reply_markup=main_menu_keyboard()
            )
    
    async def cancel_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel post creation"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        if user_id in self.user_data:
            del self.user_data[user_id]
        
        await query.edit_message_text(
            "❌ Post cancelled.",
            reply_markup=main_menu_keyboard()
        )
    
    async def add_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add channel command"""
        if not context.args:
            await update.message.reply_text(
                "Usage: /addchannel @channel_username or /addchannel -100xxxxxxxxx\n\n"
                "Make sure the bot is added as admin to the channel first!"
            )
            return
        
        channel_identifier = context.args[0]
        user_id = update.effective_user.id
        bot = context.bot
        
        try:
            # Get channel info
            chat = await bot.get_chat(channel_identifier)
            
            if chat.type != 'channel':
                await update.message.reply_text("❌ This is not a channel!")
                return
            
            # Check if bot is admin
            if not await check_bot_admin(bot, chat.id):
                await update.message.reply_text("❌ Bot is not admin in this channel!")
                return
            
            # Check if user is admin
            if not await check_user_admin(bot, chat.id, user_id):
                await update.message.reply_text("❌ You are not admin in this channel!")
                return
            
            # Add channel to database
            await db.add_channel(chat.id, chat.title, user_id)
            
            await update.message.reply_text(
                f"✅ Channel '{chat.title}' added successfully!",
                reply_markup=main_menu_keyboard()
            )
            
        except Exception as e:
            logging.error(f"Error adding channel: {e}")
            await update.message.reply_text(f"❌ Error adding channel: {str(e)}")
    
    async def my_channels(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's channels"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        channels = await db.get_user_channels(user_id)
        
        if not channels:
            text = "📢 You don't have any registered channels.\n\n" \
                   "Use /addchannel command to add your channels."
        else:
            text = "📢 **Your Channels:**\n\n"
            for i, channel in enumerate(channels, 1):
                text += f"{i}. {channel['channel_name']}\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

user_handler = UserHandler()
