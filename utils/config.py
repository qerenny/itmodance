import os
import json
from dotenv import load_dotenv # type: ignore

load_dotenv()

BOT_TG_ID = os.getenv('BOT_TG_ID')
BOT_API = os.getenv('BOT_API')
BOT_TEST_PROVIDER_TOKEN = os.getenv('BOT_TEST_PROVIDER_TOKEN')
BOT_LIVE_PROVIDER_TOKEN = os.getenv('BOT_LIVE_PROVIDER_TOKEN')
BOT_ADMIN_IDS = json.loads(os.getenv('BOT_ADMIN_IDS'))

DB_PORT = int(os.getenv('DB_PORT'))
DB_NAME = os.getenv('DB_NAME')
DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')