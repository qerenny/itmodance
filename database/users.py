# database/users.py
from database.connection import connect_to_db, disconnect_from_db
from utils.logging_utils import setup_logger
import const.const_db

logger = setup_logger('users', 'database.log')

def add_user(telegram_id, username, first_name, last_name, gender, consent_timestamp, is_itmo, isu_code):
    """
    Добавляет нового пользователя или обновляет существующую запись по telegram_id.
    """
    tunnel, conn, cur = const.const_db.TUNNEL, const.const_db.CONN, const.const_db.CUR
    try:
        query = """
            INSERT INTO users (telegram_id, username, first_name, last_name, gender, consent_timestamp, is_itmo, isu_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (telegram_id) DO UPDATE SET
                username = EXCLUDED.username,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                gender = EXCLUDED.gender,
                consent_timestamp = EXCLUDED.consent_timestamp,
                is_itmo = EXCLUDED.is_itmo,
                isu_code = EXCLUDED.isu_code,
                updated_at = NOW();
        """
        cur.execute(query, (telegram_id, username, first_name, last_name, gender, consent_timestamp, is_itmo, isu_code))
        conn.commit()
        logger.info(f"User {telegram_id} added/updated successfully.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error in add_user: {str(e)}")
        raise


def get_user_by_telegram_id(telegram_id):
    """
    Получает данные пользователя по telegram_id.
    """
    tunnel, conn, cur = const.const_db.TUNNEL, const.const_db.CONN, const.const_db.CUR
    
    try:
        query = "SELECT * FROM users WHERE telegram_id = %s;"
        cur.execute(query, (telegram_id,))
        user = cur.fetchone()
        logger.info(f"Fetched user for telegram_id {telegram_id}.")
        return user
    except Exception as e:
        logger.error(f"Error in get_user_by_telegram_id: {str(e)}")

