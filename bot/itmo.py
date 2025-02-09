# bot/itmo.py
import re
from telebot import types
from bot.bot import bot
from database.users import add_user, get_user_by_telegram_id
from utils.logging_utils import log_function_call, setup_logger

logger = setup_logger('itmo', 'itmo.log')

# Локальный словарь для отслеживания состояния ввода ИСУ для каждого чата.
itmo_states = {}

# Регулярное выражение для проверки, что введённый ИСУ состоит ровно из 6 цифр.
ISU_REGEX = re.compile(r'^\d{6}$')

@log_function_call(logger)
async def prompt_for_itmo_status(chat_id: int):
    """
    Спрашивает у пользователя, является ли он студентом ИТМО.
    Отправляет inline-клавиатуру с вариантами "Да" и "Нет".
    """
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_yes = types.InlineKeyboardButton("Да", callback_data="itmo_yes")
    btn_no = types.InlineKeyboardButton("Нет", callback_data="itmo_no")
    markup.add(btn_yes, btn_no)
    await bot.send_message(chat_id, "Вы студент ИТМО?", reply_markup=markup)
    # Устанавливаем состояние (на случай, если понадобится отслеживать ответ)
    itmo_states[chat_id] = "pending_response"
    
@log_function_call(logger)
async def prompt_for_isu(chat_id: int):
    """
    Запрашивает ввод ИСУ (6 цифр) у пользователя, который подтвердил, что является студентом ИТМО,
    но ещё не указал ИСУ. Устанавливает состояние 'awaiting_isu'.
    """
    itmo_states[chat_id] = "awaiting_isu"
    await bot.send_message(chat_id, "Введите ваш ИСУ (6 цифр):")

@bot.callback_query_handler(func=lambda call: call.data in ["itmo_yes", "itmo_no"])
@log_function_call(logger)
async def handle_itmo_response(call):
    """
    Обрабатывает ответ на вопрос, является ли пользователь студентом ИТМО.
    Если "Да" – обновляет запись (is_itmo=True) и переводит в состояние ввода ИСУ;
    если "Нет" – обновляет запись (is_itmo=False) и завершает регистрацию.
    """
    chat_id = call.message.chat.id
    user = get_user_by_telegram_id(chat_id)
    if user is None:
        await bot.answer_callback_query(call.id, "Ошибка: пользователь не найден в базе.")
        return

    if call.data == "itmo_yes":
        # Обновляем запись: is_itmo = True; ISU пока не указан
        add_user(
            chat_id,
            call.from_user.username,
            user[3],  # first_name
            user[4],  # last_name
            user[5],  # gender
            user[6],  # consent_timestamp
            True,
            None      # isu_code пока отсутствует
        )
        # Переводим в состояние ввода ИСУ
        itmo_states[chat_id] = "awaiting_isu"
        await bot.answer_callback_query(call.id, "Отлично, вы студент ИТМО. Введите, пожалуйста, ваш ИСУ (6 цифр).")
        await bot.send_message(chat_id, "Введите ваш ИСУ (6 цифр):")
    else:  # itmo_no
        # Обновляем запись: is_itmo = False
        add_user(
            chat_id,
            call.from_user.username,
            user[3],  # first_name
            user[4],  # last_name
            user[5],  # gender
            user[6],  # consent_timestamp
            False,
            None      # isu_code не требуется
        )
        # Убираем состояние, если было установлено
        if chat_id in itmo_states:
            del itmo_states[chat_id]
        await bot.answer_callback_query(call.id, "Спасибо за ответ. Регистрация завершена.")
        await bot.send_message(chat_id, "Спасибо, регистрация завершена.")

@bot.message_handler(func=lambda message: itmo_states.get(message.chat.id) == "awaiting_isu")
@log_function_call(logger)
async def handle_isu_input(message):
    """
    Обрабатывает ввод ИСУ, проверяя, что он состоит ровно из 6 цифр.
    В случае успеха обновляет запись пользователя.
    """
    chat_id = message.chat.id
    text = message.text.strip()

    if not ISU_REGEX.fullmatch(text):
        await bot.send_message(chat_id, "Неверный формат. Введите ровно 6 цифр для ИСУ.")
        return

    user = get_user_by_telegram_id(chat_id)
    if user is None:
        await bot.send_message(chat_id, "Ошибка: пользователь не найден в базе.")
        return

    # Обновляем запись: сохраняем ИСУ и подтверждаем, что is_itmo уже True
    add_user(
        chat_id,
        message.from_user.username,
        user[3],  # first_name
        user[4],  # last_name
        user[5],  # gender
        user[6],  # consent_timestamp
        True,
        text      # сохраненный ИСУ-код
    )
    # Убираем состояние ввода ИСУ
    if chat_id in itmo_states:
        del itmo_states[chat_id]
    await bot.send_message(chat_id, "Спасибо, ваш ИСУ успешно сохранён. Регистрация завершена.")
