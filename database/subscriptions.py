# database/subscriptions.py
from database.connection import connect_to_db, disconnect_from_db
from utils.logging_utils import setup_logger
import const.const_db

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
        cur.execute(query, (user_id, start_date, end_date, payment_info))
        sub_id = cur.fetchone()[0]
        conn.commit()
        logger.info(f"Subscription {sub_id} added for user {user_id}.")
        return sub_id
    except Exception as e:
        conn.rollback()
        logger.error(f"Error in add_subscription: {str(e)}")
        raise

