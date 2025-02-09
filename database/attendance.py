# database/attendance.py
from database.connection import connect_to_db, disconnect_from_db
from utils.logging_utils import setup_logger
import const.const_db

logger = setup_logger('attendance', 'database.log')

def add_attendance(user_id, lesson_id):
    """
    Регистрирует участие пользователя в занятии.
    При наличии конфликта (одинаковая пара user_id и lesson_id) операция не дублируется.
    """
    tunnel, conn, cur = const.const_db.TUNNEL, const.const_db.CONN, const.const_db.CUR
    try:
        query = """
            INSERT INTO attendance (user_id, lesson_id)
            VALUES (%s, %s)
            ON CONFLICT (user_id, lesson_id) DO NOTHING;
        """
        cur.execute(query, (user_id, lesson_id))
        conn.commit()
        logger.info(f"Attendance recorded for user {user_id} on lesson {lesson_id}.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error in add_attendance: {str(e)}")
        raise

def get_attendance_by_lesson(lesson_id):
    """
    Возвращает список записей участия для заданного занятия.
    Каждая запись содержит (user_id, confirmed_at).
    """
    tunnel, conn, cur = const.const_db.TUNNEL, const.const_db.CONN, const.const_db.CUR
    try:
        query = "SELECT user_id, confirmed_at FROM attendance WHERE lesson_id = %s;"
        cur.execute(query, (lesson_id,))
        records = cur.fetchall()
        logger.info(f"Fetched {len(records)} attendance records for lesson {lesson_id}.")
        return records
    except Exception as e:
        logger.error(f"Error in get_attendance_by_lesson: {str(e)}")
        raise