# bot/attendance.py
import re
from telebot import types
from bot.bot import bot
from database.attendance import add_attendance, get_attendance_by_lesson
from database.users import get_user_by_telegram_id
from utils.config import BOT_ADMIN_IDS
from utils.logging_utils import log_function_call, setup_logger

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
    Из callback_data извлекается идентификатор занятия, затем регистрируется участие.
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
        add_attendance(chat_id, lesson_id)
        await bot.answer_callback_query(call.id, "Ваше участие подтверждено!")
        await bot.send_message(chat_id, "Спасибо, ваше участие зафиксировано.")
    except Exception as e:
        logger.error(f"Ошибка регистрации участия для пользователя {chat_id}, занятие {lesson_id}: {str(e)}")
        await bot.answer_callback_query(call.id, "Ошибка при регистрации участия. Попробуйте позже.")

@bot.message_handler(commands=['attendance_stats'])
@log_function_call(logger)
async def attendance_stats(message):
    """
    Команда для администратора для получения статистики по подтверждённым участникам занятия.
    Ожидается, что сообщение будет вида: /attendance_stats <lesson_id>
    """
    chat_id = message.chat.id
    if message.from_user.id not in BOT_ADMIN_IDS:
        await bot.send_message(chat_id, "У вас нет прав для выполнения этой команды.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await bot.send_message(chat_id, "Пожалуйста, укажите ID занятия. Пример: /attendance_stats 5")
        return

    try:
        lesson_id = int(parts[1])
    except ValueError:
        await bot.send_message(chat_id, "Некорректный ID занятия. Он должен быть числом.")
        return

    try:
        records = get_attendance_by_lesson(lesson_id)
        if not records:
            await bot.send_message(chat_id, f"Для занятия с ID {lesson_id} подтверждений участия не найдено.")
            return

        text = f"Статистика участия для занятия ID {lesson_id}:\n"
        count = 0
        for record in records:
            user_id = record[0]
            confirmed_at = record[1]
            text += f"- Пользователь {user_id}, подтверждено: {confirmed_at}\n"
            count += 1
        text += f"Всего подтверждений: {count}"
        await bot.send_message(chat_id, text)
    except Exception as e:
        logger.error(f"Ошибка при получении статистики участия для занятия {lesson_id}: {str(e)}")
        await bot.send_message(chat_id, "Ошибка при получении статистики участия.")
