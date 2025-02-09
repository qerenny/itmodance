#databse/connection.py
from utils.config import API_IP, API_PORT_SSH, API_USERNAME_SSH, API_PRIVATE_KEY_SSH, API_PASSWORD_SSH, DB_NAME, DB_USERNAME, DB_PASSWORD, DB_PORT
import psycopg2
from utils.logging_utils import setup_logger, retry_on_error, log_function_call
from sshtunnel import SSHTunnelForwarder

logger = setup_logger('connection.database', 'database.log')

@retry_on_error(retries=3, delay=5)
@log_function_call(logger)
def connect_to_db():
    """
    Establishes a secure connection to the database via SSH tunnel.
    """
    tunnel = None
    conn = None
    try:
        tunnel = SSHTunnelForwarder(
            (API_IP, API_PORT_SSH),
            ssh_username=API_USERNAME_SSH,
            ssh_private_key=API_PRIVATE_KEY_SSH,
            ssh_private_key_password=API_PASSWORD_SSH,
            remote_bind_address=('localhost', DB_PORT),
            local_bind_address=('localhost', 6349),
        )
        tunnel.start()
        logger.info("SSH tunnel established successfully.")

        conn = psycopg2.connect(
            database=DB_NAME,
            user=DB_USERNAME,
            password=DB_PASSWORD,
            host=tunnel.local_bind_host,
            port=tunnel.local_bind_port,
        )
        conn.autocommit = True

        cur = conn.cursor()
        logger.info("Database connection established successfully.")
        return tunnel, conn, cur

    except Exception as e:
        logger.error(f"Error while connecting to database: {str(e)}")
        if tunnel:
            tunnel.close()
        if conn:
            conn.close()
        raise


@log_function_call(logger)
def disconnect_from_db(conn, tunnel):
    """
    Closes database and SSH tunnel connections safely.
    """
    logger.info("Disconnecting from the database and stopping SSH tunnel.")
    try:
        if conn:
            conn.close()
        if tunnel:
            tunnel.stop()
        logger.info("Database connections closed successfully.")
    except Exception as e:
        logger.error(f"Error while disconnecting from database: {str(e)}")
        raise