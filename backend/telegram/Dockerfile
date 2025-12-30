FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy root requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install telegram bot specific dependencies
RUN pip install --no-cache-dir python-telegram-bot[all]==20.7

# Copy entire backend directory (needed for imports)
COPY backend ./backend

WORKDIR /app

CMD ["python", "-m", "backend.telegram.run_bot"]