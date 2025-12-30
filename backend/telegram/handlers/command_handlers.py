"""
Telegram Bot Command Handlers

Handles all bot commands like /start, /help, /new, etc.
"""
import logging
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime

from backend.telegram.services.user_service import UserService
from backend.telegram.services.conversation_service import ConversationService
from backend.telegram.services.export_service import ExportService
from backend.telegram.keyboards import context_keyboards, settings_keyboards
from backend.db.database import SessionLocal

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command.

    Creates a new user account if needed and shows welcome message.
    Supports deep linking with start parameters (e.g., /start web_campaign).
    """
    user = update.effective_user
    start_param = context.args[0] if context.args else None

    logger.info(f"User {user.id} ({user.username}) started the bot with param: {start_param}")

    # Create or get user
    user_service = UserService(SessionLocal)
    try:
        user_record = await user_service.get_or_create_user(user)

        # Track conversion source if deep link
        if start_param:
            await user_service.track_conversion(user_record.user_id, source=start_param)

        # Welcome message
        welcome_text = f"""
⚽ **Welcome to Lucide, {user.first_name}!**

I'm your intelligent football analysis assistant. Ask me anything about:

🏆 Match predictions & analysis
📊 Team statistics & standings
👥 Player performance & transfers
📅 Upcoming fixtures & schedules
🎯 Head-to-head comparisons

**Quick Start:**
• Just ask me a question in plain language
• Use /context to set a league or match focus
• Use /help to see all available commands

**Example questions:**
• "Who will win PSG vs Barcelona?"
• "Show me Premier League standings"
• "How is Mbappé performing this season?"

Let's analyze some football! ⚽
"""

        await update.message.reply_text(
            welcome_text,
            parse_mode="Markdown",
        )

        # Show quick action buttons
        keyboard = [
            [
                InlineKeyboardButton("🎯 Set Context", callback_data="cmd_context"),
                InlineKeyboardButton("📚 View Help", callback_data="cmd_help"),
            ],
            [
                InlineKeyboardButton("🌐 Language", callback_data="cmd_language"),
                InlineKeyboardButton("⭐ Upgrade", callback_data="cmd_subscription"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "Choose an option or just start asking questions:",
            reply_markup=reply_markup,
        )

    except Exception as e:
        logger.error(f"Error in start_command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ An error occurred. Please try again or contact support."
        )
    finally:
        await user_service.close()


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command - Show all available commands and features."""
    help_text = """
📖 **Lucide Help Guide**

**Basic Commands:**
/start - Start the bot & create account
/new - Start a new conversation
/help - Show this help message
/cancel - Cancel current operation

**Context & Settings:**
/context - Set league/match/team context
/language - Switch language (FR/EN)
/settings - Manage preferences

**History & Export:**
/history - View past conversations
/export - Export your data (GDPR)

**Subscription:**
/subscription - View tier & upgrade

**How to Use:**

1️⃣ **Ask Questions Naturally**
Just type your question:
• "Who will win Real Madrid vs Barcelona?"
• "Show PSG statistics"
• "Mbappé goals this season"

2️⃣ **Set Context for Faster Responses**
Use /context to set a league or match focus:
• All questions will use that context
• No need to repeat league/team names

3️⃣ **View Analysis History**
Use /history to browse past conversations

**Features:**

🔍 Match Analysis (39+ patterns detected)
📊 Team & Player Statistics
🏆 League Standings & Fixtures
🎯 Predictions with Confidence Scores
📈 Historical Performance Trends
⚡ Real-time Updates

**Subscription Tiers:**

🆓 FREE: 50 messages/day
⭐ PREMIUM: Unlimited + priority

Use /subscription to upgrade

**Need Help?**
Contact support@lucide.ai
"""

    # Check if this is a callback query or a regular command
    if update.callback_query:
        await update.callback_query.edit_message_text(help_text, parse_mode="Markdown")
    else:
        await update.message.reply_text(help_text, parse_mode="Markdown")


async def new_conversation_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /new command - Start a new conversation."""
    user = update.effective_user

    user_service = UserService(SessionLocal)
    conversation_service = ConversationService(SessionLocal)

    try:
        user_record = await user_service.get_or_create_user(user)

        # Create new conversation
        conversation_id = str(uuid.uuid4())
        title = f"New conversation - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        await conversation_service.create_conversation(
            conversation_id=conversation_id,
            user_id=user_record.user_id,
            title=title,
        )

        # Store active conversation in user context
        context.user_data["active_conversation_id"] = conversation_id
        context.user_data["context"] = None  # Reset context

        await update.message.reply_text(
            "✅ **New conversation started!**\n\n"
            "Ask me anything about football. I'll remember our conversation context.\n\n"
            "Tip: Use /context to set a league or match focus for faster responses.",
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.error(f"Error in new_conversation_command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Failed to create new conversation. Please try again."
        )
    finally:
        await user_service.close()
        await conversation_service.close()


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /history command - Show conversation history."""
    user = update.effective_user

    user_service = UserService(SessionLocal)
    conversation_service = ConversationService(SessionLocal)

    try:
        user_record = await user_service.get_or_create_user(user)

        # Get user's conversations
        conversations = await conversation_service.get_user_conversations(
            user_id=user_record.user_id, limit=10
        )

        if not conversations:
            await update.message.reply_text(
                "📚 **No conversations yet**\n\n"
                "Start chatting with me to build your history!\n\n"
                "Ask me anything about football matches, teams, or players.",
                parse_mode="Markdown",
            )
            return

        # Build inline keyboard with conversations
        keyboard = []
        for conv in conversations:
            # Truncate title if too long
            display_title = conv.title[:45] + "..." if len(conv.title) > 45 else conv.title

            # Count messages (if available)
            msg_count = getattr(conv, "message_count", "?")

            keyboard.append([
                InlineKeyboardButton(
                    f"💬 {display_title} ({msg_count} msgs)",
                    callback_data=f"conv_open_{conv.conversation_id}",
                )
            ])

        # Add action buttons
        keyboard.append([
            InlineKeyboardButton("🗑️ Delete", callback_data="conv_delete_mode"),
            InlineKeyboardButton("🔄 Load More", callback_data="conv_load_more"),
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"📚 **Your Conversations** ({len(conversations)} recent)\n\n"
            "Select a conversation to continue or delete:",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.error(f"Error in history_command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Failed to load conversation history. Please try again."
        )
    finally:
        await user_service.close()
        await conversation_service.close()


async def context_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /context command - Show context selection menu."""
    try:
        # Get current context from user_data
        current_context = context.user_data.get("context", {})

        keyboard = context_keyboards.get_main_context_menu(current_context)
        message_text = (
            "🎯 **Set Context**\n\n"
            "Choose what you want to analyze:\n"
            "• League - Set a specific league/competition\n"
            "• Match - Focus on a specific match\n"
            "• Team - Analyze a specific team\n"
            "• Player - Track a specific player\n"
            "• Clear - Remove current context\n\n"
            "Setting context helps me give faster, more relevant answers!"
        )

        # Check if this is a callback query or a regular command
        if update.callback_query:
            await update.callback_query.edit_message_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )

    except Exception as e:
        logger.error(f"Error in context_command: {e}", exc_info=True)
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "❌ Failed to show context menu. Please try again."
            )
        else:
            await update.message.reply_text(
                "❌ Failed to show context menu. Please try again."
            )


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /language command - Switch language."""
    user = update.effective_user
    user_service = UserService(SessionLocal)

    try:
        user_record = await user_service.get_or_create_user(user)

        # Get current language
        current_lang = user_record.preferred_language or "fr"

        keyboard = [
            [
                InlineKeyboardButton(
                    f"{'✅ ' if current_lang == 'fr' else ''}Français",
                    callback_data="lang_fr",
                ),
                InlineKeyboardButton(
                    f"{'✅ ' if current_lang == 'en' else ''}English",
                    callback_data="lang_en",
                ),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        message_text = (
            "🌐 **Select Language / Choisir la langue**\n\n"
            f"Current: {'Français 🇫🇷' if current_lang == 'fr' else 'English 🇬🇧'}"
        )

        # Check if this is a callback query or a regular command
        if update.callback_query:
            await update.callback_query.edit_message_text(
                message_text,
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                message_text,
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )

    except Exception as e:
        logger.error(f"Error in language_command: {e}", exc_info=True)
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "❌ Failed to show language menu. Please try again."
            )
        else:
            await update.message.reply_text(
                "❌ Failed to show language menu. Please try again."
            )
    finally:
        await user_service.close()


async def subscription_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /subscription command - Show subscription info and upgrade options."""
    user = update.effective_user
    user_service = UserService(SessionLocal)

    try:
        user_record = await user_service.get_or_create_user(user)

        tier = user_record.subscription_tier or "FREE"
        tier_info = {
            "FREE": {"name": "Free", "emoji": "🆓", "limit": "50 msgs/day"},
            "BASIC": {"name": "Basic", "emoji": "💙", "limit": "500 msgs/day"},
            "PREMIUM": {"name": "Premium", "emoji": "⭐", "limit": "Unlimited"},
            "ENTERPRISE": {"name": "Enterprise", "emoji": "🏢", "limit": "Unlimited + API"},
        }

        current_tier = tier_info.get(tier, tier_info["FREE"])

        subscription_text = f"""
⭐ **Your Subscription**

Current Plan: {current_tier['emoji']} **{current_tier['name']}**
Message Limit: {current_tier['limit']}

{'**🎉 You have unlimited access!**' if tier in ['PREMIUM', 'ENTERPRISE'] else ''}

**Available Plans:**

🆓 **Free**
• 50 messages per day
• All analysis features
• Basic support

⭐ **Premium** - €9.99/month
• Unlimited messages
• Priority analysis (faster)
• Advanced statistics
• Priority support
• No ads

🏢 **Enterprise** - Custom pricing
• Everything in Premium
• API access
• Custom integrations
• Dedicated support
• SLA guarantees

{'**Want to upgrade?**' if tier == 'FREE' else '**Manage subscription:**'}
"""

        keyboard = []

        if tier == "FREE":
            keyboard.append([
                InlineKeyboardButton("⭐ Upgrade to Premium", callback_data="sub_premium"),
            ])
            keyboard.append([
                InlineKeyboardButton("🏢 Enterprise Inquiry", callback_data="sub_enterprise"),
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("📊 Usage Statistics", callback_data="sub_stats"),
            ])
            keyboard.append([
                InlineKeyboardButton("📧 Billing Info", callback_data="sub_billing"),
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Check if this is a callback query or a regular command
        if update.callback_query:
            await update.callback_query.edit_message_text(
                subscription_text,
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                subscription_text,
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )

    except Exception as e:
        logger.error(f"Error in subscription_command: {e}", exc_info=True)
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "❌ Failed to load subscription info. Please try again."
            )
        else:
            await update.message.reply_text(
                "❌ Failed to load subscription info. Please try again."
            )
    finally:
        await user_service.close()


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings command - Show user settings menu."""
    try:
        keyboard = settings_keyboards.get_settings_menu()

        await update.message.reply_text(
            "⚙️ **Settings**\n\n"
            "Manage your Lucide preferences:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.error(f"Error in settings_command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Failed to show settings menu. Please try again."
        )


async def link_account_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /link command - Link Telegram account to existing web/mobile account.

    Usage: /link LUCIDE-XXXXX
    """
    if not context.args or len(context.args) != 1:
        await update.message.reply_text(
            "**Link Your Account**\n\n"
            "To link your Telegram account with your existing Lucide account:\n\n"
            "1. Log in to lucide.ai\n"
            "2. Go to Settings → Telegram Integration\n"
            "3. Copy the linking code\n"
            "4. Send: `/link YOUR_CODE`\n\n"
            "Example: `/link LUCIDE-ABC123`",
            parse_mode="Markdown",
        )
        return

    code = context.args[0].upper()
    user = update.effective_user

    user_service = UserService(SessionLocal)

    try:
        # Validate and link account
        success = await user_service.link_account(
            telegram_user=user,
            linking_code=code,
        )

        if success:
            await update.message.reply_text(
                "✅ **Account Linked Successfully!**\n\n"
                "Your Telegram account is now connected.\n"
                "All your conversation history is available here.\n\n"
                "Use /history to access your conversations.",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                "❌ **Invalid or Expired Code**\n\n"
                "The linking code is invalid or has expired.\n"
                "Please generate a new code from lucide.ai and try again.",
                parse_mode="Markdown",
            )

    except Exception as e:
        logger.error(f"Error in link_account_command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ An error occurred while linking your account. Please try again."
        )
    finally:
        await user_service.close()


async def export_data_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /export command - Export user data (GDPR compliance)."""
    user = update.effective_user

    user_service = UserService(SessionLocal)
    export_service = ExportService(SessionLocal)

    try:
        await update.message.reply_text("⏳ Preparing your data export...")

        user_record = await user_service.get_or_create_user(user)

        # Generate export (JSON format)
        export_data = await export_service.export_user_data(user_record.user_id)

        # Send as file
        import io
        import json

        export_file = io.BytesIO(
            json.dumps(export_data, indent=2, ensure_ascii=False).encode("utf-8")
        )
        export_file.name = f"lucide_data_{user_record.user_id}.json"

        await update.message.reply_document(
            document=export_file,
            filename=export_file.name,
            caption="📦 **Your Complete Data Export**\n\n"
            "This file contains all your:\n"
            "• User profile\n"
            "• Conversations\n"
            "• Messages\n"
            "• Settings\n"
            "• Usage statistics\n\n"
            "GDPR compliant export in JSON format.",
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.error(f"Error in export_data_command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Failed to export data. Please try again or contact support."
        )
    finally:
        await user_service.close()
        await export_service.close()


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command - Cancel current operation."""
    # Clear any pending operations from context
    context.user_data.clear()

    await update.message.reply_text(
        "✅ **Operation Cancelled**\n\n"
        "Any pending operation has been cancelled.\n"
        "You can start fresh with /new or continue chatting.",
        parse_mode="Markdown",
    )
