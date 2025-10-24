# HR Bot - Telegram бот для автоматизации найма

Telegram-бот для автоматизации процесса скрининга резюме и первичного интервью с кандидатами.

## 📋 Функционал

- ✅ Запрос названия вакансии в начале диалога
- ✅ Сбор личных данных кандидата (имя, фамилия, отчество, телефон, Telegram username, город)
- ✅ Автоматическое определение Telegram username или запрос, если отсутствует
- ✅ Загрузка резюме в форматах PDF и DOCX (до 5 МБ)
- ✅ Проверка размера файла резюме
- ✅ Имитация скрининга резюме с результатом (принят/отклонен)
- ✅ Первичное интервью с ограничением времени на ответ
- ✅ Сохранение ответов кандидата
- ✅ Имитация анализа результатов интервью
- ✅ Уведомления о статусах на каждом этапе
- ✅ Система быстрых вопросов (/questions)
- ✅ Возможность продолжить интервью позже через /resume

## ⚙️ Параметры конфигурации

В файле `config.py`:

```python
# Основные настройки
BOT_TOKEN = "ваш_токен_от_BotFather"
ADMIN_ID = "ваш_telegram_id"

# Параметры интервью
INTERVIEW_TIME_LIMIT = 60  # секунды на ответ
INTERVIEW_QUESTIONS_COUNT = 5  # количество вопросов

# Ограничения файлов
MAX_RESUME_SIZE_MB = 5  # максимальный размер резюме в МБ

# Директория для резюме (временно)
RESUMES_DIR = 'resumes'
```

## 🚀 Установка на сервер

### Системные требования
- Python 3.10+
- Linux/Ubuntu (рекомендуется)

### Установка зависимостей

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python и pip
sudo apt install python3.10 python3-pip python3-venv -y

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### Запуск

```bash
# Активация окружения
source venv/bin/activate

# Создание .env файла
echo "BOT_TOKEN=ваш_токен" > .env
echo "ADMIN_ID=ваш_id" >> .env

# Запуск бота
python main.py
```

### Автозапуск через systemd

Создайте файл `/etc/systemd/system/hrbot.service`:

```ini
[Unit]
Description=HR Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/path/to/HR_Bot
Environment="PATH=/path/to/HR_Bot/venv/bin"
ExecStart=/path/to/HR_Bot/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Активация:
```bash
sudo systemctl enable hrbot
sudo systemctl start hrbot
```

## 🔌 API Endpoints для интеграции с бэкендом

### 1. Управление кандидатами

#### `POST /api/candidates`
Создание нового кандидата

**Request Body:**
```json
{
  "telegram_id": 123456789,
  "vacancy_name": "Python Developer",
  "first_name": "Иван",
  "last_name": "Иванов", 
  "middle_name": "Иванович",
  "phone": "+79123456789",
  "telegram_username": "@ivan_ivanov",
  "city": "Москва",
  "resume_path": "resumes/123456789_resume.pdf"
}
```

**Response:**
```json
{
  "success": true,
  "candidate_id": "uuid",
  "message": "Кандидат создан"
}
```

#### `GET /api/candidates/{telegram_id}/status`
Получить статус кандидата

**Response:**
```json
{
  "status": "interview_pending",
  "status_text": "Ожидание интервью",
  "description": "Готовимся к вашему интервью",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:30:00Z"
}
```

### 2. Скрининг резюме

#### `POST /api/screening/process`
Запустить скрининг резюме

**Request Body:**
```json
{
  "candidate_id": "uuid",
  "resume_path": "resumes/123456789_resume.pdf",
  "vacancy_name": "Python Developer"
}
```

#### `GET /api/screening/{candidate_id}/result`
Получить результат скрининга

**Response:**
```json
{
  "passed": true,
  "score": 85,
  "feedback": "Ваше резюме соответствует требованиям",
  "processed_at": "2024-01-01T12:15:00Z"
}
```

### 3. Интервью

#### `GET /api/vacancies/{vacancy_name}/questions`
Получить вопросы для интервью

**Response:**
```json
{
  "questions": [
    {
      "id": 1,
      "text": "Расскажите о своем опыте работы",
      "time_limit": 60,
      "order": 1
    },
    {
      "id": 2, 
      "text": "Какие технологии вы используете?",
      "time_limit": 60,
      "order": 2
    }
  ]
}
```

#### `POST /api/interview/answers`
Сохранить ответ на вопрос

**Request Body:**
```json
{
  "candidate_id": "uuid",
  "question_id": 1,
  "answer": "У меня 5 лет опыта в Python разработке",
  "timestamp": "2024-01-01T12:20:00Z",
  "time_taken": 45
}
```

#### `POST /api/interview/{candidate_id}/complete`
Завершить интервью

**Request Body:**
```json
{
  "candidate_id": "uuid",
  "answers": [
    {
      "question_id": 1,
      "answer": "Ответ 1",
      "time_taken": 45
    }
  ],
  "completed_at": "2024-01-01T12:30:00Z"
}
```

#### `GET /api/interview/{candidate_id}/result`
Получить результат интервью

**Response:**
```json
{
  "passed": true,
  "score": 78,
  "feedback": "Поздравляем! Вы прошли на следующий этап",
  "analyzed_at": "2024-01-01T12:35:00Z"
}
```

### 4. FAQ и информация

#### `GET /api/info/timing`
Получить информацию о сроках

**Response:**
```json
{
  "resume_review_days": "1-2",
  "interview_analysis_days": "2-3", 
  "hr_review_days": "3-5"
}
```

#### `GET /api/info/contact`
Получить контактную информацию

**Response:**
```json
{
  "email": "hr@company.com",
  "phone": "+7 (495) 123-45-67",
  "working_hours": "Пн-Пт, 9:00-18:00 (МСК)"
}
```

## 🔄 Триггеры от бэкенда к боту

### Webhook endpoint для уведомлений

#### `POST /api/bot/notify`
Получить уведомления от бэкенда

**Request Body:**
```json
{
  "telegram_id": 123456789,
  "event_type": "screening_complete",
  "data": {
    "passed": true,
    "score": 85,
    "feedback": "Ваше резюме соответствует требованиям"
  }
}
```

**Возможные event_type:**
- `screening_complete` - скрининг завершен
- `interview_result` - результат интервью готов
- `status_changed` - статус кандидата изменился
- `interview_reminder` - напоминание о незавершенном интервью

### Настройка webhook в боте

В `main.py` замените polling на webhook:

```python
# Вместо:
# await dp.start_polling(bot)

# Используйте:
from aiohttp import web

async def handle_webhook(request):
    update = await request.json()
    await dp.feed_update(bot, Update(**update))
    return web.Response()

app = web.Application()
app.router.add_post('/webhook', handle_webhook)

# Установка webhook
await bot.set_webhook(f'{WEBHOOK_URL}/webhook')
web.run_app(app, host='0.0.0.0', port=8080)
```

## 📝 Команды бота

- `/start` - Начать работу с ботом
- `/resume` - Продолжить незавершенное интервью
- `/questions` - Часто задаваемые вопросы (статус, сроки, контакты)
- `/cancel` - Отменить текущий процесс

## 🛠 Разработка

### Структура проекта
```
HR_Bot/
├── main.py              # Точка входа
├── config.py            # Конфигурация
├── handlers.py          # Обработчики команд
├── states.py            # FSM состояния
├── keyboards.py         # Клавиатуры
├── mock_data.py         # Заглушки (заменить на API)
├── requirements.txt     # Зависимости
└── resumes/            # Временное хранилище
```

### Замена заглушек на API

В файле `mock_data.py` замените методы класса `MockDatabase` на HTTP-запросы к вашим API endpoints.

Пример замены:
```python
import aiohttp

async def save_candidate(self, user_id: int, data: dict) -> bool:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f'{BACKEND_URL}/api/candidates',
            json={
                'telegram_id': user_id,
                'vacancy_name': data['vacancy_name'],
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'middle_name': data.get('middle_name'),
                'phone': data['phone'],
                'telegram_username': data.get('telegram_username'),
                'city': data['city'],
                'resume_path': data['resume_path']
            },
            headers={'Authorization': f'Bearer {API_TOKEN}'}
        ) as response:
            return response.status == 201
```

## 📄 Лицензия

MIT