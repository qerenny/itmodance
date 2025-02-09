from utils.logging_utils import log_function_call, setup_logger
from bot.payment import buy
from telebot import types
from const.const_bot import (
    SUB1_DICT, SUB2_DICT, SUB3_DICT, MAIN_MENU
)
from bot.bot import bot

logger = setup_logger('subscriptions', 'bot.log')

@log_function_call(logger)
async def show_subscription_options(call):
    """
    Предлагаем выбрать подписку, используя inline-кнопки, + "В главное меню".
    """
    username = call.from_user.username
    chat_id = call.message.chat.id

    try:
        text2 = "Выберите свою подписку:"

        markup = types.InlineKeyboardMarkup(row_width=1)

        SUB1 = types.InlineKeyboardButton(text=SUB1_DICT['label'], callback_data='SUB1')
        SUB2 = types.InlineKeyboardButton(text=SUB2_DICT['label'], callback_data='SUB2')
        SUB3 = types.InlineKeyboardButton(text=SUB3_DICT['label'], callback_data='SUB3')
        
        markup.add(SUB1)
        markup.add(SUB2)
        markup.add(SUB3)

        btn_main_menu = types.InlineKeyboardButton(text=MAIN_MENU, callback_data='menu_start')
        markup.add(btn_main_menu)

        await bot.send_message(chat_id=chat_id, text=text2, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error in show_subscription_options: {str(e)}")
        raise


@bot.callback_query_handler(func=lambda call: call.data.startswith('SUB'))
async def handle_subscription_callback(call):
    """
    Обрабатываем выбор подписки (inline).
    """
    await bot.answer_callback_query(call.id)
    data = call.data

    if data == 'SUB1':
        await buy(call.message, SUB1_DICT)
    elif data == 'SUB2':
        await buy(call.message, SUB2_DICT)
    elif data == 'SUB3':
        await buy(call.message, SUB3_DICT)
