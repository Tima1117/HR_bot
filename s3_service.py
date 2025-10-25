"""
Сервис для работы с Yandex Object Storage (S3-совместимое API)
"""
import os
import uuid
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.client import Config
from config import YC_ACCESS_KEY_ID, YC_SECRET_ACCESS_KEY, YC_REGION, YC_BUCKET_NAME, YC_ENDPOINT_URL


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
            # Проверяем наличие обязательных переменных
            if not all([YC_ACCESS_KEY_ID, YC_SECRET_ACCESS_KEY, YC_BUCKET_NAME]):
                missing = []
                if not YC_ACCESS_KEY_ID: missing.append('YC_ACCESS_KEY_ID')
                if not YC_SECRET_ACCESS_KEY: missing.append('YC_SECRET_ACCESS_KEY')
                if not YC_BUCKET_NAME: missing.append('YC_BUCKET_NAME')
                print(f"[YC STORAGE ERROR] Отсутствуют переменные окружения: {', '.join(missing)}")
                self.s3_client = None
                return
            
            print(f"[YC STORAGE] Инициализация подключения к бакету: {self.bucket_name}")
            
            # Создаем клиент с детальной конфигурацией
            self.s3_client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=YC_ACCESS_KEY_ID,
                aws_secret_access_key=YC_SECRET_ACCESS_KEY,
                region_name=YC_REGION,
                config=Config(
                    s3={'addressing_style': 'virtual'},
                    retries={'max_attempts': 3, 'mode': 'standard'}
                )
            )
            
            # Проверяем подключение
            self._check_connection()
            print(f"[YC STORAGE] Успешно подключен к бакету: {self.bucket_name}")
            
        except NoCredentialsError:
            print("[YC STORAGE ERROR] Не найдены credentials для Yandex Cloud")
            self.s3_client = None
        except Exception as e:
            print(f"[YC STORAGE ERROR] Ошибка инициализации: {str(e)}")
            self.s3_client = None
    
    def _check_connection(self):
        """Проверка подключения к Yandex Object Storage"""
        if not self.s3_client:
            raise Exception("S3 клиент не инициализирован")
        
        try:
            # Проверяем доступность бакета
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"[YC STORAGE] Бакет {self.bucket_name} доступен")
            
            # Дополнительная проверка - список объектов (если есть права)
            try:
                response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, MaxKeys=1)
                print(f"[YC STORAGE] Права на чтение: OK")
            except ClientError as e:
                print(f"[YC STORAGE] Права на чтение: ограничены ({e.response['Error']['Code']})")
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"[YC STORAGE ERROR] Ошибка доступа к бакету: {error_code} - {error_message}")
            
            if error_code == '404':
                print(f"[YC STORAGE ERROR] Бакет '{self.bucket_name}' не найден")
            elif error_code == '403':
                print(f"[YC STORAGE ERROR] Доступ запрещен к бакету '{self.bucket_name}'")
            elif error_code == 'InvalidAccessKeyId':
                print("[YC STORAGE ERROR] Неверный Access Key ID")
            elif error_code == 'SignatureDoesNotMatch':
                print("[YC STORAGE ERROR] Неверная подпись - проверьте Secret Key")
            
            raise
    
    def upload_file(self, file_path: str, user_id: int, original_filename: str) -> str:
        """
        Загрузка файла в Yandex Object Storage
        """
        if not self.s3_client:
            print("[YC STORAGE ERROR] Клиент не инициализирован, загрузка невозможна")
            return None
        
        try:
            # Генерируем уникальное имя файла в хранилище
            file_extension = os.path.splitext(original_filename)[1]
            s3_key = f"resumes/{user_id}/{uuid.uuid4()}{file_extension}"
            
            print(f"[YC STORAGE] Загрузка файла: {original_filename} -> {s3_key}")
            
            # Загружаем файл
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'Metadata': {
                        'user_id': str(user_id),
                        'original_filename': original_filename,
                        'uploaded_via': 'telegram_bot'
                    }
                }
            )
            
            print(f"[YC STORAGE] Файл успешно загружен: {s3_key}")
            return s3_key
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"[YC STORAGE ERROR] Ошибка загрузки файла: {error_code} - {error_message}")
            return None
        except Exception as e:
            print(f"[YC STORAGE ERROR] Неожиданная ошибка при загрузке: {e}")
            return None

    # ... остальные методы без изменений ...
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
            print(f"[YC STORAGE ERROR] Ошибка генерации ссылки: {e}")
            return None
    
    def delete_file(self, s3_key: str) -> bool:
        """Удаление файла из хранилища"""
        if not self.s3_client:
            return False
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            print(f"[YC STORAGE] Файл удален: {s3_key}")
            return True
        except ClientError as e:
            print(f"[YC STORAGE ERROR] Ошибка удаления файла: {e}")
            return False
    
    def is_available(self) -> bool:
        """Проверка доступности Yandex Object Storage"""
        return self.s3_client is not None
    
    def get_public_url(self, s3_key: str) -> str:
        """Получение публичной ссылки на файл"""
        return f"https://{self.bucket_name}.storage.yandexcloud.net/{s3_key}"


# Глобальный экземпляр сервиса
storage_service = YandexStorageService()