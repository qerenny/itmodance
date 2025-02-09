# bot/consent.py
import datetime
from telebot import types
from bot.bot import bot
from database.users import add_user, get_user_by_telegram_id
from utils.logging_utils import log_function_call, setup_logger

logger = setup_logger('consent', 'consent.log')
CONSENT_BUTTON_CALLBACK = 'consent_agree'

@log_function_call(logger)
async def ask_for_consent(chat_id):
    """
    Отправляет сообщение с запросом на обработку персональных данных и кнопку для подтверждения.
    """
    text = (
        "Для продолжения работы с ботом, пожалуйста, подтвердите, что вы согласны на обработку ваших "
        "персональных данных согласно соответствующей статье РФ."
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    consent_button = types.InlineKeyboardButton("Я согласен", callback_data=CONSENT_BUTTON_CALLBACK)
    markup.add(consent_button)
    await bot.send_message(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == CONSENT_BUTTON_CALLBACK)
@log_function_call(logger)
async def handle_consent_agree(call):
    """
    Обрабатывает нажатие кнопки "Я согласен" и фиксирует факт согласия (текущая дата и время) в базе данных.
    Затем переводит пользователя в состояние ввода имени и фамилии.
    """
    telegram_id = call.from_user.id
    username = call.from_user.username
    consent_timestamp = datetime.datetime.now()

    try:
        user = get_user_by_telegram_id(telegram_id)
        if user is None:
            # Создаем нового пользователя с подтверждением согласия.
            add_user(telegram_id, username, None, None, None, consent_timestamp, False, None)
        else:
            # Обновляем существующую запись, фиксируя время согласия.
            first_name = user[3]
            last_name = user[4]
            gender = user[5]
            is_itmo = user[7]
            isu_code = user[8]
            add_user(telegram_id, username, first_name, last_name, gender, consent_timestamp, is_itmo, isu_code)
    except Exception as e:
        logger.error(f"Ошибка при обработке согласия для пользователя {telegram_id}: {str(e)}")
        await bot.answer_callback_query(call.id, "Ошибка при обработке согласия.")
        return

    await bot.answer_callback_query(call.id, "Согласие получено.")

    # Импортируем и вызываем функцию для запроса ФИО, которая установит состояние 'awaiting_name'
    from bot.user_info import prompt_for_name
    await prompt_for_name(call.message.chat.id)
