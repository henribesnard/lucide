# Lucide Telegram Bot

A comprehensive Telegram bot implementation for Lucide, providing intelligent football analysis through conversational AI.

## Overview

The Lucide Telegram Bot allows users to interact with the Lucide football analysis platform directly through Telegram, offering:

- **Conversational AI**: Ask questions in natural language about football matches, teams, and players
- **Match Analysis**: 39+ pattern detection algorithms for deep match insights
- **Real-time Updates**: Live match data and statistics from API-Football v3
- **Context Management**: Set league/match/team/player context for faster responses
- **Multi-language Support**: French and English
- **Subscription Tiers**: FREE, BASIC, PREMIUM, ENTERPRISE with different limits

## Architecture

```
backend/telegram/
├── bot.py                 # Main bot application
├── config.py              # Configuration and settings
├── requirements.txt       # Python dependencies
├── handlers/             # Message and command handlers
│   ├── command_handlers.py    # /start, /help, /new, etc.
│   ├── message_handlers.py    # Text message processing
│   ├── callback_handlers.py   # Inline keyboard callbacks
│   └── inline_handlers.py     # Inline query handling
├── services/             # Business logic services
│   ├── user_service.py        # User management
│   ├── conversation_service.py # Conversation CRUD
│   └── export_service.py      # Data export (GDPR)
├── keyboards/            # Inline keyboard layouts
│   ├── context_keyboards.py   # League/match/team selectors
│   └── settings_keyboards.py  # Settings menus
├── middleware/           # Middleware components
│   ├── rate_limiter.py        # Rate limiting
│   └── error_handler.py       # Error handling
└── utils/                # Utility functions
    └── formatter.py           # Message formatting
```

## Features

### Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot and create account |
| `/new` | Start a new conversation |
| `/history` | View conversation history |
| `/context` | Set match/league/team context |
| `/language` | Switch language (FR/EN) |
| `/subscription` | View subscription & upgrade |
| `/settings` | Manage preferences |
| `/link` | Link to existing web/mobile account |
| `/export` | Export your data (GDPR compliant) |
| `/help` | Show help message |
| `/cancel` | Cancel current operation |

### Key Features

1. **Automatic User Creation**: Users are automatically created when they start the bot
2. **Context Management**: Set context for faster, more relevant responses
3. **Conversation History**: All conversations are saved and accessible
4. **Rate Limiting**: 30 messages/minute (configurable, upgradable)
5. **Error Handling**: Comprehensive error handling with user-friendly messages
6. **Inline Mode**: Use @LucideBot in any chat to search for matches (optional)
7. **Group Chat Support**: Bot can be added to groups (optional)
8. **Data Export**: GDPR-compliant data export in JSON format

## Installation

### 1. Install Dependencies

```bash
pip install -r backend/telegram/requirements.txt
```

### 2. Create Bot on Telegram

1. Talk to @BotFather on Telegram
2. Create a new bot: `/newbot`
3. Follow the prompts to set name and username
4. Save the bot token

### 3. Environment Configuration

Add to your `.env` file:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_BOT_USERNAME=LucideBot

# Webhook (for production)
TELEGRAM_WEBHOOK_URL=https://yourdomain.com
TELEGRAM_WEBHOOK_PATH=/telegram/webhook
TELEGRAM_WEBHOOK_SECRET=your_webhook_secret

# Features
TELEGRAM_ENABLE_GROUPS=true
TELEGRAM_ENABLE_INLINE_MODE=true
TELEGRAM_ENABLE_PAYMENTS=false

# Rate Limiting
TELEGRAM_RATE_LIMIT_MESSAGES=30
TELEGRAM_RATE_LIMIT_WINDOW=60

# Backend Integration
BACKEND_BASE_URL=http://localhost:8000

# Redis (for rate limiting and sessions)
REDIS_URL=redis://localhost:6379
REDIS_DB=1

# Database (same as main backend)
DATABASE_URL=postgresql://user:password@localhost:5432/lucide
```

### 4. Database Migration

The bot requires additional fields in the `users` table. Run this migration:

```sql
-- Add Telegram fields to users table
ALTER TABLE users ADD COLUMN telegram_id BIGINT UNIQUE;
ALTER TABLE users ADD COLUMN telegram_username VARCHAR(255);
ALTER TABLE users ADD COLUMN telegram_first_name VARCHAR(255);
ALTER TABLE users ADD COLUMN telegram_last_name VARCHAR(255);
ALTER TABLE users ADD COLUMN telegram_language_code VARCHAR(10);

-- Make email/password nullable for Telegram-only users
ALTER TABLE users ALTER COLUMN email DROP NOT NULL;
ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;

-- Create index for fast telegram_id lookups
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
```

## Running the Bot

### Development (Polling)

For local development, use polling mode:

```bash
cd backend/telegram
python bot.py
```

Or from project root:

```bash
python -m backend.telegram.bot
```

### Production (Webhook)

For production, integrate with FastAPI:

```python
# backend/main.py

from backend.telegram.bot import create_bot

# Add to FastAPI startup
@app.on_event("startup")
async def startup_telegram_bot():
    bot = create_bot()
    # Set webhook
    await bot.application.bot.set_webhook(
        url=f"{TELEGRAM_WEBHOOK_URL}{TELEGRAM_WEBHOOK_PATH}",
        secret_token=TELEGRAM_WEBHOOK_SECRET,
    )

# Add webhook endpoint
from telegram import Update

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    bot = create_bot()
    update = Update.de_json(await request.json(), bot.application.bot)
    await bot.application.process_update(update)
    return {"status": "ok"}
```

## Integration with Lucide Backend

The bot integrates with the existing Lucide backend:

### 1. User Authentication

- Telegram users are automatically created in the `users` table
- `telegram_id` is used as the primary identifier
- No password required for Telegram users

### 2. Conversation Management

- Uses existing `conversations` and `messages` tables
- Each conversation has a unique `conversation_id`
- Messages are stored with `role` (user/assistant), `content`, `intent`, `tools_used`

### 3. Lucide Pipeline Integration

```python
from backend.agents.pipeline import LucidePipeline

# Create pipeline instance
pipeline = LucidePipeline(
    session_id=conversation_id,
    db_session_factory=SessionLocal,
)

# Process message
result = await pipeline.process(
    message_text,
    context=user_context,  # Optional context (league, match, team)
    user_id=str(user_record.user_id),
    model_type="slow",  # "slow", "medium", or "fast"
    language="fr",  # "fr" or "en"
    status_callback=status_callback,  # Optional progress updates
)

# Get response
response = result["answer"]
intent = result["intent"]
tools_used = result["tool_results"]
```

### 4. Context Management

Users can set context for their questions:

- **League Context**: "Premier League", "Ligue 1", "CAN"
- **Match Context**: Specific match (e.g., "PSG vs Barcelona")
- **Team Context**: Specific team (e.g., "Real Madrid")
- **Player Context**: Specific player (e.g., "Mbappé")

Context is stored in `context.user_data["context"]` and passed to the pipeline.

## Rate Limiting

The bot implements rate limiting to prevent spam:

- **Default**: 30 messages per minute
- **Configurable**: Set via `TELEGRAM_RATE_LIMIT_MESSAGES` and `TELEGRAM_RATE_LIMIT_WINDOW`
- **Subscription-based**: Can be increased for premium users
- **Implementation**: In-memory (development) or Redis (production)

To modify rate limits for premium users:

```python
# In message_handlers.py

if user_record.subscription_tier == SubscriptionTier.PREMIUM:
    max_messages = 100  # Premium: 100 messages/minute
else:
    max_messages = 30   # Free: 30 messages/minute
```

## Error Handling

Comprehensive error handling:

1. **Logging**: All errors logged with full traceback
2. **User Messages**: User-friendly error messages
3. **Admin Notifications**: Critical errors sent to admins (TODO)
4. **External Tracking**: Integration with Sentry/DataDog (TODO)

## Inline Mode

Users can use @LucideBot in any chat:

```
@LucideBot PSG vs Barcelona
```

Returns inline results with match predictions.

**Enable in .env:**
```bash
TELEGRAM_ENABLE_INLINE_MODE=true
```

## Group Chat Support

Add bot to groups for shared match analysis:

- Bot only responds when mentioned: `@LucideBot who will win?`
- Or when replying to bot's message
- No persistent context in groups (privacy)

**Enable in .env:**
```bash
TELEGRAM_ENABLE_GROUPS=true
```

## Data Export (GDPR Compliance)

Users can export all their data:

```
/export
```

Returns JSON file with:
- User profile
- All conversations
- All messages
- Usage statistics
- Export metadata

## Account Linking

Link Telegram account to existing web/mobile account:

1. User logs in to lucide.ai
2. Goes to Settings → Telegram Integration
3. Gets linking code (e.g., `LUCIDE-ABC123`)
4. Sends to bot: `/link LUCIDE-ABC123`
5. Accounts are linked

**Implementation:**
- Linking codes stored in Redis with 10-minute expiry
- Verify code and update `telegram_id` in user record
- All conversations become available in Telegram

## Testing

### Manual Testing

1. Start the bot: `python backend/telegram/bot.py`
2. Open Telegram and search for your bot
3. Send `/start`
4. Test all commands and features

### Automated Testing

```bash
# Unit tests
pytest backend/telegram/tests/

# Integration tests
pytest backend/telegram/tests/integration/
```

(Note: Test suite to be implemented)

## Deployment

### Docker

```dockerfile
# Dockerfile for Telegram bot

FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ backend/

CMD ["python", "-m", "backend.telegram.bot"]
```

### Docker Compose

```yaml
# docker-compose.yml

services:
  telegram-bot:
    build: .
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
```

### Environment Variables

Required:
- `TELEGRAM_BOT_TOKEN`
- `DATABASE_URL`
- `REDIS_URL`

Optional:
- `TELEGRAM_WEBHOOK_URL`
- `TELEGRAM_WEBHOOK_PATH`
- `TELEGRAM_WEBHOOK_SECRET`
- `TELEGRAM_ENABLE_GROUPS`
- `TELEGRAM_ENABLE_INLINE_MODE`

## Troubleshooting

### Bot Not Responding

1. Check bot token is correct
2. Verify bot is running: `ps aux | grep python`
3. Check logs: `tail -f logs/telegram_bot.log`
4. Test webhook: `curl -X POST https://yourdomain.com/telegram/webhook`

### Database Errors

1. Verify `telegram_id` field exists in `users` table
2. Run migrations: See "Database Migration" section
3. Check database connection: `psql -d lucide`

### Rate Limiting Issues

1. Adjust limits in `.env`:
   ```
   TELEGRAM_RATE_LIMIT_MESSAGES=60
   TELEGRAM_RATE_LIMIT_WINDOW=60
   ```
2. Or increase for specific users in database

### Pipeline Integration Errors

1. Verify Lucide backend is running
2. Check `BACKEND_BASE_URL` in `.env`
3. Test pipeline directly: `python -m backend.agents.pipeline`

## Monitoring

### Metrics to Track

- Message volume (messages/hour)
- Response time (seconds)
- Error rate (errors/messages)
- User growth (new users/day)
- Subscription conversions (upgrades/day)

### Logs

Logs are written to:
- Console (development)
- File (production): `logs/telegram_bot.log`
- External service (Sentry, DataDog)

### Health Check

Add to monitoring system:

```bash
# Check if bot is running
curl -X GET https://api.telegram.org/bot${BOT_TOKEN}/getMe
```

## Security

1. **Environment Variables**: Never commit `.env` to version control
2. **Webhook Secret**: Use strong secret for webhook validation
3. **Rate Limiting**: Prevent abuse with configurable limits
4. **Input Validation**: All user input is validated
5. **SQL Injection**: Using SQLAlchemy ORM prevents SQL injection
6. **HTTPS Only**: Webhooks must use HTTPS

## Future Enhancements

- [ ] Telegram Payments integration for subscriptions
- [ ] Voice message support (speech-to-text)
- [ ] Image generation for match visualizations
- [ ] Broadcast messaging to subscribers
- [ ] Admin panel for bot management
- [ ] A/B testing framework
- [ ] Multi-bot support (different bots per region)
- [ ] Bot analytics dashboard

## Support

For issues and questions:

- GitHub Issues: https://github.com/yourorg/lucide/issues
- Email: support@lucide.ai
- Telegram Support Group: @LucideSupport

## License

[Your License Here]

## Credits

Built with:
- [python-telegram-bot](https://python-telegram-bot.org/) - Telegram Bot API wrapper
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM
- [Redis](https://redis.io/) - Caching and rate limiting

---

**Lucide Telegram Bot** - Intelligent Football Analysis at Your Fingertips ⚽
