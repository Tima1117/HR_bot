"""
Конфигурация бота
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота от BotFather
BOT_TOKEN = os.getenv('BOT_TOKEN')

# ID администратора (опционально)
ADMIN_ID = os.getenv('ADMIN_ID')

# Параметры интервью
INTERVIEW_TIME_LIMIT = 60  # секунды на ответ
INTERVIEW_QUESTIONS_COUNT = 5  # количество вопросов

# Директория для сохранения резюме (заглушка, потом будет БД)
RESUMES_DIR = 'resumes'

# Ограничения на файлы
MAX_RESUME_SIZE_MB = 5  # Максимальный размер резюме в МБ
MAX_RESUME_SIZE_BYTES = MAX_RESUME_SIZE_MB * 1024 * 1024  # В байтах

# Создаем директорию, если не существует
os.makedirs(RESUMES_DIR, exist_ok=True)