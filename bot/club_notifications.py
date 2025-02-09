# bot/club_notifications.py
import datetime
from bot.bot import bot
from database.lessons import get_lessons_by_date
from database.users import get_all_club_users
from database.notifications import add_notification
from utils.logging_utils import setup_logger, log_function_call

logger = setup_logger('club_notifications', 'club_notifications.log')

@log_function_call(logger)
def get_tomorrow_date():
    """Возвращает завтрашнюю дату."""
    return datetime.date.today() + datetime.timedelta(days=1)

@log_function_call(logger)
def get_club_lessons_for_date(date_obj):
    """
    Получает клубные занятия для заданной даты.
    Предполагается, что в поле type занятий записывается значение "Клубное"
    для клубных занятий.
    """
    return get_lessons_by_date(date_obj, "Клубное")

@log_function_call(logger)
def get_club_users():
    """
    Получает список пользователей, у которых заполнено поле ИСУ и отмечено, что они являются студентами ИТМО.
    """
    return get_all_club_users()

@log_function_call(logger)
async def notify_club_lessons():
    """
    Для всех клубных занятий, которые пройдут завтра, отправляет уведомление всем пользователям,
    у которых заполнен ИСУ (то есть они являются студентами ИТМО).
    Для каждого уведомления также регистрируется запись в таблице notifications.
    """
    tomorrow = get_tomorrow_date()
    lessons = get_club_lessons_for_date(tomorrow)
    if not lessons:
        logger.info(f"No club lessons scheduled for {tomorrow}.")
        return

    club_users = get_club_users()
    if not club_users:
        logger.info("No club users found.")
        return

    for lesson in lessons:
        # Предполагаем, что структура lesson: 
        # [id, title, type, lesson_date, lesson_time, place, description, ...]
        lesson_id = lesson[0]
        title = lesson[1]
        lesson_date = lesson[3]
        lesson_time = lesson[4]
        place = lesson[5]
        lesson_info = f"{title} {lesson_date} в {lesson_time} (место: {place})"
        for user in club_users:
            # Структура user: [id, telegram_id, username, first_name, last_name, ...]
            user_id = user[0]         # первичный ключ из таблицы users
            telegram_id = user[1]     # Telegram ID для отправки сообщения
            try:
                await bot.send_message(telegram_id, f"Напоминаем: завтра состоится клубное занятие:\n{lesson_info}")
                add_notification(user_id, "club", lesson_id)
            except Exception as e:
                logger.error(f"Error notifying user {telegram_id} (user_id {user_id}) for lesson {lesson_id}: {str(e)}")
