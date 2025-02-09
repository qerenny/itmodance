# bot/subscriptions.py
import datetime
from utils.logging_utils import log_function_call, setup_logger
from bot.payment import buy
from telebot import types
from const.const_bot import (
    SUB1_DICT, SUB2_DICT, SUB3_DICT, MAIN_MENU
)
from bot.bot import bot
from database.users import get_user_by_telegram_id
from database.subscriptions import get_active_subscription

logger = setup_logger('subscriptions', 'bot.log')

async def get_subscription_status_text(chat_id: int) -> str:
    """
    Проверяет наличие активной подписки для пользователя по chat_id.
    Если активная подписка есть, возвращает отформатированный текст с оставшимся временем;
    иначе возвращает пустую строку.
    """
    user = get_user_by_telegram_id(chat_id)
    if not user:
        return ""
    
    user_pk = user[0]
    active_sub = get_active_subscription(user_pk)
    if not active_sub:
        return ""
    
    # Предполагаем, что active_sub имеет структуру:
    # (id, start_date, end_date, payment_info, created_at)
    end_date = active_sub[2]
    now = datetime.datetime.now()
    remaining = end_date - now

    if remaining.total_seconds() <= 0:
        return ""
    
    days = remaining.days
    seconds = remaining.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    return (f"\nУ вас активная подписка до {end_date.strftime('%Y-%m-%d %H:%M:%S')} "
            f"(осталось: {days} дн. {hours} ч. {minutes} мин.)")

@log_function_call(logger)
async def show_subscription_options(call):
    """
    Отправляет сообщение с выбором подписки.
    Если у пользователя уже есть активная подписка, к тексту добавляется информация о ней.
    """
    chat_id = call.message.chat.id

    # Получаем текст с информацией об активной подписке (если есть)
    subscription_status_text = await get_subscription_status_text(chat_id)

    try:
        if subscription_status_text:
            text2 = f"{subscription_status_text}"
        else:
            text2 = f"Выберите свою подписку:"

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
    Обрабатывает выбор подписки через inline-кнопки.
    В зависимости от выбора вызывается функция buy с соответствующим продуктом.
    """
    await bot.answer_callback_query(call.id)
    data = call.data

    if data == 'SUB1':
        await buy(call.message, SUB1_DICT)
    elif data == 'SUB2':
        await buy(call.message, SUB2_DICT)
    elif data == 'SUB3':
        await buy(call.message, SUB3_DICT)
