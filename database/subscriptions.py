# database/subscriptions.py
from database.connection import connect_to_db, disconnect_from_db
from utils.logging_utils import setup_logger
import const.const_db
from psycopg2.extras import Json


logger = setup_logger('subscriptions', 'database.log')

def add_subscription(user_id, start_date, end_date, payment_info):
    """
    Добавляет подписку для пользователя и возвращает её идентификатор.
    payment_info передается в виде словаря, который сохраняется в формате JSONB.
    """
    tunnel, conn, cur = const.const_db.TUNNEL, const.const_db.CONN, const.const_db.CUR
    try:
        query = """
            INSERT INTO subscriptions (user_id, start_date, end_date, payment_info)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
        """
        cur.execute(query, (user_id, start_date, end_date, Json(payment_info)))
        sub_id = cur.fetchone()[0]
        conn.commit()
        logger.info(f"Subscription {sub_id} added for user {user_id}.")
        return sub_id
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding subscription: {str(e)}")
        raise

def get_active_subscription(user_id):
    """
    Возвращает активную подписку пользователя, если таковая имеется.
    Активной считается подписка, у которой end_date > NOW().
    Возвращается запись подписки в виде кортежа:
      (id, start_date, end_date, payment_info, created_at)
    Если активной подписки нет, возвращается None.
    """
    tunnel, conn, cur = const.const_db.TUNNEL, const.const_db.CONN, const.const_db.CUR
    try:
        query = """
            SELECT id, start_date, end_date, payment_info, created_at
            FROM subscriptions
            WHERE user_id = %s AND end_date > NOW()
            ORDER BY end_date DESC
            LIMIT 1;
        """
        cur.execute(query, (user_id,))
        subscription = cur.fetchone()
        logger.info(f"Fetched active subscription for user {user_id}: {subscription}")
        return subscription
    except Exception as e:
        logger.error(f"Error in get_active_subscription: {str(e)}")
        raise
    
def update_subscription_end_date(subscription_id, new_end_date):
    """
    Обновляет дату окончания подписки с заданным subscription_id.
    """
    tunnel, conn, cur = const.const_db.TUNNEL, const.const_db.CONN, const.const_db.CUR
    try:
        query = "UPDATE subscriptions SET end_date = %s WHERE id = %s;"
        cur.execute(query, (new_end_date, subscription_id))
        conn.commit()
        logger.info(f"Subscription {subscription_id} updated with new end_date: {new_end_date}.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating subscription {subscription_id}: {str(e)}")
        raise
    
def get_subscriptions_expiring_tomorrow():
    """
    Возвращает список подписок, у которых дата окончания (end_date) равна завтрашней дате.
    Результатом является список кортежей: (id, user_id, end_date)
    """
    tunnel, conn, cur = const.const_db.TUNNEL, const.const_db.CONN, const.const_db.CUR
    try:
        query = """
            SELECT id, user_id, end_date
            FROM subscriptions
            WHERE end_date::date = (CURRENT_DATE + INTERVAL '1 day');
        """
        cur.execute(query)
        subs = cur.fetchall()
        logger.info(f"Fetched {len(subs)} subscriptions expiring tomorrow.")
        return subs
    except Exception as e:
        logger.error(f"Error in get_subscriptions_expiring_tomorrow: {str(e)}")
        raise
    
def get_all_active_subscription_users():
    """
    Возвращает список уникальных user_id для пользователей, у которых есть активная подписка.
    Активная подписка считается, если end_date > NOW().
    """
    tunnel, conn, cur = const.const_db.TUNNEL, const.const_db.CONN, const.const_db.CUR
    try:
        query = """
            SELECT DISTINCT user_id
            FROM subscriptions
            WHERE end_date > NOW();
        """
        cur.execute(query)
        rows = cur.fetchall()
        user_ids = [row[0] for row in rows]
        logger.info(f"Fetched {len(user_ids)} active subscription users.")
        return user_ids
    except Exception as e:
        logger.error(f"Error in get_all_active_subscription_users: {str(e)}")
        raise