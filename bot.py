import logging
import re
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from config import Config

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# URL shortening functions
def shorten_tinyurl(long_url, custom_alias=None):
    """Shorten URL using TinyURL API"""
    try:
        base_url = "https://tinyurl.com/api-create.php"
        params = {"url": long_url}
        
        if custom_alias:
            params["alias"] = custom_alias
        
        response = requests.get(base_url, params=params, timeout=10)
        
        if response.status_code == 200:
            return response.text.strip()
        return None
    except Exception as e:
        logger.error(f"TinyURL error: {e}")
        return None

def shorten_isgd(long_url, custom_alias=None):
    """Shorten URL using is.gd API"""
    try:
        base_url = "https://is.gd/create.php"
        params = {
            "format": "simple",
            "url": long_url
        }
        
        if custom_alias:
            params["shorturl"] = custom_alias
        
        response = requests.get(base_url, params=params, timeout=10)
        
        if response.status_code == 200:
            return response.text.strip()
        return None
    except Exception as e:
        logger.error(f"is.gd error: {e}")
        return None

def shorten_vgd(long_url, custom_alias=None):
    """Shorten URL using v.gd API"""
    try:
        base_url = "https://v.gd/create.php"
        params = {
            "format": "simple",
            "url": long_url
        }
        
        if custom_alias:
            params["shorturl"] = custom_alias
        
        response = requests.get(base_url, params=params, timeout=10)
        
        if response.status_code == 200:
            return response.text.strip()
        return None
    except Exception as e:
        logger.error(f"v.gd error: {e}")
        return None

def is_valid_url(url):
    """Validate if URL is properly formatted"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🔗 Shorten URL", callback_data='shorten'),
            InlineKeyboardButton("📊 History", callback_data='history')
        ],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data='settings'),
            InlineKeyboardButton("❓ Help", callback_data='help')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "🔗 *Welcome to CompressLink Bot!*\n\n"
        "I can shorten long URLs quickly and easily.\n\n"
        "*Features:*\n"
        "✅ Shorten URLs with TinyURL, is.gd, or v.gd\n"
        "✅ Custom aliases available\n"
        "✅ View your shortened links history\n"
        "✅ Free and unlimited usage\n\n"
        "Just send me a URL or use the button below!"
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Handle URL shortening
async def shorten_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /shorten command or button click"""
    query = update.callback_query if update.callback_query else None
    
    if query:
        await query.answer()
    
    # Show service selection
    keyboard = [
        [
            InlineKeyboardButton("🔗 TinyURL", callback_data='service_tinyurl'),
            InlineKeyboardButton("🔗 is.gd", callback_data='service_isgd')
        ],
        [
            InlineKeyboardButton("🔗 v.gd", callback_data='service_vgd'),
            InlineKeyboardButton("🔄 Auto", callback_data='service_auto')
        ],
        [
            InlineKeyboardButton("🎯 Custom Alias", callback_data='custom_alias')
        ],
        [
            InlineKeyboardButton("🔙 Back to Menu", callback_data='main_menu')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🔗 *URL Shortener*\n\n"
        "Choose a service to shorten your URL:\n\n"
        "*TinyURL* - Most popular, reliable\n"
        "*is.gd* - Fast, simple, clean\n"
        "*v.gd* - Alternative option\n"
        "*Auto* - Let me choose the best\n"
        "*Custom Alias* - Create your own short link\n\n"
        "Or simply paste a URL in the chat!"
    )
    
    if query:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# Handle message with URL
async def handle_url_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages containing URLs"""
    message_text = update.message.text
    
    # Check if message contains a URL
    url_pattern = re.compile(r'https?://[^\s]+')
    urls = url_pattern.findall(message_text)
    
    if not urls:
        await update.message.reply_text(
            "❌ No valid URL found in your message.\n"
            "Please send a URL like: `https://example.com`",
            parse_mode='Markdown'
        )
        return
    
    # Get user's preferred service from context
    service = context.user_data.get('preferred_service', 'auto')
    custom_alias = context.user_data.get('custom_alias')
    
    # Store original message for history
    if 'url_history' not in context.user_data:
        context.user_data['url_history'] = []
    
    # Shorten each URL
    shortened_urls = []
    for url in urls:
        if not is_valid_url(url):
            await update.message.reply_text(f"❌ Invalid URL: {url}")
            continue
        
        # Choose service
        if service == 'tinyurl':
            short_url = shorten_tinyurl(url, custom_alias)
        elif service == 'isgd':
            short_url = shorten_isgd(url, custom_alias)
        elif service == 'vgd':
            short_url = shorten_vgd(url, custom_alias)
        else:  # auto - try in order
            short_url = shorten_tinyurl(url, custom_alias)
            if not short_url:
                short_url = shorten_isgd(url, custom_alias)
            if not short_url:
                short_url = shorten_vgd(url, custom_alias)
        
        if short_url:
            shortened_urls.append((url, short_url))
            
            # Save to history
            context.user_data['url_history'].append({
                'original': url,
                'shortened': short_url,
                'service': service if service != 'auto' else 'auto',
                'alias': custom_alias
            })
            # Keep only last 50 entries
            if len(context.user_data['url_history']) > 50:
                context.user_data['url_history'] = context.user_data['url_history'][-50:]
        else:
            await update.message.reply_text(f"❌ Failed to shorten: {url}\nPlease try again.")
    
    # Clear custom alias after use
    context.user_data['custom_alias'] = None
    
    # Send results
    if shortened_urls:
        keyboard = [
            [InlineKeyboardButton("📋 Copy All", callback_data=f'copy_{shortened_urls[0][1]}')],
            [InlineKeyboardButton("🔄 Shorten Another", callback_data='shorten')],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        result_text = "*✅ URL Shortened!*\n\n"
        for original, shortened in shortened_urls:
            result_text += f"*Original:*\n`{original}`\n\n"
            result_text += f"*Short URL:*\n`{shortened}`\n\n"
        
        if len(shortened_urls) == 1:
            result_text += "Click the short URL above to test it."
        else:
            result_text += "All URLs have been shortened."
        
        await update.message.reply_text(
            result_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ No URLs could be shortened.\n"
            "Please check your URLs and try again."
        )

# Handle custom alias input
async def handle_custom_alias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom alias input from user"""
    if not context.user_data.get('waiting_for_alias'):
        return
    
    alias = update.message.text.strip()
    
    # Validate alias (alphanumeric only, 4-20 chars)
    if not re.match(r'^[a-zA-Z0-9]{4,20}$', alias):
        await update.message.reply_text(
            "❌ Invalid alias!\n\n"
            "Requirements:\n"
            "• 4-20 characters\n"
            "• Only letters and numbers\n"
            "• No spaces or special characters\n\n"
            "Please try again or type /cancel to cancel."
        )
        return
    
    context.user_data['custom_alias'] = alias
    context.user_data['waiting_for_alias'] = False
    
    await update.message.reply_text(
        f"✅ Custom alias set: `{alias}`\n\n"
        "Now send me a URL to shorten with this alias!",
        parse_mode='Markdown'
    )

# Service selection handler
async def service_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == 'custom_alias':
        context.user_data['waiting_for_alias'] = True
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data='shorten')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🎯 *Custom Alias*\n\n"
            "Enter your custom alias (short name for your URL):\n\n"
            "Requirements:\n"
            "• 4-20 characters\n"
            "• Only letters and numbers\n"
            "• No spaces or special characters\n\n"
            "Example: `myLink123`\n\n"
            "Type your alias below:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    # Set service preference
    service = data.split('_')[1]
    context.user_data['preferred_service'] = service
    
    service_names = {
        'tinyurl': 'TinyURL',
        'isgd': 'is.gd',
        'vgd': 'v.gd',
        'auto': 'Auto (smart selection)'
    }
    
    await query.edit_message_text(
        f"✅ Service set to: *{service_names.get(service, service)}*\n\n"
        f"Now send me a URL to shorten!\n\n"
        f"*Tip:* You can also use /shorten anytime.",
        parse_mode='Markdown'
    )
    
    # Show the shorten menu again
    await shorten_url(update, context)

# History handler
async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    history = context.user_data.get('url_history', [])
    
    if not history:
        keyboard = [[InlineKeyboardButton("🔗 Shorten a URL", callback_data='shorten')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📊 *History*\n\n"
            "You haven't shortened any URLs yet.\n"
            "Start by shortening your first URL!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    # Show last 10 entries
    history_text = "*📊 Your Shortened URLs*\n\n"
    for i, entry in enumerate(reversed(history[-10:]), 1):
        history_text += f"{i}. `{entry['shortened']}`\n"
        history_text += f"   ↳ {entry['original'][:50]}...\n\n"
    
    keyboard = [
        [InlineKeyboardButton("🗑️ Clear History", callback_data='clear_history')],
        [InlineKeyboardButton("🔗 Shorten New URL", callback_data='shorten')],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        history_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Clear history handler
async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data['url_history'] = []
    
    await query.edit_message_text(
        "🗑️ *History Cleared!*\n\n"
        "All your shortened URLs have been removed.",
        parse_mode='Markdown'
    )

# Settings handler
async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    current_service = context.user_data.get('preferred_service', 'auto')
    service_names = {
        'tinyurl': 'TinyURL',
        'isgd': 'is.gd',
        'vgd': 'v.gd',
        'auto': 'Auto'
    }
    
    keyboard = [
        [
            InlineKeyboardButton("🔗 Default Service", callback_data='shorten'),
            InlineKeyboardButton("📊 History", callback_data='history')
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data='help'),
            InlineKeyboardButton("🔙 Back to Menu", callback_data='main_menu')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    settings_text = (
        "⚙️ *Settings*\n\n"
        f"*Default Service:* {service_names.get(current_service, 'Auto')}\n"
        f"*Links Shortened:* {len(context.user_data.get('url_history', []))}\n\n"
        "You can change these settings anytime."
    )
    
    await query.edit_message_text(
        settings_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Help handler
async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    
    help_text = (
        "❓ *Help & Commands*\n\n"
        "*How to use:*\n"
        "1. Send any URL to shorten it\n"
        "2. Or use /shorten to choose options\n\n"
        "*Commands:*\n"
        "/start - Show main menu\n"
        "/shorten - Open URL shortener\n"
        "/history - View your shortened URLs\n"
        "/help - Show this help message\n"
        "/cancel - Cancel current operation\n\n"
        "*Features:*\n"
        "✅ Multiple shortening services\n"
        "✅ Custom aliases\n"
        "✅ URL history\n"
        "✅ Smart auto-selection\n\n"
        "*Supported Services:*\n"
        "🔗 TinyURL\n"
        "🔗 is.gd\n"
        "🔗 v.gd\n\n"
        "All services are free and unlimited!"
    )
    
    if query:
        await query.edit_message_text(help_text, parse_mode='Markdown')
    else:
        await update.message.reply_text(help_text, parse_mode='Markdown')

# Cancel handler
async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    context.user_data['waiting_for_alias'] = False
    context.user_data['custom_alias'] = None
    
    await update.message.reply_text(
        "❌ Operation cancelled.\n"
        "Type /start to go back to the main menu."
    )

# Copy handler
async def copy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    url = query.data.split('_', 1)[1]
    
    await query.message.reply_text(
        f"📋 *URL copied to clipboard!*\n\n"
        f"`{url}`\n\n"
        f"*Note:* Please select and copy the URL manually.",
        parse_mode='Markdown'
    )

# Main menu handler
async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(update, context)

# Button handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == 'main_menu':
        await main_menu_handler(update, context)
    elif data == 'shorten':
        await shorten_url(update, context)
    elif data == 'history':
        await history_handler(update, context)
    elif data == 'settings':
        await settings_handler(update, context)
    elif data == 'help':
        await help_handler(update, context)
    elif data.startswith('service_'):
        await service_handler(update, context)
    elif data == 'clear_history':
        await clear_history(update, context)
    elif data == 'custom_alias':
        await service_handler(update, context)
    elif data.startswith('copy_'):
        await copy_handler(update, context)

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Start the bot"""
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("shorten", shorten_url))
    application.add_handler(CommandHandler("history", history_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("cancel", cancel_handler))
    
    # Callback query handler
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Message handlers
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_url_message
    ))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    logger.info("🤖 URL Shortener Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
