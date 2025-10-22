# HR Bot - Telegram бот для автоматизации найма

Телеграм-бот для автоматизации процесса скрининга резюме и первичного интервью с кандидатами.

## 📋 Функционал

### Текущая версия (v1.0 - Standalone)
- ✅ Запрос названия вакансии в начале диалога
- ✅ Сбор личных данных кандидата (имя, фамилия, отчество, телефон, город)
- ✅ Загрузка резюме в форматах PDF и DOCX
- ✅ Имитация скрининга резюме с результатом (принят/отклонен)
- ✅ Первичное интервью с ограничением времени на ответ
- ✅ Сохранение ответов кандидата
- ✅ Имитация анализа результатов интервью
- ✅ Уведомления о статусах на каждом этапе

### Заглушки (будут заменены в v2.0)
- 🔄 Сохранение данных в файлы вместо БД
- 🔄 Случайные результаты скрининга вместо анализа нейросетью
- 🔄 Захардкоженные вопросы вместо загрузки из БД
- 🔄 Случайные результаты интервью вместо анализа ответов

## 🚀 Установка и запуск

### Предварительные требования
- Python 3.10 или выше
- Telegram аккаунт для создания бота

### Шаг 1: Создание бота в Telegram

1. Найдите [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям и выберите имя и username для бота
4. Скопируйте токен бота (выглядит как `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Шаг 2: Установка зависимостей

```bash
# Перейдите в директорию проекта
cd /home/timofei/Документы/Cursor/HR_Bot

# Создайте виртуальное окружение
python3 -m venv venv

# Активируйте виртуальное окружение
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
```

### Шаг 3: Настройка

```bash
# Создайте файл .env на основе примера
cp .env.example .env

# Откройте .env и добавьте токен вашего бота
nano .env
```

В файле `.env` замените `your_bot_token_here` на токен, который вы получили от BotFather:
```
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### Шаг 4: Запуск бота

```bash
# Убедитесь, что виртуальное окружение активировано
source venv/bin/activate

# Запустите бота
python main.py
```

Вы должны увидеть сообщение:
```
INFO - Бот запущен!
```

### Шаг 5: Тестирование

1. Найдите вашего бота в Telegram по username
2. Отправьте команду `/start`
3. Следуйте инструкциям бота

## 📁 Структура проекта

```
HR_Bot/
├── main.py              # Точка входа, запуск бота
├── config.py            # Конфигурация (токены, настройки)
├── states.py            # FSM состояния
├── keyboards.py         # Клавиатуры бота
├── handlers.py          # Обработчики команд и сообщений
├── mock_data.py         # Заглушки для БД и бэкенда
├── requirements.txt     # Зависимости Python
├── .env                 # Переменные окружения (не коммитится)
├── .env.example         # Пример файла с переменными
├── .gitignore          # Игнорируемые файлы
└── resumes/            # Папка для сохранения резюме (создается автоматически)
```

## 🔧 Настройка параметров

В файле `config.py` вы можете изменить:

- `INTERVIEW_TIME_LIMIT` - время на ответ в секундах (по умолчанию 60)
- `INTERVIEW_QUESTIONS_COUNT` - количество вопросов (по умолчанию 5)
- `RESUMES_DIR` - папка для сохранения резюме

## 🔌 Интеграция с бэкендом (TODO для v2.0)

### Что нужно будет доработать:

#### 1. Подключение к базе данных
Заменить класс `MockDatabase` в `mock_data.py` на реальные HTTP-запросы к Go API:

**Текущий код (заглушка):**
```python
def save_candidate(self, user_id: int, data: dict) -> bool:
    self.candidates[user_id] = data
    return True
```

**Будущая реализация:**
```python
import aiohttp

async def save_candidate(self, user_id: int, data: dict) -> bool:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f'{BACKEND_URL}/api/candidates',
            json={
                'telegram_id': user_id,
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'middle_name': data.get('middle_name'),
                'phone': data['phone'],
                'city': data['city'],
                'resume_path': data['resume_path']
            },
            headers={'Authorization': f'Bearer {API_TOKEN}'}
        ) as response:
            return response.status == 201
```

#### 2. API endpoints, которые нужно реализовать в Go бэкенде:

| Метод | Endpoint | Описание | Тело запроса |
|-------|----------|----------|--------------|
| POST | `/api/candidates` | Создать кандидата | `{telegram_id, vacancy_name, first_name, last_name, middle_name, phone, city, resume_path}` |
| GET | `/api/screening/{user_id}` | Получить результат скрининга | - |
| GET | `/api/vacancies/{vacancy_name}/questions` | Получить вопросы для вакансии по названию | - |
| POST | `/api/interview/answers` | Сохранить ответ на вопрос | `{user_id, question_id, answer, timestamp}` |
| GET | `/api/interview/{user_id}/result` | Получить результат интервью | - |
| GET | `/api/candidates/{user_id}/status` | Получить статус кандидата | - |

#### 3. Загрузка файлов
Заменить локальное сохранение резюме на загрузку в S3-совместимое хранилище (Яндекс Object Storage):

```python
# Добавить в requirements.txt:
# aioboto3==12.0.0

import aioboto3

async def upload_resume_to_s3(file_path: str, user_id: int) -> str:
    """Загрузить резюме в Яндекс Object Storage"""
    session = aioboto3.Session()
    async with session.client(
        's3',
        endpoint_url='https://storage.yandexcloud.net',
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY
    ) as s3:
        object_name = f'resumes/{user_id}/{file_path.split("/")[-1]}'
        await s3.upload_file(file_path, S3_BUCKET, object_name)
        return f'{S3_BUCKET_URL}/{object_name}'
```

#### 4. Webhooks вместо Polling (для продакшена)
Для деплоя на Яндекс.Облаке рекомендуется использовать webhooks вместо long polling:

```python
# В main.py заменить:
# await dp.start_polling(bot)

# На:
from aiohttp import web

async def handle_webhook(request):
    update = await request.json()
    await dp.feed_update(bot, Update(**update))
    return web.Response()

app = web.Application()
app.router.add_post('/webhook', handle_webhook)

# При старте установить webhook:
await bot.set_webhook(f'{WEBHOOK_URL}/webhook')
web.run_app(app, host='0.0.0.0', port=8080)
```

#### 5. Триггеры от бэкенда
Добавить endpoint для получения триггеров от бэкенда:

```python
# Endpoint для получения уведомлений от бэкенда
@app.route('/api/notify', methods=['POST'])
async def backend_notify(request):
    data = await request.json()
    user_id = data['telegram_id']
    event_type = data['event_type']  # 'screening_complete', 'interview_result'
    
    if event_type == 'screening_complete':
        # Отправить кандидату результат скрининга
        await send_screening_result(user_id, data['result'])
    elif event_type == 'interview_result':
        # Отправить результат интервью
        await send_interview_result(user_id, data['result'])
    
    return web.Response(status=200)
```

#### 6. Переменные окружения для продакшена
Добавить в `.env`:
```env
# Backend API
BACKEND_URL=https://api.yourcompany.ru
API_TOKEN=your_api_token

# Webhook
WEBHOOK_URL=https://bot.yourcompany.ru

# S3 Storage
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key
S3_BUCKET=hr-bot-resumes
S3_BUCKET_URL=https://storage.yandexcloud.net/hr-bot-resumes
```

## 🚢 Деплой на Яндекс.Облаке

### Вариант 1: Yandex Compute Cloud (VM)

```bash
# 1. Создайте VM в Яндекс.Облаке
# 2. Подключитесь по SSH
# 3. Установите необходимое ПО:

sudo apt update
sudo apt install python3.10 python3-pip python3-venv nginx -y

# 4. Скопируйте проект и настройте
git clone <your-repo-url>
cd HR_Bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Настройте systemd сервис (создайте /etc/systemd/system/hrbot.service):
[Unit]
Description=HR Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/HR_Bot
Environment="PATH=/home/ubuntu/HR_Bot/venv/bin"
ExecStart=/home/ubuntu/HR_Bot/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target

# 6. Запустите сервис:
sudo systemctl enable hrbot
sudo systemctl start hrbot
```

### Вариант 2: Yandex Cloud Functions (serverless)

Для serverless подхода нужно адаптировать код для работы через webhook и Cloud Functions.

## 📝 Команды бота

- `/start` - Начать работу с ботом
- `/cancel` - Отменить текущий процесс

## 🛠 Разработка и отладка

### Просмотр логов
```bash
# Если запущено через systemd:
sudo journalctl -u hrbot -f

# Если запущено вручную - логи выводятся в консоль
```

### Очистка данных для тестирования
```bash
# Удалить сохраненные резюме
rm -rf resumes/*
```

## 🐛 Известные ограничения текущей версии

1. Данные хранятся только в памяти (при перезапуске бота теряются)
2. Резюме сохраняются локально на диск
3. Результаты скрининга и интервью генерируются случайно
4. Нет связи с реальной базой данных и бэкендом
5. Нет аутентификации и авторизации
6. Нет административной панели

Все эти ограничения будут устранены при интеграции с Go бэкендом.

## 📄 Лицензия

MIT

## 👤 Автор

Создано для HR-платформы автоматизации найма

