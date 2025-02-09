# logging_utils.py

import logging
import logging.handlers
import os
from functools import wraps
from typing import Callable, Any
import time
from datetime import datetime


class LogColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


LOGGER_PRESET = "[tg_id={chat_id}, user={username}]"

class ColoredFormatter(logging.Formatter):
    LEVEL_COLORS = {
        "DEBUG": LogColors.OKBLUE,
        "INFO": LogColors.OKGREEN,
        "WARNING": LogColors.WARNING,
        "ERROR": LogColors.FAIL,
        "CRITICAL": LogColors.BOLD + LogColors.FAIL,
    }

    def format(self, record):
        # Применяем цвет только к levelname
        level_color = self.LEVEL_COLORS.get(record.levelname, LogColors.ENDC)
        record.levelname = f"{level_color}{record.levelname}{LogColors.ENDC}"
        return super().format(record)

def setup_logger(name: str, log_file: str) -> logging.Logger:
    """
    Creates and configures a logger with file rotation and colored level names in console output.
    """
    os.makedirs('./logs', exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s --> %(message)s'
    )

    file_handler = logging.handlers.RotatingFileHandler(
        f'./logs/{log_file}',
        maxBytes=10485760,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_formatter = ColoredFormatter('%(asctime)s - %(levelname)s - %(name)s --> %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def retry_on_error(retries: int = 3, delay: int = 5) -> Callable:
    """
    Декоратор для повторных попыток выполнения функции при ошибке
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger = logging.getLogger(func.__module__)
                    logger.error(
                        f"Attempt {attempt + 1}/{retries} failed for {func.__name__}: {str(e)}"
                    )
                    if attempt < retries - 1:
                        time.sleep(delay)
            raise last_exception

        return wrapper

    return decorator


class DatabaseConnectionManager:
    """
    Контекстный менеджер для работы с базой данных
    """

    def __init__(self, connect_func, disconnect_func):
        self.connect_func = connect_func
        self.disconnect_func = disconnect_func
        self.logger = logging.getLogger('DatabaseManager')

    def __enter__(self):
        try:
            return self.connect_func()
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.disconnect_func()
        except Exception as e:
            self.logger.error(f"Failed to disconnect from database: {e}")
            raise


def log_function_call(logger: logging.Logger) -> Callable:
    """
    Декоратор для логирования вызовов функций.
    Также извлекает информацию о пользователе из call или message,
    используя LOGGER_PRESET.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Изначально пустая информация
            user_info_str = ""

            # Проверяем, не является ли первый аргумент call (CallbackQuery)
            if args:
                if hasattr(args[0], 'message') and hasattr(args[0].message, 'chat'):
                    chat_id = args[0].message.chat.id
                    username = getattr(args[0].from_user, 'username', None) or "N/A"
                    user_info_str = LOGGER_PRESET.format(chat_id=chat_id, username=username)
                elif hasattr(args[0], 'chat') and hasattr(args[0], 'from_user'):
                    # Или первый аргумент – это message
                    chat_id = args[0].chat.id
                    username = getattr(args[0].from_user, 'username', None) or "N/A"
                    user_info_str = LOGGER_PRESET.format(chat_id=chat_id, username=username)

            # Логируем вход в функцию
            logger.info(f"{LogColors.OKBLUE}\n\n{LogColors.WARNING}{user_info_str}{LogColors.ENDC} {LogColors.OKBLUE}Entered {func.__name__} function.{LogColors.ENDC}")

            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()

                if user_info_str:
                    logger.info(
                        f"{LogColors.OKBLUE}{user_info_str}Function {func.__name__} completed successfully in {duration:.2f} seconds{LogColors.ENDC}"
                    )
                else:
                    logger.info(
                        f"{LogColors.OKBLUE}Function {func.__name__} completed successfully in {duration:.2f} seconds{LogColors.ENDC}"
                    )
                return result

            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()

                if user_info_str:
                    logger.error(
                        f"{LogColors.WARNING}{user_info_str} Function {func.__name__} failed after {duration:.2f} seconds. Error: {str(e)}{LogColors.ENDC}"
                    )
                else:
                    logger.error(
                        f"{LogColors.WARNING}Function {func.__name__} failed after {duration:.2f} seconds. Error: {str(e)}{LogColors.ENDC}"
                    )
                raise

        return wrapper

    return decorator