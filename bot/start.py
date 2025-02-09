# start.py
from bot.consent import ask_for_consent
from database.users import get_user_by_telegram_id
from telebot import types
from bot.bot import bot
from const.const_bot import (
    DONATION, SUBSCRIPTION
)
from bot.donation import show_donation_options
from bot.subscription_fun.subscription import show_subscription_options
from utils.logging_utils import log_function_call, setup_logger
from bot.user_info import prompt_for_name, prompt_for_gender
from bot.itmo import prompt_for_itmo_status, prompt_for_isu

logger = setup_logger('start', 'bot.log')


@log_function_call(logger)
@bot.message_handler(commands=['start'])
async def send_start(message):
    """
    Обработчик команды /start.
    Проверяет, заполнены ли обязательные данные пользователя (согласие, ФИО, пол).
    Если какие-либо данные отсутствуют, запрашивает их.
    """
    telegram_id = message.from_user.id
    try:
        user = get_user_by_telegram_id(telegram_id)
    except Exception as e:
        logger.error(f"Ошибка при получении данных пользователя {telegram_id}: {str(e)}")
        await bot.send_message(message.chat.id, "Произошла ошибка при обращении к базе данных.")
        return

    # Если записи нет, запрашиваем согласие
    if user is None:
        await ask_for_consent(message.chat.id)
        return

    # Структура записи (пример): 
    # [id, telegram_id, username, first_name, last_name, gender, consent_timestamp, is_itmo, isu_code, ...]
    consent_timestamp = user[6]
    first_name = user[3]
    last_name = user[4]
    gender = user[5]
    is_itmo = user[7]
    isu_code = user[8]

    if consent_timestamp is None:
        await ask_for_consent(message.chat.id)
        return

    if not first_name or not last_name:
        await prompt_for_name(message.chat.id)
        return

    if not gender:
        await prompt_for_gender(message.chat.id)
        return
    
    if not is_itmo:  # если поле is_itmo ещё не заполнено
        await prompt_for_itmo_status(message.chat.id)
        return
    
    if is_itmo is True and (isu_code is None or not str(isu_code).strip()):
        await prompt_for_isu(message.chat.id)
        return

    try:
        await send_main_menu(message)

    except Exception as e:
        logger.exception(f"Unhandled error in send_start for chat_id={telegram_id}: {str(e)}")
        raise

@log_function_call(logger)
async def send_main_menu(message):
    """
    Отправляет главное меню пользователю без обработки реферальных кодов и удаляет старое меню.
    """
    username = message.from_user.username
    chat_id = message.chat.id
    
    text = '''Приветствуем в боте клуба парных танцев "Потанцуем?".'''
    try:
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_donation = types.InlineKeyboardButton(text=DONATION, callback_data='menu_payment')
        btn_subscription = types.InlineKeyboardButton(text=SUBSCRIPTION, callback_data='menu_subscription')
    
        markup.add(btn_donation)
        markup.add(btn_subscription)

        sent_msg = await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=markup
        )
    except Exception as e:
        logger.error(f"Error in send_main_menu: {str(e)}")
        raise


@log_function_call(logger)
@bot.callback_query_handler(func=lambda call: call.data in [
    'menu_payment', 'menu_start', 'menu_subscription'
])
async def handle_menu_callback(call):
    """
    Обрабатываем нажатия на кнопки PROFILE, HELP, INSTRUCTIONS, REFERRALS и MAIN MENU (inline).
    """

    try:
        if call.data == 'menu_payment':
            await show_donation_options(call)
        elif call.data == 'menu_subscription':
            await show_subscription_options(call)
        elif call.data == 'menu_start':
            await send_main_menu(call.message)

            
    except Exception as e:
        logger.error(f"Critical error in handle_menu_callback: {str(e)}")