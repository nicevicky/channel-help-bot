from telegram import Update, LabeledPrice
from telegram.ext import ContextTypes
from database import db
from utils.keyboards import *
from config import *
import logging

class PaymentHandler:
    
    async def upgrade_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show upgrade menu"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        user = await db.get_user(user_id)
        
        if user and user.get('is_premium', False):
            await query.edit_message_text(
                "⭐ You already have Premium access!\n\n"
                "Premium features:\n"
                "• No ads in your posts\n"
                "• Priority support\n"
                "• Advanced formatting options",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
            )
            return
        
        text = f"""
⭐ **Upgrade to Premium**

Premium Benefits:
• Remove ads from all your posts
• Priority customer support
• Advanced formatting options
• Future premium features

**Pricing:**
• Telegram Stars: {UPGRADE_PRICE_STARS} ⭐
• Other methods: ${UPGRADE_PRICE_USD}

Choose your payment method:
        """
        
        await query.edit_message_text(
            text,
            reply_markup=upgrade_keyboard(),
            parse_mode='Markdown'
        )
    
    async def pay_with_stars(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Stars payment"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Create invoice for Stars payment
            await context.bot.send_invoice(
                chat_id=query.from_user.id,
                title="Premium Upgrade",
                description="Upgrade to Premium to remove ads and get exclusive features",
                payload="premium_upgrade",
                provider_token="",  # Empty for Stars
                currency="XTR",  # Telegram Stars currency
                prices=[LabeledPrice("Premium Upgrade", UPGRADE_PRICE_STARS)]
            )
            
            await query.edit_message_text(
                "💫 Stars payment invoice sent! Please complete the payment.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="upgrade_menu")]])
            )
            
        except Exception as e:
            logging.error(f"Error creating Stars invoice: {e}")
            await query.edit_message_text(
                "❌ Error creating payment. Please try again later.",
                reply_markup=upgrade_keyboard()
            )
    
    async def pay_with_crypto(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle crypto payment"""
        query = update.callback_query
        await query.answer()
        
        crypto_type = query.data.replace("pay_", "").upper()
        
        if crypto_type == "BTC":
            wallet = CRYPTO_WALLET_BTC
            symbol = "₿"
        elif crypto_type == "ETH":
            wallet = CRYPTO_WALLET_ETH
            symbol = "Ξ"
        else:
            await query.edit_message_text("❌ Unsupported crypto type")
            return
        
        if not wallet:
            await query.edit_message_text(
                "❌ Crypto payments not available at the moment.",
                reply_markup=upgrade_keyboard()
            )
            return
        
                text = f"""
{symbol} **{crypto_type} Payment**

Amount: ${UPGRADE_PRICE_USD} worth of {crypto_type}
Wallet Address:
`{wallet}`

**Instructions:**
1. Send the equivalent of ${UPGRADE_PRICE_USD} in {crypto_type} to the above address
2. Send the transaction hash to @{context.bot.username} with your user ID: {query.from_user.id}
3. Your account will be upgraded within 24 hours after verification

⚠️ **Important:** Include your User ID in the message when sending transaction proof!
        """
        
        keyboard = [
            [InlineKeyboardButton("📋 Copy Wallet", callback_data=f"copy_wallet_{crypto_type.lower()}")],
            [InlineKeyboardButton("✅ Payment Sent", callback_data="payment_sent")],
            [InlineKeyboardButton("🔙 Back", callback_data="upgrade_menu")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def pay_with_bank(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle bank transfer payment"""
        query = update.callback_query
        await query.answer()
        
        if not BANK_DETAILS:
            await query.edit_message_text(
                "❌ Bank transfer not available at the moment.",
                reply_markup=upgrade_keyboard()
            )
            return
        
        text = f"""
🏦 **Bank Transfer Payment**

Amount: ${UPGRADE_PRICE_USD}

Bank Details:
{BANK_DETAILS}

**Instructions:**
1. Transfer ${UPGRADE_PRICE_USD} to the above bank account
2. Send the transfer receipt to @{context.bot.username}
3. Include your User ID: {query.from_user.id}
4. Your account will be upgraded within 24 hours after verification

⚠️ **Important:** Include your User ID when sending payment proof!
        """
        
        keyboard = [
            [InlineKeyboardButton("✅ Payment Sent", callback_data="payment_sent")],
            [InlineKeyboardButton("🔙 Back", callback_data="upgrade_menu")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def payment_sent(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle payment sent confirmation"""
        query = update.callback_query
        await query.answer()
        
        text = f"""
✅ **Payment Confirmation Received**

Your User ID: `{query.from_user.id}`

Thank you for your payment! Please send your payment proof (transaction hash or receipt) to the bot admin.

Your premium upgrade will be processed within 24 hours after verification.

You will receive a notification once your account is upgraded.
        """
        
        # Notify admin about pending payment
        try:
            await context.bot.send_message(
                MAIN_ADMIN_ID,
                f"💰 **New Payment Notification**\n\n"
                f"User: @{query.from_user.username or 'N/A'}\n"
                f"User ID: {query.from_user.id}\n"
                f"Name: {query.from_user.full_name}\n\n"
                f"User has indicated payment completion. Please verify and upgrade manually using:\n"
                f"/upgrade {query.from_user.id}",
                parse_mode='Markdown'
            )
        except Exception as e:
            logging.error(f"Error notifying admin: {e}")
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]),
            parse_mode='Markdown'
        )
    
    async def handle_successful_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle successful Stars payment"""
        user_id = update.pre_checkout_query.from_user.id
        
        # Answer pre-checkout query
        await update.pre_checkout_query.answer(ok=True)
    
    async def handle_successful_stars_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle successful Stars payment completion"""
        user_id = update.message.successful_payment.from_user.id
        
        # Upgrade user to premium
        await db.upgrade_user(user_id)
        
        await update.message.reply_text(
            "🎉 **Payment Successful!**\n\n"
            "Your account has been upgraded to Premium!\n\n"
            "Premium features are now active:\n"
            "• No ads in your posts\n"
            "• Priority support\n"
            "• Advanced formatting options\n\n"
            "Thank you for your support! 💫",
            reply_markup=main_menu_keyboard(),
            parse_mode='Markdown'
        )
        
        # Notify admin
        try:
            await context.bot.send_message(
                MAIN_ADMIN_ID,
                f"💫 **Stars Payment Completed**\n\n"
                f"User: @{update.message.from_user.username or 'N/A'}\n"
                f"User ID: {user_id}\n"
                f"Amount: {UPGRADE_PRICE_STARS} Stars\n"
                f"Status: Automatically upgraded to Premium",
                parse_mode='Markdown'
            )
        except Exception as e:
            logging.error(f"Error notifying admin about Stars payment: {e}")

payment_handler = PaymentHandler()
