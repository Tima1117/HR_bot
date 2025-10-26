"""
Клиент для взаимодействия с бэкенд API на Go
"""
import asyncio
import logging
import os
import uuid
from typing import Dict, Any, Optional

import aiohttp

logger = logging.getLogger(__name__)


class BackendClient:
    """Клиент для работы с бэкенд API"""

    def __init__(self, base_url: str):
        """
        Инициализация клиента

        Args:
            base_url: Базовый URL бэкенд API
        """
        self.base_url = base_url.rstrip('/')

    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict[str, Any]]:
        """
        Базовый метод для выполнения HTTP запросов

        Args:
            method: HTTP метод (GET, POST, PUT, DELETE)
            endpoint: Эндпоинт API
            data: Данные для отправки

        Returns:
            Ответ от API или None в случае ошибки
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                        method=method,
                        url=url,
                        json=data,
                        timeout=aiohttp.ClientTimeout(total=10),
                        ssl=False,
                ) as response:
                    if response.status == 200 or response.status == 201:
                        return await response.json()
                    elif response.status == 204:
                        return {}  # No content
                    else:
                        error_text = await response.text()
                        logger.error(f"API error {response.status}: {error_text}")
                        return None

        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error: {e}")
            return None
        except asyncio.TimeoutError:
            logger.error("API request timeout")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in API request: {e}")
            return None

    # ==================== КАНДИДАТ ====================

    async def get_candidate(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        return await self._make_request('GET', f'/api/v1/candidates/by-tg-id/{telegram_id}')

    async def create_candidate(self, candidate_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        api_data = {
            'telegram_id': candidate_data.get('telegram_id'),
            'full_name': candidate_data.get('full_name'),
            'phone': candidate_data.get('phone'),
            'city': candidate_data.get('city')
        }
        api_data = {k: v for k, v in api_data.items() if v is not None}
        return await self._make_request('POST', '/api/v1/candidate', api_data)

    # ==================== СКРИНИНГ РЕЗЮМЕ ====================

    async def process_screening(self, candidate_id: int, vacancy_id: uuid) -> Optional[Dict[str, Any]]:
        api_data = {
            'candidate_id': candidate_id,
            'vacancy_id': vacancy_id,
        }
        api_data = {k: v for k, v in api_data.items() if v is not None}
        return await self._make_request('POST', f'/api/v1/screening/process', api_data)

    async def get_screening_result(self, candidate_id: int, vacancy_id: uuid) -> Optional[Dict[str, Any]]:
        return await self._make_request('GET', f'/api/v1/screening/result/{candidate_id}/{vacancy_id}')

    # ==================== ИНТЕРВЬЮ ====================

    # ==================== СТАТУСЫ И УВЕДОМЛЕНИЯ ====================

    # ==================== ФАЙЛЫ И РЕЗЮМЕ ====================


# Синглтон экземпляр клиента
_backend_client = None


def get_backend_client() -> BackendClient:
    """
    Получение экземпляра клиента бэкенда

    Returns:
        Экземпляр BackendClient
    """
    global _backend_client

    if _backend_client is None:
        base_url = os.getenv('BACKEND_BASE_URL')

        _backend_client = BackendClient(base_url)
        logger.info(f"Backend client initialized with base URL: {base_url}")

    return _backend_client
