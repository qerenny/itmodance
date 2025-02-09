import datetime
from telebot import types
from bot.bot import bot
from utils.logging_utils import log_function_call, setup_logger
from database.attendance import get_attendance_by_lesson
from database.lessons import get_future_lessons
from database.users import get_user_by_id

logger = setup_logger('admin_attendance', 'bot.log')


@log_function_call(logger)
def build_future_lessons_keyboard():
    """
    Создает InlineKeyboardMarkup с кнопками для будущих занятий.
    Текст каждой кнопки содержит название, дату и время занятия.
    Callback data формируется как "stats_<lesson_id>".
    """
    lessons = get_future_lessons()
    markup = types.InlineKeyboardMarkup(row_width=1)
    for lesson in lessons:
        lesson_id = lesson[0]
        title = lesson[1]
        lesson_date = lesson[2]
        lesson_time = lesson[3]
        # Форматируем кнопку, например: "Танцы - 2025-03-15 18:00"
        button_text = f"{title} - {lesson_date} {lesson_time}"
        btn = types.InlineKeyboardButton(button_text, callback_data=f"stats_{lesson_id}")
        markup.add(btn)
    logger.info("Built future lessons keyboard.")
    return markup

async def send_future_lessons_for_stats(chat_id: int):
    """
    Отправляет сообщение с кнопками для выбора будущего занятия для получения статистики.
    """
    markup = build_future_lessons_keyboard()
    # Вместо markup.inline_keyboard используем markup.keyboard для проверки наличия кнопок
    if not markup.keyboard:
        await bot.send_message(chat_id, "Нет будущих занятий для статистики.")
    else:
        await bot.send_message(chat_id, "Выберите занятие для получения статистики:", reply_markup=markup)
        
@log_function_call(logger)
def build_attendance_stats_string(lesson_id: int) -> str:
    """
    Формирует строку статистики участия для занятия с данным lesson_id.
    Выводит:
      - Количество мужчин и женщин,
      - Список участников с ФИО и @username.
    """
    records = get_attendance_by_lesson(lesson_id)
    if not records:
        return "Для данного занятия не зафиксировано подтверждений участия."
    
    male_count = 0
    female_count = 0
    male_list = []
    female_list = []
    
    # Перебираем все записи участия. Предполагается, что каждая запись имеет вид (user_id, confirmed_at).
    for record in records:
        user_id = record[0]
        user = get_user_by_id(user_id)
        if user:
            # Структура user: (id, telegram_id, username, first_name, last_name, gender)
            gender = user[5] or ""
            full_name = f"{user[3]} {user[4]}"
            username = user[2] or ""
            entry = f"{full_name} (@{username})"
            if gender.lower() in ("женский", "female"):
                female_count += 1
                female_list.append(entry)
            elif gender.lower() in ("мужской", "male"):
                male_count += 1
                male_list.append(entry)
    
    stats = f"Статистика участия для занятия ID {lesson_id}:\n"
    stats += f"Мужчин: {male_count}\n"
    stats += f"Женщин: {female_count}\n\n"
    if male_list:
        stats += "Парни:\n" + "\n".join(male_list) + "\n\n"
    if female_list:
        stats += "Девушки:\n" + "\n".join(female_list)
    return stats

@bot.callback_query_handler(func=lambda call: call.data.startswith("stats_"))
@log_function_call(logger)
async def handle_stats_callback(call):
    """
    Обрабатывает нажатие на кнопку статистики для выбранного занятия.
    Из callback data извлекается lesson_id, затем формируется и отправляется сообщение со статистикой.
    """
    try:
        lesson_id_str = call.data.split("_")[1]
        lesson_id = int(lesson_id_str)
    except Exception as e:
        await bot.answer_callback_query(call.id, "Ошибка: некорректные данные занятия.")
        logger.error(f"Error parsing lesson_id in stats callback: {str(e)}")
        return

    stats_text = build_attendance_stats_string(lesson_id)
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id, stats_text)
