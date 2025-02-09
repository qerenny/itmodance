# init_db.py
import psycopg2
from database.connection import connect_to_db, disconnect_from_db
from utils.logging_utils import setup_logger

logger = setup_logger('init_db', 'database.log')

def create_tables():
    tunnel, conn, cur = connect_to_db()
    try:
        # Таблица пользователей
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                gender TEXT,
                consent_timestamp TIMESTAMP,  -- момент подтверждения согласия
                is_itmo BOOLEAN,
                isu_code TEXT,                -- 6-значный код, если применимо
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        logger.info("Table 'users' ensured.")

        # Таблица занятий
        cur.execute("""
            CREATE TABLE IF NOT EXISTS lessons (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                type TEXT NOT NULL,           -- категория = тип занятия
                lesson_date DATE NOT NULL,    -- дата проведения занятия
                lesson_time TIME NOT NULL,    -- время проведения занятия
                place TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        logger.info("Table 'lessons' ensured.")

        # Таблица подписок
        cur.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                start_date TIMESTAMP NOT NULL,
                end_date TIMESTAMP NOT NULL,
                payment_info JSONB,           -- дополнительные данные о платеже (если нужны)
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        logger.info("Table 'subscriptions' ensured.")

        # Таблица подтверждения участия (посещаемость)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
                confirmed_at TIMESTAMP DEFAULT NOW(),
                UNIQUE (user_id, lesson_id)
            );
        """)
        logger.info("Table 'attendance' ensured.")

        # Таблица уведомлений
        cur.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                lesson_id INTEGER REFERENCES lessons(id) ON DELETE CASCADE,
                notification_type TEXT NOT NULL,  -- тип уведомления: club, subscription, subscription_expiry и т.д.
                sent_at TIMESTAMP DEFAULT NOW()
            );
        """)
        logger.info("Table 'notifications' ensured.")

        conn.commit()
    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")
        conn.rollback()
        raise
    finally:
        disconnect_from_db(conn, tunnel)

if __name__ == '__main__':
    create_tables()
