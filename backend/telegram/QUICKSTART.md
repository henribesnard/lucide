# Lucide Telegram Bot - Quick Start Guide

Get your Telegram bot running in 5 minutes!

## Prerequisites

- Python 3.10+
- PostgreSQL database (from main Lucide backend)
- Redis server
- Telegram account

---

## Step 1: Create Your Bot (2 minutes)

1. Open Telegram
2. Search for `@BotFather`
3. Send: `/newbot`
4. Choose a name: `Lucide Football Analysis`
5. Choose a username: `LucideFootballBot` (must end with 'bot')
6. **Copy the bot token** - you'll need it next!

---

## Step 2: Install Dependencies (1 minute)

```bash
# Navigate to telegram folder
cd backend/telegram

# Install requirements
pip install -r requirements.txt
```

---

## Step 3: Configure Environment (1 minute)

```bash
# Copy example env file
cp .env.example .env

# Edit .env file
nano .env  # or use your favorite editor
```

**Minimal configuration needed:**

```bash
# Required: Your bot token from BotFather
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Required: Database (same as main backend)
DATABASE_URL=postgresql://user:password@localhost:5432/lucide

# Required: Redis
REDIS_URL=redis://localhost:6379

# Optional: Customize bot username
TELEGRAM_BOT_USERNAME=LucideFootballBot
```

---

## Step 4: Update Database (30 seconds)

```bash
# Run migration to add Telegram fields
psql -d lucide -f migrations/001_add_telegram_fields.sql
```

Or manually:

```sql
-- Add Telegram fields to users table
ALTER TABLE users ADD COLUMN telegram_id BIGINT UNIQUE;
ALTER TABLE users ADD COLUMN telegram_username VARCHAR(255);
ALTER TABLE users ADD COLUMN telegram_first_name VARCHAR(255);
ALTER TABLE users ADD COLUMN telegram_last_name VARCHAR(255);
ALTER TABLE users ADD COLUMN telegram_language_code VARCHAR(10);

-- Make email/password optional
ALTER TABLE users ALTER COLUMN email DROP NOT NULL;
ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;

-- Create index
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
```

---

## Step 5: Run the Bot (30 seconds)

```bash
# From backend/telegram directory
python run_bot.py
```

You should see:

```
INFO - Starting bot in POLLING mode...
INFO - Press Ctrl+C to stop
INFO - Bot post-initialization complete
```

---

## Step 6: Test Your Bot (1 minute)

1. Open Telegram
2. Search for your bot: `@LucideFootballBot`
3. Click "Start"
4. You should see a welcome message!
5. Try asking: `Who will win PSG vs Barcelona?`

---

## Quick Test Commands

Try these commands to verify everything works:

```
/start          - See welcome message
/help           - View help guide
/new            - Start new conversation
/history        - View conversation history (will be empty first time)
/context        - Set context menu
/language       - Switch to English (if French by default)
/subscription   - View subscription info
```

Ask a question:
```
Show me Premier League standings
```

or

```
Analyse le match PSG vs Marseille
```

---

## Troubleshooting

### Bot doesn't respond

**Check if bot is running:**
```bash
ps aux | grep python
```

**Check logs:**
```bash
tail -f logs/telegram_bot.log  # if logging to file
```

**Verify bot token:**
```python
# Test token
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe
```

### Database errors

**Verify migration ran:**
```sql
SELECT column_name FROM information_schema.columns
WHERE table_name = 'users' AND column_name LIKE 'telegram%';
```

Should return: `telegram_id`, `telegram_username`, etc.

### Module not found errors

```bash
# Make sure you're in the right directory
cd backend/telegram

# Install dependencies again
pip install -r requirements.txt

# Run from project root
cd ../..
python -m backend.telegram.run_bot
```

### Redis connection errors

**Start Redis:**
```bash
# Linux/Mac
redis-server

# Docker
docker run -d -p 6379:6379 redis:7-alpine
```

**Test connection:**
```bash
redis-cli ping
# Should return: PONG
```

---

## Production Deployment (Webhook Mode)

For production, use webhooks instead of polling:

### 1. Set up HTTPS domain

You need:
- Domain name: `yourdomain.com`
- SSL certificate (Let's Encrypt)
- Nginx/Caddy as reverse proxy

### 2. Update .env

```bash
TELEGRAM_WEBHOOK_URL=https://yourdomain.com
TELEGRAM_WEBHOOK_PATH=/telegram/webhook
TELEGRAM_WEBHOOK_SECRET=your_random_secret_here
```

### 3. Run in webhook mode

```bash
python run_bot.py --webhook --host 0.0.0.0 --port 8443
```

### 4. Set webhook

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://yourdomain.com/telegram/webhook" \
  -d "secret_token=your_random_secret_here"
```

---

## Docker Deployment

### Option 1: Standalone Container

```bash
# Build image
docker build -t lucide-telegram-bot -f backend/telegram/Dockerfile .

# Run container
docker run -d \
  --name lucide-bot \
  --env-file backend/telegram/.env \
  -p 8443:8443 \
  lucide-telegram-bot
```

### Option 2: Docker Compose

Add to your `docker-compose.yml`:

```yaml
services:
  telegram-bot:
    build:
      context: .
      dockerfile: backend/telegram/Dockerfile
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
```

Run:
```bash
docker-compose up -d telegram-bot
```

---

## Next Steps

Once your bot is running:

1. **Invite beta testers**: Share your bot with 5-10 users
2. **Monitor logs**: Watch for errors and issues
3. **Test all commands**: Go through each `/command`
4. **Test conversation flow**: Have multi-turn conversations
5. **Check database**: Verify users and conversations are created
6. **Stress test**: Send many messages quickly (test rate limiting)

---

## Getting Help

- **Documentation**: Read `README.md` for detailed docs
- **Implementation details**: Check `IMPLEMENTATION_SUMMARY.md`
- **Migration strategy**: See `documentation/telegram-bot-conversion-strategies.md`

---

## Common Customizations

### Change rate limit

Edit `.env`:
```bash
TELEGRAM_RATE_LIMIT_MESSAGES=60  # Allow 60 messages per minute
TELEGRAM_RATE_LIMIT_WINDOW=60
```

### Change bot commands

Edit `backend/telegram/handlers/command_handlers.py`

### Change welcome message

Edit the `start_command` function in `command_handlers.py`

### Add new command

1. Add handler in `command_handlers.py`:
```python
async def new_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("New command!")
```

2. Register in `bot.py`:
```python
self.application.add_handler(
    CommandHandler("newcommand", command_handlers.new_command)
)
```

3. Add to bot menu in `bot.py`:
```python
BotCommand("newcommand", "Description of new command"),
```

---

## Success Checklist

- [ ] Bot token obtained from @BotFather
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` configured with token and database
- [ ] Database migration run successfully
- [ ] Bot running (`python run_bot.py`)
- [ ] Can send `/start` and get welcome message
- [ ] Can ask questions and get responses
- [ ] Conversations saved to database
- [ ] Rate limiting works (tested)
- [ ] Error handling works (tested)

---

**You're all set! Your Lucide Telegram bot is now running.** 🎉

For production deployment, monitoring, and advanced features, see the full `README.md`.
