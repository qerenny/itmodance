# bot/subscription_expiry.py
import datetime
from bot.bot import bot
from database.subscriptions import get_subscriptions_expiring_tomorrow
from database.users import get_user_by_id
from database.notifications import add_notification
from utils.logging_utils import log_function_call, setup_logger

logger = setup_logger('subscription_expiry', 'subscription_expiry.log')

@log_function_call(logger)
def get_expiring_subscriptions():
    """
    Получает список подписок, истекающих завтра.
    """
    return get_subscriptions_expiring_tomorrow()

@log_function_call(logger)
async def notify_expiring_subscriptions():
    """
    Получает список подписок, истекающих завтра, и отправляет уведомление каждому пользователю.
    """
    subs = get_expiring_subscriptions()
    if not subs:
        logger.info("Нет подписок, истекающих завтра.")
        return

    for sub in subs:
        subscription_id, user_id, end_date = sub
        # Получаем данные пользователя по первичному ключу
        user = get_user_by_id(user_id)
        if not user:
            logger.error(f"Пользователь с id {user_id} не найден.")
            continue
        telegram_id = user[1]  # Предполагается, что telegram_id находится во втором столбце
        # Форматируем дату окончания подписки
        end_date_str = end_date.strftime('%Y-%m-%d')
        message_text = (
            f"Ваша подписка истекает завтра ({end_date_str}). "
            "Не забудьте продлить её, чтобы продолжить пользоваться услугами."
        )
        try:
            await bot.send_message(telegram_id, message_text)
            # Регистрируем уведомление; здесь lesson_id=None, а тип уведомления "subscription_expiry"
            add_notification(user_id, "subscription_expiry", None)
            logger.info(f"Уведомление об истекающей подписке отправлено пользователю {telegram_id}.")
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления для пользователя {telegram_id}: {str(e)}")

