#!/usr/bin/env python3
"""
Singapore Weather Telegram Bot
Main entry point for the bot application
"""
from flask import Flask
import threading

app = Flask('')


@app.route('/')
def home():
    return "I'm alive!"


def run_web():
    app.run(host='0.0.0.0', port=8080)


def keep_alive():
    t = threading.Thread(target=run_web)
    t.start()


import logging
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram import BotCommand
from config import BOT_TOKEN
from bot_handlers import (start_handler, help_handler, weather_handler,
                          rainfall_handler, wind_speed_handler,
                          wind_direction_handler, wind_handler,
                          stations_handler, error_handler, menu_handler,
                          callback_query_handler)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main function to run the bot"""
    logger.info("Starting Singapore Weather Bot...")

    # Validate bot token
    if not BOT_TOKEN or BOT_TOKEN.strip() == "":
        logger.error(
            "Bot token is missing or empty. Please set the TELEGRAM_BOT_TOKEN environment variable."
        )
        raise ValueError("Bot token is required to run the bot")

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("menu", menu_handler))
    application.add_handler(CommandHandler("weather", weather_handler))
    application.add_handler(CommandHandler("rainfall", rainfall_handler))
    application.add_handler(CommandHandler("windspeed", wind_speed_handler))
    application.add_handler(
        CommandHandler("winddirection", wind_direction_handler))
    application.add_handler(CommandHandler("wind", wind_handler))
    application.add_handler(CommandHandler("stations", stations_handler))

    # Add callback query handler for menu buttons
    application.add_handler(CallbackQueryHandler(callback_query_handler))

    # Add error handler
    application.add_error_handler(error_handler)

    # Add message handler for unknown commands
    application.add_handler(MessageHandler(filters.COMMAND, help_handler))

    logger.info("Bot handlers registered successfully")

    # Run the bot
    logger.info("Bot is running and polling for updates...")
    keep_alive()
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == '__main__':
    main()
