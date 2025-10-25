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

# Директория для временного сохранения резюме
RESUMES_DIR = 'resumes'

# Ограничения на файлы
MAX_RESUME_SIZE_MB = 5  # Максимальный размер резюме в МБ
MAX_RESUME_SIZE_BYTES = MAX_RESUME_SIZE_MB * 1024 * 1024  # В байтах

# Настройки Yandex Object Storage (S3-совместимое API)
YC_ACCESS_KEY_ID = os.getenv('YC_ACCESS_KEY_ID')
YC_SECRET_ACCESS_KEY = os.getenv('YC_SECRET_ACCESS_KEY')
YC_REGION = os.getenv('YC_REGION', 'ru-central1')
YC_BUCKET_NAME = os.getenv('YC_BUCKET_NAME')
YC_ENDPOINT_URL = os.getenv('YC_ENDPOINT_URL')

# Создаем директорию для временных файлов, если не существует
os.makedirs(RESUMES_DIR, exist_ok=True)