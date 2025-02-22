import datetime
from telebot import types
from bot.bot import bot
from utils.logging_utils import log_function_call, setup_logger
from database.lessons import get_lessons_by_date
from database.subscriptions import get_all_active_subscription_users
from database.users import get_all_club_users, get_user_by_id
from database.notifications import add_notification, notification_exists

logger = setup_logger('lesson_notifications', 'bot.log')

@log_function_call(logger)
async def notify_all_lessons():
    """
    Универсальная функция уведомлений. Обрабатывает занятия всех типов ("Клубное", "Подписка", "Индивидуальное").
    Уведомления отправляются за день до занятия.
    """
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    lesson_types = ["Клубное", "Подписка", "Индивидуальное"]
    
    for lesson_type in lesson_types:
        lessons = get_lessons_by_date(tomorrow, lesson_type)
        if not lessons:
            logger.info(f"No {lesson_type.lower()} lessons scheduled for {tomorrow}.")
            continue

        # Получаем список пользователей в зависимости от типа занятия
        if lesson_type == "Подписка":
            user_ids = get_all_active_subscription_users()
        elif lesson_type == "Клубное":
            user_ids = [user[0] for user in get_all_club_users()]  # Берем user_id
        else:  # Индивидуальное занятие (список участников определяется отдельно)
            user_ids = [lesson[7] for lesson in lessons]  # Предполагаем, что в 7-м индексе хранится user_id

        if not user_ids:
            logger.info(f"No users found for {lesson_type.lower()} lessons.")
            continue

        for lesson in lessons:
            lesson_id, title, _, lesson_date, lesson_time, place, *_ = lesson
            lesson_info = f"{title} {lesson_date} в {lesson_time} (место: {place})"

            for user_id in user_ids:
                user = get_user_by_id(user_id)
                if not user:
                    logger.error(f"User with id {user_id} not found.")
                    continue

                telegram_id = user[1]  # Telegram ID

                if notification_exists(user_id, lesson_id, lesson_type.lower()):
                    logger.info(f"Notification already sent for user {user_id} for lesson {lesson_id}. Skipping.")
                    continue

                try:
                    await send_attendance_notification(telegram_id, lesson_id, lesson_info, lesson_type)
                    add_notification(user_id, lesson_type.lower(), lesson_id)
                    logger.info(f"Notification sent to user {telegram_id} for {lesson_type.lower()} lesson {lesson_id}.")
                except Exception as e:
                    logger.error(f"Error notifying user {telegram_id} (user_id {user_id}) for lesson {lesson_id}: {str(e)}")

@log_function_call(logger)
async def send_attendance_notification(chat_id: int, lesson_id: int, lesson_info: str, lesson_type: str):
    """
    Отправляет уведомление о занятии с кнопкой подтверждения.
    """
    markup = types.InlineKeyboardMarkup(row_width=1)
    button = types.InlineKeyboardButton("Подтвердить участие", callback_data=f"attend_{lesson_id}")
    markup.add(button)
    text = f"Напоминаем о {lesson_type.lower()} занятии:\n{lesson_info}\nПожалуйста, подтвердите своё участие."
    await bot.send_message(chat_id, text, reply_markup=markup)
