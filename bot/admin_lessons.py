# bot/admin_lessons.py
import datetime
from telebot import types
from bot.bot import bot
from database.lessons import add_lesson
from utils.config import BOT_ADMIN_IDS
from utils.logging_utils import log_function_call, setup_logger

logger = setup_logger('admin_lessons', 'bot.log')

# Словарь для хранения текущего состояния добавления занятия для каждого администратора.
# Ключ – chat_id, значение – словарь вида:
# { "step": <текущий шаг>, "data": { "title": ..., "type": ..., "date": ..., "time": ..., "place": ..., "description": ... } }
admin_lesson_states = {}

# Последовательность шагов: title, type, date, time, place, description.
STEPS = ["title", "type", "date", "time", "place", "description"]

@log_function_call(logger)
@bot.message_handler(commands=['addlesson'])
async def start_add_lesson(message):
    """
    Обработчик команды /addlesson.
    Проверяет, является ли пользователь администратором, и инициализирует процесс добавления занятия.
    """
    chat_id = message.chat.id
    if message.from_user.id not in BOT_ADMIN_IDS:
        await bot.send_message(chat_id, "У вас нет прав для выполнения этой команды.")
        return

    admin_lesson_states[chat_id] = {"step": "title", "data": {}}
    await bot.send_message(chat_id, "Введите название занятия:")

@bot.message_handler(func=lambda message: message.chat.id in admin_lesson_states)
@log_function_call(logger)
async def process_lesson_input(message):
    """
    Обрабатывает ввод администратора для добавления занятия по шагам.
    """
    chat_id = message.chat.id
    state = admin_lesson_states.get(chat_id)
    if not state:
        return  # Если по какой-то причине состояние не найдено, ничего не делаем

    current_step = state.get("step")
    text = message.text.strip()

    if current_step == "title":
        state["data"]["title"] = text
        state["step"] = "type"
        await bot.send_message(chat_id, "Введите тип занятия (категория):")
    elif current_step == "type":
        state["data"]["type"] = text
        state["step"] = "date"
        await bot.send_message(chat_id, "Введите дату занятия в формате ГГГГ-ММ-ДД:")
    elif current_step == "date":
        # Проверка формата даты
        try:
            date_obj = datetime.datetime.strptime(text, "%Y-%m-%d").date()
            state["data"]["date"] = date_obj
            state["step"] = "time"
            await bot.send_message(chat_id, "Введите время занятия в формате ЧЧ:ММ (24-часовой формат):")
        except ValueError:
            await bot.send_message(chat_id, "Неверный формат даты. Пожалуйста, введите дату в формате ГГГГ-ММ-ДД:")
    elif current_step == "time":
        # Проверка формата времени
        try:
            time_obj = datetime.datetime.strptime(text, "%H:%M").time()
            state["data"]["time"] = time_obj
            state["step"] = "place"
            await bot.send_message(chat_id, "Введите место проведения занятия:")
        except ValueError:
            await bot.send_message(chat_id, "Неверный формат времени. Пожалуйста, введите время в формате ЧЧ:ММ:")
    elif current_step == "place":
        state["data"]["place"] = text
        state["step"] = "description"
        await bot.send_message(chat_id, "Введите описание занятия:")
    elif current_step == "description":
        state["data"]["description"] = text
        # Все поля собраны – сохраняем запись в БД.
        data = state["data"]
        try:
            lesson_id = add_lesson(
                data["title"],
                data["type"],
                data["date"],
                data["time"],
                data["place"],
                data["description"]
            )
            await bot.send_message(chat_id, f"Занятие успешно добавлено. ID занятия: {lesson_id}")
        except Exception as e:
            logger.error(f"Error adding lesson: {str(e)}")
            await bot.send_message(chat_id, "Произошла ошибка при добавлении занятия.")
        # Очищаем состояние для данного чата.
        del admin_lesson_states[chat_id]
