#middleware/connection.py
import const.const_db
import database.connection
from utils.logging_utils import log_function_call, setup_logger, retry_on_error

logger = setup_logger('connection.middleware', 'middleware.log')

@retry_on_error(retries=3, delay=5)
@log_function_call(logger)
def login_db():
    """
    Ensures a connection to the local database is established.
    """
    try:
        if const.const_db.CONN is None:
            const.const_db.TUNNEL, const.const_db.CONN, const.const_db.CUR = database.connection.connect_to_db()
            logger.info("Successfully connected to database.")
    except Exception as e:
        logger.error(f"Failed to connect to DB: {str(e)}")
        raise

@retry_on_error(retries=3, delay=5)
@log_function_call(logger)
def logout():
    """
    Disconnects from 3X-UI and the local DB.
    """
    try:
        database.connection.disconnect_from_db(const.const_db.CONN, const.const_db.TUNNEL)
        logger.info("Successfully disconnected from all services.")
    except Exception as e:
        logger.error(f"Failed to disconnect: {str(e)}")
        raise
