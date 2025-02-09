#subscriptions.py
from telebot import types
from bot.bot import bot
from const.const_bot import (
    R100_DICT, R300_DICT, R500_DICT, R1000_DICT, MAIN_MENU
)
from utils.logging_utils import log_function_call, setup_logger
from bot.payment import buy

logger = setup_logger('donation', 'bot.log')

@log_function_call(logger)
async def show_donation_options(call):
    """
    Предлагаем выбрать подписку, используя inline-кнопки, + "В главное меню".
    """
    username = call.from_user.username
    chat_id = call.message.chat.id

    try:
        text2 = "Выберите размер пожертвования:"

        markup = types.InlineKeyboardMarkup(row_width=1)

        R100 = types.InlineKeyboardButton(text=R100_DICT['label'], callback_data='R100')
        R300 = types.InlineKeyboardButton(text=R300_DICT['label'], callback_data='R300')
        R600 = types.InlineKeyboardButton(text=R500_DICT['label'], callback_data='R500')
        R1000 = types.InlineKeyboardButton(text=R1000_DICT['label'], callback_data='R1000')
        
        markup.add(R100)
        markup.add(R300)
        markup.add(R600)
        markup.add(R1000)

        btn_main_menu = types.InlineKeyboardButton(text=MAIN_MENU, callback_data='menu_start')
        markup.add(btn_main_menu)

        await bot.send_message(chat_id=chat_id, text=text2, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error in show_subscription_options: {str(e)}")
        raise


@bot.callback_query_handler(func=lambda call: call.data.startswith('R'))
async def handle_donation_callback(call):
    """
    Обрабатываем выбор подписки (inline).
    """
    await bot.answer_callback_query(call.id)
    data = call.data

    if data == 'R100':
        await buy(call.message, R100_DICT)
    elif data == 'R300':
        await buy(call.message, R300_DICT)
    elif data == 'R500':
        await buy(call.message, R500_DICT)
    elif data == 'R1000':
        await buy(call.message, R1000_DICT)