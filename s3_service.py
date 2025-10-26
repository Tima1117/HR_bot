"""
Сервис для работы с Yandex Object Storage (S3-совместимое API)
"""
import logging
import sys
import uuid

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError, NoCredentialsError

from config import YC_ACCESS_KEY_ID, YC_SECRET_ACCESS_KEY, YC_BUCKET_NAME, YC_ENDPOINT_URL

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


class YandexStorageService:
    """Сервис для работы с Yandex Object Storage"""

    def __init__(self):
        self.s3_client = None
        self.bucket_name = YC_BUCKET_NAME
        self.endpoint_url = YC_ENDPOINT_URL
        self._initialize_client()

    def _initialize_client(self):
        """Инициализация S3 клиента для Yandex Cloud"""
        try:
            if not all([YC_ACCESS_KEY_ID, YC_SECRET_ACCESS_KEY, YC_BUCKET_NAME]):
                missing = []
                if not YC_ACCESS_KEY_ID: missing.append('YC_ACCESS_KEY_ID')
                if not YC_SECRET_ACCESS_KEY: missing.append('YC_SECRET_ACCESS_KEY')
                if not YC_BUCKET_NAME: missing.append('YC_BUCKET_NAME')
                logger.error(f"Отсутствуют переменные окружения: {', '.join(missing)}")
                self.s3_client = None
                return

            logger.info(f"Инициализация подключения к бакету: {self.bucket_name}")
            self.s3_client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=YC_ACCESS_KEY_ID,
                aws_secret_access_key=YC_SECRET_ACCESS_KEY,
                config=Config(
                    s3={'addressing_style': 'virtual'},
                    retries={'max_attempts': 3, 'mode': 'standard'}
                )
            )

            self._check_connection()
            logger.info(f"Успешно подключен к бакету: {self.bucket_name}")

        except NoCredentialsError:
            logger.error("Не найдены credentials для Yandex Cloud")
            self.s3_client = None
        except Exception as e:
            logger.error(f"Ошибка инициализации: {str(e)}")
            self.s3_client = None

    def _check_connection(self):
        """Проверка подключения к Yandex Object Storage"""
        if not self.s3_client:
            raise Exception("S3 клиент не инициализирован")

        try:
            # Проверяем доступность бакета
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Бакет {self.bucket_name} доступен")

            # Дополнительная проверка - список объектов (если есть права)
            try:
                self.s3_client.list_objects_v2(Bucket=self.bucket_name, MaxKeys=1)
                logger.info(f"Права на чтение: OK")
            except ClientError as e:
                logger.error(f"Права на чтение: ограничены ({e.response['Error']['Code']})")

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Ошибка доступа к бакету: {error_code} - {error_message}")
            raise

    def upload_file(self, file_path: str, tg_id: int, vacancy_id: uuid) -> str:
        """
        Загрузка файла в Yandex Object Storage
        """
        if not self.s3_client:
            logger.error("Клиент не инициализирован, загрузка невозможна")
            return None

        try:
            s3_key = f"{tg_id}/{vacancy_id}"

            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'Metadata': {
                        'uploaded_via': 'telegram_bot'
                    }
                }
            )
            return s3_key

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Ошибка загрузки файла: {error_code} - {error_message}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при загрузке: {e}")
            return None

    def get_file_url(self, s3_key: str, expires_in: int = 3600) -> str:
        """Получение временной ссылки на файл"""
        if not self.s3_client:
            return None
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"Ошибка генерации ссылки: {e}")
            return None

    def delete_file(self, s3_key: str) -> bool:
        """Удаление файла из хранилища"""
        if not self.s3_client:
            return False
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            logger.error(f"Ошибка удаления файла: {e}")
            return False

    def is_available(self) -> bool:
        """Проверка доступности Yandex Object Storage"""
        return self.s3_client is not None

    def get_public_url(self, s3_key: str) -> str:
        """Получение публичной ссылки на файл"""
        return f"https://{self.bucket_name}.storage.yandexcloud.net/{s3_key}"


# Глобальный экземпляр сервиса
storage_service = YandexStorageService()
