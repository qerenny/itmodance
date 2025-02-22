# bot/attendance.py
import re
from telebot import types
from bot.bot import bot
from database.attendance import add_attendance, get_attendance_by_lesson
from database.users import get_user_by_telegram_id
from utils.config import BOT_ADMIN_IDS
from utils.logging_utils import log_function_call, setup_logger
from bot.admin_fun.admin_attendance import send_future_lessons_for_stats

logger = setup_logger('attendance', 'attendance.log')

@log_function_call(logger)
async def send_attendance_notification(chat_id: int, lesson_id: int, lesson_info: str):
    """
    Отправляет уведомление о занятии с кнопкой подтверждения участия.
    :param chat_id: Идентификатор чата пользователя.
    :param lesson_id: Идентификатор занятия.
    :param lesson_info: Текстовое описание занятия (например, название, дата, время).
    """
    markup = types.InlineKeyboardMarkup(row_width=1)
    button = types.InlineKeyboardButton("Подтвердить участие", callback_data=f"attend_{lesson_id}")
    markup.add(button)
    text = f"Напоминаем о занятии:\n{lesson_info}\nПожалуйста, подтвердите своё участие."
    await bot.send_message(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("attend_"))
@log_function_call(logger)
async def handle_attendance_confirmation(call):
    """
    Обрабатывает нажатие кнопки подтверждения участия.
    Из callback_data извлекается идентификатор занятия, затем регистрируется участие,
    используя первичный ключ пользователя из таблицы users. После успешной регистрации
    удаляется сообщение с кнопкой.
    """
    chat_id = call.message.chat.id
    user = get_user_by_telegram_id(chat_id)
    if user is None:
        await bot.answer_callback_query(call.id, "Ошибка: пользователь не найден в базе.")
        return

    try:
        lesson_id_str = call.data.split("_")[1]
        lesson_id = int(lesson_id_str)
    except (IndexError, ValueError):
        await bot.answer_callback_query(call.id, "Ошибка: некорректные данные занятия.")
        return

    try:
        # Используем первичный ключ пользователя (первый элемент записи)
        user_pk = user[0]
        add_attendance(user_pk, lesson_id)
        # Удаляем исходное сообщение с кнопкой
        await bot.delete_message(chat_id, call.message.message_id)
        await bot.answer_callback_query(call.id, "Ваше участие подтверждено!")
        await bot.send_message(chat_id, "Спасибо, ваше участие зафиксировано.")
    except Exception as e:
        logger.error(f"Ошибка регистрации участия для пользователя {chat_id}, занятие {lesson_id}: {str(e)}")
        await bot.answer_callback_query(call.id, "Ошибка при регистрации участия. Попробуйте позже.")
