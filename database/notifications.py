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

def notification_exists(user_id, lesson_id, notification_type):
    """
    Проверяет, существует ли запись уведомления для заданного пользователя, занятия и типа уведомления.
    Возвращает True, если такая запись найдена, иначе False.
    """
    tunnel, conn, cur = const.const_db.TUNNEL, const.const_db.CONN, const.const_db.CUR
    try:
        query = """
            SELECT 1 FROM notifications
            WHERE user_id = %s AND lesson_id = %s AND notification_type = %s
            LIMIT 1;
        """
        cur.execute(query, (user_id, lesson_id, notification_type))
        exists = cur.fetchone() is not None
        logger.info(f"Notification exists check for user {user_id}, lesson_id {lesson_id}, type {notification_type}: {exists}")
        return exists
    except Exception as e:
        logger.error(f"Error in notification_exists: {str(e)}")
        raise