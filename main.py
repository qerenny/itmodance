# main.py
import asyncio
from bot.bot import bot
from utils.logging_utils import setup_logger
from bot import start, payment, donation, subscription, consent, admin_attendance, user_info, admin_lessons, club_notifications, itmo, attendance
from middleware.connection import login_db, logout
import datetime
from bot.club_notifications import notify_club_lessons

logger = setup_logger('main', 'main.log')

async def run_daily_notifications_at_10():
    """
    Асинхронно ожидает наступления 10:00 и запускает уведомления,
    затем повторяет цикл для следующего дня.
    """
    while True:
        now = datetime.datetime.now()
        target_time = now.replace(hour=10, minute=0, second=0, microsecond=0)
        # Если текущее время уже позже 10:00, планируем на следующий день.
        if now > target_time:
            target_time += datetime.timedelta(days=1)
        wait_seconds = (target_time - now).total_seconds()
        logger.info(f"Ожидаем {wait_seconds:.0f} секунд до следующего запуска в 10:00.")
        await asyncio.sleep(wait_seconds)
        try:
            await notify_club_lessons()
        except Exception as e:
            logger.error(f"Ошибка в уведомлениях: {str(e)}")


async def run_test_notifications_every_minute():
    """
    Тестовая функция, которая каждые 60 секунд вызывает рассылку уведомлений.
    Используйте её для проверки работы уведомлений без ожидания 10:00.
    """
    while True:
        try:
            await notify_club_lessons()
            logger.info("Тестовое уведомление отправлено.")
        except Exception as e:
            logger.error(f"Ошибка при тестовой рассылке уведомлений: {str(e)}")
        await asyncio.sleep(60)  # Ждём 60 секунд перед следующим запуском


async def run_bot():
    while True:
        try:
            # Устанавливаем соединение один раз
            login_db()
            logger.info("Starting bot polling with established DB connection...")
            await asyncio.gather(
                bot.polling(),
                run_daily_notifications_at_10()
            )
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
