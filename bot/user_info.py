# bot/user_info.py
import re
from telebot import types
from bot.bot import bot
from database.users import add_user, get_user_by_telegram_id
from utils.logging_utils import log_function_call, setup_logger

logger = setup_logger('user_info', 'user_info.log')

# Состояния пользователей: ключ – chat_id, значение – текущее состояние.
user_states = {}

# Регулярное выражение для проверки корректного ввода имени и фамилии.
NAME_REGEX = re.compile(r'^[A-Za-zА-Яа-яЁё\s-]+$')

def is_valid_name(text: str) -> bool:
    """
    Проверяет, что текст содержит минимум два слова (имя и фамилию)
    и что каждое слово состоит только из допустимых символов.
    """
    parts = text.strip().split()
    if len(parts) < 2:
        return False
    for part in parts:
        if not NAME_REGEX.fullmatch(part):
            return False
    return True

@log_function_call(logger)
async def prompt_for_name(chat_id: int):
    """
    Запрашивает у пользователя ввод имени и фамилии.
    Устанавливает состояние 'awaiting_name'.
    """
    user_states[chat_id] = "awaiting_name"
    await bot.send_message(chat_id, "Пожалуйста, введите своё имя и фамилию:")

@log_function_call(logger)
async def prompt_for_gender(chat_id: int):
    """
    Запрашивает у пользователя выбор пола через inline-кнопки.
    Устанавливает состояние 'awaiting_gender'.
    """
    user_states[chat_id] = "awaiting_gender"
    markup = types.InlineKeyboardMarkup(row_width=2)
    male_btn = types.InlineKeyboardButton("Мужской", callback_data="gender_male")
    female_btn = types.InlineKeyboardButton("Женский", callback_data="gender_female")
    markup.add(male_btn, female_btn)
    await bot.send_message(chat_id, "Пожалуйста, выберите свой пол:", reply_markup=markup)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "awaiting_name")
@log_function_call(logger)
async def handle_name_input(message):
    """
    Обрабатывает ввод ФИО.
    Если формат некорректен, просит повторить ввод.
    При корректном вводе обновляет запись пользователя и переводит в состояние выбора пола.
    """
    chat_id = message.chat.id
    text = message.text.strip()

    if not is_valid_name(text):
        await bot.send_message(chat_id, "Некорректный формат. Введите имя и фамилию, используя только буквы, пробел и дефис.")
        return

    parts = text.split()
    first_name = parts[0]
    last_name = parts[1]

    try:
        user = get_user_by_telegram_id(chat_id)
        if user is None:
            # Если по какой-то причине запись отсутствует, создаем новую.
            add_user(chat_id, message.from_user.username, first_name, last_name, None, None, None, None)
        else:
            # Обновляем запись, сохраняя уже имеющиеся значения для остальных полей.
            add_user(
                chat_id,
                message.from_user.username,
                first_name,
                last_name,
                user[5],  # gender (на данный момент может быть None)
                user[6],  # consent_timestamp
                user[7],  # is_itmo
                user[8]   # isu_code
            )
    except Exception as e:
        logger.error(f"Ошибка обновления ФИО для пользователя {chat_id}: {str(e)}")
        await bot.send_message(chat_id, "Произошла ошибка при сохранении данных. Попробуйте позже.")
        return

    # Переход к вводу пола.
    user_states[chat_id] = "awaiting_gender"
    await prompt_for_gender(chat_id)

@bot.callback_query_handler(func=lambda call: call.data in ["gender_male", "gender_female"])
@log_function_call(logger)
async def handle_gender_selection(call):
    """
    Обрабатывает выбор пола через inline-кнопки.
    Обновляет запись пользователя и очищает состояние.
    """
    chat_id = call.message.chat.id
    gender = "Мужской" if call.data == "gender_male" else "Женский"

    try:
        user = get_user_by_telegram_id(chat_id)
        if user is None:
            add_user(chat_id, call.from_user.username, None, None, gender, None, None, None)
        else:
            add_user(
                chat_id,
                call.from_user.username,
                user[3],  # first_name
                user[4],  # last_name
                gender,
                user[6],  # consent_timestamp
                user[7],  # is_itmo
                user[8]   # isu_code
            )
    except Exception as e:
        logger.error(f"Ошибка обновления пола для пользователя {chat_id}: {str(e)}")
        await bot.answer_callback_query(call.id, "Ошибка при сохранении данных.")
        return

    if chat_id in user_states:
        del user_states[chat_id]

    await bot.answer_callback_query(call.id, "Данные успешно сохранены.")
    await bot.send_message(chat_id, "Спасибо, ваши данные сохранены.")
