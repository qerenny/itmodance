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

def get_lessons_by_date(date_obj, lesson_type):
    """
    Возвращает список занятий, которые проводятся в date_obj и имеют указанный тип.
    Например, для клубных занятий lesson_type должен быть "Клубное".
    """
    tunnel, conn, cur = const.const_db.TUNNEL, const.const_db.CONN, const.const_db.CUR
    try:
        query = "SELECT * FROM lessons WHERE lesson_date = %s AND type = %s;"
        cur.execute(query, (date_obj, lesson_type))
        lessons = cur.fetchall()
        logger.info(f"Fetched {len(lessons)} lessons for date {date_obj} and type '{lesson_type}'.")
        return lessons
    except Exception as e:
        logger.error(f"Error in get_lessons_by_date: {str(e)}")
        raise
    
def get_future_lessons():
    """
    Возвращает список будущих занятий (начиная с текущей даты).
    Предполагается, что таблица lessons имеет столбцы:
      id, title, lesson_date, lesson_time, place, ...
    """
    tunnel, conn, cur = const.const_db.TUNNEL, const.const_db.CONN, const.const_db.CUR
    try:
        query = """
            SELECT id, title, lesson_date, lesson_time, place
            FROM lessons
            WHERE lesson_date >= CURRENT_DATE
            ORDER BY lesson_date ASC;
        """
        cur.execute(query)
        lessons = cur.fetchall()
        logger.info(f"Fetched {len(lessons)} future lessons.")
        return lessons
    except Exception as e:
        logger.error(f"Error in get_future_lessons: {str(e)}")
        raise
