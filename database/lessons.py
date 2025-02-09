# database/lessons.py
from database.connection import connect_to_db, disconnect_from_db
from utils.logging_utils import setup_logger
import const.const_db

logger = setup_logger('lessons', 'database.log')

def add_lesson(title, lesson_type, lesson_date, lesson_time, place, description):
    """
    Добавляет новое занятие и возвращает его идентификатор.
    """
    tunnel, conn, cur = const.const_db.TUNNEL, const.const_db.CONN, const.const_db.CUR
    try:
        query = """
            INSERT INTO lessons (title, type, lesson_date, lesson_time, place, description)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
        """
        cur.execute(query, (title, lesson_type, lesson_date, lesson_time, place, description))
        lesson_id = cur.fetchone()[0]
        conn.commit()
        logger.info(f"Lesson {lesson_id} added successfully.")
        return lesson_id
    except Exception as e:
        conn.rollback()
        logger.error(f"Error in add_lesson: {str(e)}")
        raise

