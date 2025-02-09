# main.py
import asyncio
from bot.bot import bot
from utils.logging_utils import setup_logger
from bot import start, payment, donation, subscription, consent, user_info
from middleware.connection import login_db, logout

logger = setup_logger('main', 'main.log')

async def run_bot():
    while True:
        try:
            # Устанавливаем соединение один раз
            login_db()
            logger.info("Starting bot polling with established DB connection...")
            await bot.polling()
        except Exception as e:
            logger.error(f"Bot polling error: {str(e)}")
            logger.info("Attempting to restart bot in 5 seconds...")
            await asyncio.sleep(5)
        # Если бот перезапускается, соединение будет переиспользовано до явного logout().

def main():
    logger.info("Bot main function started.")
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (KeyboardInterrupt).")
    except Exception as e:
        logger.error(f"Critical error in main: {str(e)}")
        raise
    finally:
        logout()  # Завершаем соединение при выходе
    logger.info("Bot main function ended.")

if __name__ == '__main__':
    main()
