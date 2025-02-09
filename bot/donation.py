#subscriptions.py
from telebot import types
from bot.bot import bot
from const_bot import (
    R100_ARR, R300_ARR, R500_ARR, R1000_ARR, MAIN_MENU
)
from utils.logging_utils import log_function_call, setup_logger
from bot.payment import buy

logger = setup_logger('subscriptions', 'bot.log')

@log_function_call(logger)
async def show_payment_options(call):
    """
    Предлагаем выбрать подписку, используя inline-кнопки, + "В главное меню".
    """
    username = call.from_user.username
    chat_id = call.message.chat.id

    try:
        text2 = "Выберите размер пожертвования:"

        markup = types.InlineKeyboardMarkup(row_width=1)

        R100 = types.InlineKeyboardButton(text=R100_ARR['label'], callback_data='R100')
        R300 = types.InlineKeyboardButton(text=R300_ARR['label'], callback_data='R300')
        R600 = types.InlineKeyboardButton(text=R500_ARR['label'], callback_data='R500')
        R1000 = types.InlineKeyboardButton(text=R1000_ARR['label'], callback_data='R1000')
        
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
async def handle_pay_callback(call):
    """
    Обрабатываем выбор подписки (inline).
    """
    await bot.answer_callback_query(call.id)
    data = call.data

    await bot.delete_message(call.message.chat.id, call.message.message_id)

    if data == 'R100':
        await buy(call.message, R100_ARR)
    elif data == 'R300':
        await buy(call.message, R300_ARR)
    elif data == 'R500':
        await buy(call.message, R500_ARR)
    elif data == 'R1000':
        await buy(call.message, R1000_ARR)