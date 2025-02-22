import asyncio
import datetime
from bot.bot import bot
from utils.logging_utils import setup_logger
from bot.subscription_fun.subscription_expiry import notify_expiring_subscriptions
from bot.notifications import notify_all_lessons  # Универсальная функция уведомлений
from middleware.connection import login_db, logout

logger = setup_logger('main', 'main.log')

async def schedule_daily_task(task_func, hour, minute=0):
    """
    Асинхронно планирует ежедневный запуск задачи в указанное время.
    """
    while True:
        now = datetime.datetime.now()
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if now > target_time:
            target_time += datetime.timedelta(days=1)
        wait_seconds = (target_time - now).total_seconds()
        logger.info(f"Ожидание {wait_seconds:.0f} секунд до запуска задачи в {hour:02}:{minute:02}.")
        await asyncio.sleep(wait_seconds)

        try:
            await task_func()
            logger.info(f"Задача {task_func.__name__} успешно выполнена.")
        except Exception as e:
            logger.error(f"Ошибка при выполнении задачи {task_func.__name__}: {str(e)}")

async def run_test_notifications_every_minute(task_func):
    """
    Тестовая функция: вызывает указанную задачу каждые 60 секунд.
    """
    while True:
        try:
            await task_func()
            logger.info(f"Тестовая задача {task_func.__name__} выполнена.")
        except Exception as e:
            logger.error(f"Ошибка при тестовом запуске {task_func.__name__}: {str(e)}")
        await asyncio.sleep(60)

async def run_bot():
    """
    Основной цикл бота с запуском уведомлений.
    """
    login_db()
    logger.info("Запуск бота и планировщика задач...")

    await asyncio.gather(
        bot.polling(),
        schedule_daily_task(notify_all_lessons, 10, 0),  # Уведомления о занятиях в 10:00
        schedule_daily_task(notify_expiring_subscriptions, 10, 5),  # Уведомления об истекающих подписках в 10:05
    )

def main():
    logger.info("Основная функция бота запущена.")
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем (KeyboardInterrupt).")
    except Exception as e:
        logger.error(f"Критическая ошибка в main: {str(e)}")
        raise
    finally:
        logout()
        logger.info("Соединение с базой данных закрыто.")

if __name__ == '__main__':
    main()
