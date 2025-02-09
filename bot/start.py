# start.py

from telebot import types
from bot.bot import bot
from const_bot import (
    DONATION
)
from bot.donation import show_payment_options
from utils.logging_utils import log_function_call, setup_logger

logger = setup_logger('start', 'bot.log')


@log_function_call(logger)
@bot.message_handler(commands=['start'])
async def send_start(message):
    """
    Handles the /start command: checks the referral code and displays the main menu.
    """
    username = message.from_user.username
    chat_id = message.chat.id

    try:
        await send_main_menu(message)

    except Exception as e:
        logger.exception(f"Unhandled error in send_start for chat_id={chat_id}: {str(e)}")
        raise

@log_function_call(logger)
async def send_main_menu(message):
    """
    Отправляет главное меню пользователю без обработки реферальных кодов и удаляет старое меню.
    """
    username = message.from_user.username
    chat_id = message.chat.id
    
    text = "Приветствуем в боте для пожертвований клубу ""."
    try:
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_donation = types.InlineKeyboardButton(text=DONATION, callback_data='menu_payment')
    
        markup.add(btn_donation)

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
    'menu_payment', 'menu_start'
])
async def handle_menu_callback(call):
    """
    Обрабатываем нажатия на кнопки PROFILE, HELP, INSTRUCTIONS, REFERRALS и MAIN MENU (inline).
    """
    await bot.delete_message(call.message.chat.id, call.message.message_id)

    try:
        if call.data == 'menu_payment':
            await show_payment_options(call)
        elif call.data == 'menu_start':
            await send_main_menu(call.message)

            
    except Exception as e:
        logger.error(f"Critical error in handle_menu_callback: {str(e)}")