#main.py
import asyncio

from bot.bot import bot
import utils.config
from utils.logging_utils import setup_logger
from bot import start, payment, donation
logger = setup_logger('main', 'main.log')

async def run_bot():
    """
    Runs the Telegram bot with automatic reconnection and reminder task.
    """
    while True:
        try:
            logger.info("Starting bot polling...")
            await bot.polling()
        except Exception as e:
            logger.error(f"Bot polling error: {str(e)}")
            logger.info("Attempting to restart bot in 5 seconds...")
            await asyncio.sleep(5)

def main():
    """
    Main entry point to run the asynchronous bot.
    """
    logger.info("Bot main function started.")
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (KeyboardInterrupt).")
    except Exception as e:
        logger.error(f"Critical error in main: {str(e)}")
        raise
    logger.info("Bot main function ended.")

if __name__ == '__main__':
    main()