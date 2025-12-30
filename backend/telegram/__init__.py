"""
Lucide Telegram Bot Package

A comprehensive Telegram bot implementation for the Lucide football analysis platform.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the telegram directory BEFORE any other imports
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

__version__ = "1.0.0"
__author__ = "Lucide Team"

from backend.telegram.bot import create_bot, LucideTelegramBot

__all__ = ["create_bot", "LucideTelegramBot"]
