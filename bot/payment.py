#payment.py
from telebot.types import LabeledPrice
from bot.bot import bot
from const.const_bot import CURRENCY
from utils import json_fun
from utils.logging_utils import log_function_call, setup_logger
from utils.config import BOT_TEST_PROVIDER_TOKEN, BOT_LIVE_PROVIDER_TOKEN, BOT_ADMIN_IDS
import datetime
from dateutil.relativedelta import relativedelta
from database.subscriptions import add_subscription, get_active_subscription, update_subscription_end_date
from database.users import get_user_by_telegram_id

logger = setup_logger('payments', 'payment.log')

@log_function_call(logger)
async def buy(message, product):
    """
    Sends an invoice to the user for a chosen subscription product.
    """
    try:
        prices = [LabeledPrice(label=product['label'], amount=product['amount'])]
        json_data = json_fun.receipt_creator(f'receipt.json', product['description'], product['amount'])

        msg_invoice = await bot.send_invoice(
            message.chat.id,
            title=product['label'],
            description=product['description'],
            provider_token=BOT_TEST_PROVIDER_TOKEN,
            currency=CURRENCY,
            prices=prices,
            start_parameter='subscription',
            invoice_payload=product['payload'],
            need_email=True,
            send_email_to_provider=True,
            provider_data=json_data,
        )
        logger.info(f"Invoice for {product['label']} sent successfully.")

        return msg_invoice
    except Exception as e:
        logger.error(f"Error in buy: {str(e)}")
        await bot.send_message(
            chat_id=message.chat.id,
            text="❌ Произошла ошибка при создании платежа. Пожалуйста, попробуйте позже или обратитесь в поддержку."
        )
        raise


@log_function_call(logger)
@bot.pre_checkout_query_handler(func=lambda query: True)
async def process_pre_checkout_query(pre_checkout_query):
    """
    Confirms the checkout query before finalizing payment.
    """
    try:
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
        logger.info("Pre-checkout query answered with OK=True.")
    except Exception as e:
        logger.error(f"Error in process_pre_checkout_query: {str(e)}")
        await bot.answer_pre_checkout_query(
            pre_checkout_query.id,
            ok=False,
            error_message="❌ К сожалению, произошла ошибка при проверке платежа. Попробуйте позже."
        )
        raise


@log_function_call(logger)
@bot.message_handler(content_types=['successful_payment'])
async def successful_payment(message):
    from bot.start import send_main_menu

    """
    Handles a successful payment event.
    """
    tg_id = message.chat.id
    username = message.from_user.username

    try:
        try:
            payment_info = message.successful_payment
            payment_amount = payment_info.total_amount // 100
            payment_currency = payment_info.currency
            payment_payload = payment_info.invoice_payload
        except AttributeError as e:
            logger.error(f"Error retrieving payment information for tg_id={tg_id}: {str(e)}")
            raise
        
        await bot.send_message(
            chat_id=tg_id,
            text=f'✅ Платёж на {payment_amount} {payment_currency} прошёл успешно!\n'
        )
            
        if payment_payload.startswith('D'):
            await bot.send_message(
                chat_id=BOT_ADMIN_IDS[1],
                text=f'Оплата пожертвования в размере {payment_amount} {payment_currency} от @{username} ({tg_id}).'
            )
            await bot.send_message(
            chat_id=tg_id,
            text=f'✅ Ожидайте в течение 3-х дней, мы вам напишем благодарственное сообщение.\n'
            )
            
        if payment_payload.startswith('S'):
            try:
                await subscription_handler(payment_payload, payment_amount, payment_currency, tg_id)
                
                await bot.send_message(
                chat_id=BOT_ADMIN_IDS[1],
                text=f'Оплата подписки в размере {payment_amount} {payment_currency} от @{username} ({tg_id}).'
            )
            except Exception as e:
                logger.error(f"Error handling subscription payment for tg_id={tg_id}: {str(e)}")

        
        await send_main_menu(message)

    except Exception as e:
        logger.error(f"Unhandled error in successful_payment for tg_id={tg_id}: {str(e)}")
        await bot.send_message(
            chat_id=tg_id,
            text="❌ Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже или обратитесь в поддержку."
        )
        raise


@log_function_call(logger)
@bot.message_handler(content_types=['unsuccessful_payment'])
async def unsuccessful_payment(message):
    """
    Handles an unsuccessful payment event.
    """
    tg_id = message.chat.id

    try:
        await bot.send_message(
            chat_id=tg_id,
            text="❌ К сожалению, платёж не удался. Это может произойти по нескольким причинам:\n\n"
            "• Недостаточно средств на карте\n"
            "• Банк отклонил операцию\n"
            "• Технические проблемы на стороне платёжной системы\n\n"
            "Попробуйте использовать другую карту или повторите попытку позже. "
            "Если проблема сохраняется, обратитесь в поддержку."
        )
        logger.info(f"Unsuccessful payment message sent to user tg_id={tg_id}.")

    except Exception as e:
        logger.error(f"Unhandled error in unsuccessful_payment for tg_id={tg_id}: {str(e)}")
        raise
    
    
async def subscription_handler(payment_payload, payment_amount, payment_currency, tg_id):
    """
    Обрабатывает интеграцию подписки после успешного платежа.
    Если у пользователя уже есть активная подписка, то дата окончания обновляется
    (расширяется на новый период); иначе создается новая подписка.
    """
    try:
        # Определяем длительность подписки по типу
        if payment_payload == 'S1':
            months = 1
        elif payment_payload == 'S2':
            months = 2
        elif payment_payload == 'S3':
            months = 3
        else:
            months = 1  # значение по умолчанию
        logger.info(f"Определена длительность подписки: {months} месяц(ев) для payload '{payment_payload}'.")

        now = datetime.datetime.now()

        subscription_payment_info = {
            "amount": payment_amount,
            "currency": payment_currency,
            "payload": payment_payload
        }
        logger.info(f"Информация о платеже подписки: {subscription_payment_info}.")

        # Получаем запись пользователя по Telegram ID
        user = get_user_by_telegram_id(tg_id)
        if user is not None:
            user_pk = user[0]  # первичный ключ в таблице users
            active_sub = get_active_subscription(user_pk)
            if active_sub is not None:
                # Если активная подписка есть, берем базовую дату для обновления:
                # Если текущая end_date меньше now, берем now, иначе берем текущую end_date.
                current_end_date = active_sub[2]
                base_date = now if current_end_date < now else current_end_date
                new_end_date = base_date + relativedelta(months=months)
                update_subscription_end_date(active_sub[0], new_end_date)
                logger.info(f"Подписка для user_pk {user_pk} обновлена, новое окончание: {new_end_date}.")
                await bot.send_message(
                    tg_id,
                    f"Ваша подписка обновлена до {new_end_date.strftime('%Y-%m-%d %H:%M:%S')}."
                )
            else:
                # Если активной подписки нет, создаем новую
                start_date = now
                end_date = start_date + relativedelta(months=months)
                add_subscription(user_pk, start_date, end_date, subscription_payment_info)
                logger.info(f"Новая подписка добавлена для user_pk {user_pk} с окончанием {end_date}.")
                await bot.send_message(
                    tg_id,
                    f"Ваша подписка оформлена до {end_date.strftime('%Y-%m-%d %H:%M:%S')}."
                )
        else:
            logger.error(f"Пользователь с Telegram ID {tg_id} не найден при оформлении подписки.")
    except Exception as e:
        logger.error(f"Ошибка в subscription_handler: {str(e)}")
        raise