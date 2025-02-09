from telebot.async_telebot import AsyncTeleBot
from utils.logging_utils import setup_logger

from utils.config import BOT_API

logger = setup_logger('bot', 'bot.log')
bot = AsyncTeleBot(BOT_API)

