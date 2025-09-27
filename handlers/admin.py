from telegram import Update
from telegram.ext import ContextTypes
from database import db
from utils.keyboards import *
from config import MAIN_ADMIN_ID
import logging

class AdminHandler:
    def __init__(self):
        self.admin_data = {}
    
    async def is_main_admin(self, user_id: int) -> bool:
        """Check if user is main admin"""
        return user_id == MAIN_ADMIN_ID
    
    async def manage_ads(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manage advertisements"""
        query = update.callback_query
        await query.answer()
        
        if not await self.is_main_admin(query.from_user.id):
            await query.edit_message_text("❌ Access denied.")
            return
        
        keyboard = [
            [InlineKeyboardButton("➕ Create New Ad", callback_data="create_ad")],
            [InlineKeyboardButton("📋 View Current Ad", callback_data="view_current_ad")],
            [InlineKeyboardButton("🗑️ Delete Current Ad", callback_data="delete_current_ad")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(
            "📢 **Advertisement Management**\n\n"
            "Manage ads that appear in non-premium user posts:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def create_ad_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start ad creation"""
        query = update.callback_query
        await query.answer()
        
        if not await self.is_main_admin(query.from_user.id):
            return
        
        user_id = query.from_user.id
        self.admin_data[user_id] = {"step": "waiting_ad_title"}
        
        await query.edit_message_text("📝 Send the advertisement title:")
    
    async def handle_ad_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle ad creation steps"""
        user_id = update.effective_user.id
        
        if not await self.is_main_admin(user_id) or user_id not in self.admin_data:
            return
        
        step = self.admin_data[user_id].get("step")
        
        if step == "waiting_ad_title":
            self.admin_data[user_id]["title"] = update.message.text
            self.admin_data[user_id]["step"] = "waiting_ad_description"
            await update.message.reply_text("📝 Send the advertisement description:")
            
        elif step == "waiting_ad_description":
            self.admin_data[user_id]["description"] = update.message.text
            self.admin_data[user_id]["step"] = "waiting_ad_media"
            
            keyboard = [
                [InlineKeyboardButton("📷 Add Photo", callback_data="ad_add_photo")],
                [InlineKeyboardButton("⏭️ Skip Media", callback_data="ad_skip_media")]
            ]
            
            await update.message.reply_text(
                "🖼️ Do you want to add media to the ad?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        elif step == "waiting_ad_photo":
            if update.message.photo:
                self.admin_data[user_id]["media_url"] = update.message.photo[-1].file_id
                await self.ask_for_button(update)
            else:
                await update.message.reply_text("❌ Please send a photo or skip this step.")
                
        elif step == "waiting_button_text":
            self.admin_data[user_id]["button_text"] = update.message.text
            self.admin_data[user_id]["step"] = "waiting_button_url"
            await update.message.reply_text("🔗 Send the button URL:")
            
        elif step == "waiting_button_url":
            url = update.message.text
            if not url.startswith(('http://', 'https://')):
                await update.message.reply_text("❌ Please provide a valid URL starting with http:// or https://")
                return
            
            self.admin_data[user_id]["button_url"] = url
            await self.create_ad_final(update, user_id)
    
    async def ask_for_button(self, update: Update):
        """Ask for button addition"""
        user_id = update.effective_user.id
        self.admin_data[user_id]["step"] = "waiting_button_choice"
        
        keyboard = [
            [InlineKeyboardButton("➕ Add Button", callback_data="ad_add_button")],
            [InlineKeyboardButton("⏭️ Skip Button", callback_data="ad_skip_button")]
        ]
        
        await update.message.reply_text(
            "🔘 Do you want to add a button to the ad?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def handle_ad_media_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle ad media choice"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if query.data == "ad_add_photo":
            self.admin_data[user_id]["step"] = "waiting_ad_photo"
            await query.edit_message_text("📷 Send a photo for the advertisement:")
        elif query.data == "ad_skip_media":
            await self.ask_for_button_callback(query)
    
    async def ask_for_button_callback(self, query):
        """Ask for button via callback"""
        user_id = query.from_user.id
        self.admin_data[user_id]["step"] = "waiting_button_choice"
        
        keyboard = [
            [InlineKeyboardButton("➕ Add Button", callback_data="ad_add_button")],
            [InlineKeyboardButton("⏭️ Skip Button", callback_data="ad_skip_button")]
        ]
        
        await query.edit_message_text(
            "🔘 Do you want to add a button to the ad?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def handle_ad_button_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle ad button choice"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if query.data == "ad_add_button":
            self.admin_data[user_id]["step"] = "waiting_button_text"
            await query.edit_message_text("📝 Send the button text:")
        elif query.data == "ad_skip_button":
            await self.create_ad_final_callback(query, user_id)
    
    async def create_ad_final(self, update: Update, user_id: int):
        """Finalize ad creation"""
        ad_data = self.admin_data[user_id]
        
        # Deactivate current ads
        try:
            await db.supabase.table('ads').update({'is_active': False}).eq('is_active', True).execute()
        except:
            pass
        
        # Create new ad
        result = await db.add_ad(
            title=ad_data["title"],
            description=ad_data["description"],
            media_url=ad_data.get("media_url"),
            button_text=ad_data.get("button_text"),
            button_url=ad_data.get("button_url")
        )
        
        if result:
            await update.message.reply_text(
                "✅ Advertisement created successfully!\n\n"
                "The ad will now appear in all non-premium user posts.",
                reply_markup=admin_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ Error creating advertisement. Please try again.",
                reply_markup=admin_menu_keyboard()
            )
        
        # Clean up
        del self.admin_data[user_id]
    
    async def create_ad_final_callback(self, query, user_id: int):
        """Finalize ad creation via callback"""
        ad_data = self.admin_data[user_id]
        
        # Deactivate current ads
        try:
            await db.supabase.table('ads').update({'is_active': False}).eq('is_active', True).execute()
        except:
            pass
        
        # Create new ad
        result = await db.add_ad(
            title=ad_data["title"],
            description=ad_data["description"],
            media_url=ad_data.get("media_url"),
            button_text=ad_data.get("button_text"),
            button_url=ad_data.get("button_url")
        )
        
        if result:
            await query.edit_message_text(
                "✅ Advertisement created successfully!\n\n"
                "The ad will now appear in all non-premium user posts.",
                reply_markup=admin_menu_keyboard()
            )
        else:
            await query.edit_message_text(
                "❌ Error creating advertisement. Please try again.",
                reply_markup=admin_menu_keyboard()
            )
        
        # Clean up
        del self.admin_data[user_id]
    
    async def view_current_ad(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View current active ad"""
        query = update.callback_query
        await query.answer()
        
        if not await self.is_main_admin(query.from_user.id):
            return
        
        ad = await db.get_active_ad()
        
        if not ad:
            await query.edit_message_text(
                "📢 No active advertisement found.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="manage_ads")]])
            )
            return
        
        text = f"📢 **Current Advertisement:**\n\n"
        text += f"**Title:** {ad['title']}\n"
        text += f"**Description:** {ad['description']}\n"
        
        if ad.get('button_text'):
            text += f"**Button:** {ad['button_text']}\n"
            text += f"**URL:** {ad['button_url']}\n"
        
        text += f"\n**Created:** {ad['created_at'][:10]}"
        
        keyboard = [
            [InlineKeyboardButton("🗑️ Delete Ad", callback_data="delete_current_ad")],
            [InlineKeyboardButton("🔙 Back", callback_data="manage_ads")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def delete_current_ad(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete current active ad"""
        query = update.callback_query
        await query.answer()
        
        if not await self.is_main_admin(query.from_user.id):
            return
        
        try:
            await db.supabase.table('ads').update({'is_active': False}).eq('is_active', True).execute()
            
            await query.edit_message_text(
                "✅ Advertisement deleted successfully!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="manage_ads")]])
            )
        except Exception as e:
            logging.error(f"Error deleting ad: {e}")
            await query.edit_message_text(
                "❌ Error deleting advertisement.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="manage_ads")]])
            )
    
    async def user_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user statistics"""
        query = update.callback_query
        await query.answer()
        
        if not await self.is_main_admin(query.from_user.id):
            return
        
        try:
            # Get user statistics
            total_users = await db.supabase.table('users').select('*', count='exact').execute()
            premium_users = await db.supabase.table('users').select('*', count='exact').eq('is_premium', True).execute()
            total_channels = await db.supabase.table('channels').select('*', count='exact').execute()
            
            total_count = total_users.count if hasattr(total_users, 'count') else len(total_users.data)
            premium_count = premium_users.count if hasattr(premium_users, 'count') else len(premium_users.data)
            channel_count = total_channels.count if hasattr(total_channels, 'count') else len(total_channels.data)
            
            text = f"""
📊 **Bot Statistics**

👥 **Users:**
• Total Users: {total_count}
• Premium Users: {premium_count}
• Free Users: {total_count - premium_count}

📢 **Channels:**
• Total Channels: {channel_count}

💰 **Revenue:**
• Premium Conversion: {(premium_count/total_count*100):.1f}% if total_count > 0 else 0
            """
            
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logging.error(f"Error getting stats: {e}")
            await query.edit_message_text(
                "❌ Error retrieving statistics.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
            )
    
    async def manual_upgrade(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manually upgrade user (admin command)"""
        if not await self.is_main_admin(update.effective_user.id):
            await update.message.reply_text("❌ Access denied.")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /upgrade <user_id>")
            return
        
        try:
            user_id = int(context.args[0])
            result = await db.upgrade_user(user_id)
            
            if result:
                await update.message.reply_text(f"✅ User {user_id} upgraded to Premium successfully!")
                
                # Notify user
                try:
                    await context.bot.send_message(
                        user_id,
                        "🎉 **Congratulations!**\n\n"
                        "Your account has been upgraded to Premium!\n\n"
                        "Premium features are now active:\n"
                        "• No ads in your posts\n"
                        "• Priority support\n"
                        "• Advanced formatting options\n\n"
                        "Thank you for your support! 💫",
                        parse_mode='Markdown'
                    )
                except:
                    pass
            else:
                await update.message.reply_text(f"❌ Error upgrading user {user_id}")
                
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID")
        except Exception as e:
            logging.error(f"Error in manual upgrade: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")

admin_handler = AdminHandler()
