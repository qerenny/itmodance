# bot/subscription_notifications.py
import datetime
from telebot import types
from bot.bot import bot
from utils.logging_utils import log_function_call, setup_logger
from database.lessons import get_lessons_by_date  # Функция должна принимать параметр type для фильтрации
from database.subscriptions import get_all_active_subscription_users
from database.users import get_user_by_id
from database.notifications import add_notification, notification_exists

logger = setup_logger('subscription_notifications', 'bot.log')

@log_function_call(logger)
def get_subscription_lessons_for_date(date_obj):
    """
    Возвращает список занятий для указанной даты, у которых тип занятия равен 'Подписка'.
    Функция использует существующую get_lessons_by_date с дополнительным параметром типа.
    """
    # Предполагается, что get_lessons_by_date(date_obj, lesson_type) возвращает все занятия нужного типа.
    return get_lessons_by_date(date_obj, "Подписка")

@log_function_call(logger)
def get_all_subscription_users():
    """
    Возвращает список user_id всех пользователей с активной подпиской.
    """
    return get_all_active_subscription_users()

@log_function_call(logger)
async def notify_subscription_lessons():
    """
    Для всех занятий по подписке, которые пройдут завтра, отправляет уведомление пользователям,
    у которых есть активная подписка.
    
    Если уведомление для конкретного пользователя и занятия уже отправлено (проверяется через notification_exists),
    повторная отправка не производится.
    """
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    lessons = get_subscription_lessons_for_date(tomorrow)
    if not lessons:
        logger.info(f"No subscription lessons scheduled for {tomorrow}.")
        return

    user_ids = get_all_subscription_users()
    if not user_ids:
        logger.info("No subscription users found.")
        return

    for lesson in lessons:
        # Предполагаем, что структура lesson:
        # (id, title, lesson_date, lesson_time, place, description, ...)
        lesson_id = lesson[0]
        title = lesson[1]
        lesson_date = lesson[2]
        lesson_time = lesson[3]
        place = lesson[4]
        lesson_info = f"{title} {lesson_date} в {lesson_time} (место: {place})"
        for user_id in user_ids:
            # Получаем данные пользователя по первичному ключу
            user = get_user_by_id(user_id)
            if not user:
                logger.error(f"User with id {user_id} not found.")
                continue
            telegram_id = user[1]  # Предполагается, что telegram_id находится во втором столбце
            # Проверяем, отправлялось ли уже уведомление для этого пользователя и занятия
            if notification_exists(user_id, lesson_id, "subscription"):
                logger.info(f"Notification already sent for user {user_id} for lesson {lesson_id}. Skipping.")
                continue
            try:
                # Отправляем уведомление с кнопкой подтверждения участия
                await send_attendance_notification_for_subscription(telegram_id, lesson_id, lesson_info)
                add_notification(user_id, "subscription", lesson_id)
                logger.info(f"Notification sent to user {telegram_id} for lesson {lesson_id}.")
            except Exception as e:
                logger.error(f"Error notifying user {telegram_id} (user_id {user_id}) for lesson {lesson_id}: {str(e)}")

@log_function_call(logger)
async def send_attendance_notification_for_subscription(chat_id: int, lesson_id: int, lesson_info: str):
    """
    Отправляет уведомление о занятии по подписке с кнопкой подтверждения участия.
    Отправка реализована аналогично функции для клубных занятий.
    """
    markup = types.InlineKeyboardMarkup(row_width=1)
    button = types.InlineKeyboardButton("Подтвердить участие", callback_data=f"attend_{lesson_id}")
    markup.add(button)
    text = f"Напоминаем о занятии по подписке:\n{lesson_info}\nПожалуйста, подтвердите своё участие."
    await bot.send_message(chat_id, text, reply_markup=markup)
