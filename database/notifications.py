# database/notifications.py
from database.connection import connect_to_db, disconnect_from_db
from utils.logging_utils import setup_logger
import const.const_db

logger = setup_logger('notifications', 'database.log')

def add_notification(user_id, notification_type, lesson_id=None):
    """
    Регистрирует факт отправки уведомления.
    Если уведомление не связано с конкретным занятием, lesson_id может быть None.
    """
    tunnel, conn, cur = const.const_db.TUNNEL, const.const_db.CONN, const.const_db.CUR
    try:
        query = """
            INSERT INTO notifications (user_id, lesson_id, notification_type)
            VALUES (%s, %s, %s);
        """
        cur.execute(query, (user_id, lesson_id, notification_type))
        conn.commit()
        logger.info(f"Notification of type '{notification_type}' added for user {user_id}.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error in add_notification: {str(e)}")
        raise

