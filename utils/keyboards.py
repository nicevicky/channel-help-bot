from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_keyboard():
    """Main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("📝 Create Post", callback_data="create_post")],
        [InlineKeyboardButton("📊 My Channels", callback_data="my_channels")],
        [InlineKeyboardButton("⭐ Upgrade Premium", callback_data="upgrade_menu")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_menu_keyboard():
    """Admin menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("📝 Create Post", callback_data="create_post")],
        [InlineKeyboardButton("📊 My Channels", callback_data="my_channels")],
        [InlineKeyboardButton("📢 Manage Ads", callback_data="manage_ads")],
        [InlineKeyboardButton("👥 User Stats", callback_data="user_stats")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def upgrade_keyboard():
    """Upgrade options keyboard"""
    keyboard = [
        [InlineKeyboardButton("⭐ Pay with Stars", callback_data="pay_stars")],
        [InlineKeyboardButton("💳 Bank Transfer", callback_data="pay_bank")],
        [InlineKeyboardButton("₿ Bitcoin", callback_data="pay_btc")],
        [InlineKeyboardButton("Ξ Ethereum", callback_data="pay_eth")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def post_type_keyboard():
    """Post type selection keyboard"""
    keyboard = [
        [InlineKeyboardButton("📝 Text Only", callback_data="post_text")],
        [InlineKeyboardButton("🖼️ Photo + Text", callback_data="post_photo")],
        [InlineKeyboardButton("🎥 Video + Text", callback_data="post_video")],
        [InlineKeyboardButton("📄 Document + Text", callback_data="post_document")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def channel_selection_keyboard(channels):
    """Channel selection keyboard"""
    keyboard = []
    for channel in channels:
        keyboard.append([InlineKeyboardButton(
            f"📢 {channel['channel_name']}", 
            callback_data=f"select_channel_{channel['channel_id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

def confirm_post_keyboard():
    """Confirm post keyboard"""
    keyboard = [
        [InlineKeyboardButton("✅ Send Post", callback_data="confirm_send")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_post")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)
