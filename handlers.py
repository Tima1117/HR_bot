"""
Бот
Обработчики команд и сообщений бота
"""
import asyncio
import logging
import os
import sys

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from backend_client import get_backend_client
from config import INTERVIEW_TIME_LIMIT, INTERVIEW_QUESTIONS_COUNT, MAX_RESUME_SIZE_BYTES, \
    MAX_RESUME_SIZE_MB, RESUMES_DIR
from keyboards import get_start_keyboard, get_ready_for_interview_keyboard, get_quick_questions_keyboard
from mock_data import mock_db
from s3_service import storage_service
from states import RegistrationStates, InterviewStates
from util import is_valid_phone

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)
router = Router()
backend_client = get_backend_client()


# ==================== КОМАНДЫ ====================

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start"""
    await state.clear()

    start_param = None
    if message.text and len(message.text.split()) > 1:
        start_param = message.text.split()[1]

    if start_param:
        res = await backend_client.get_candidate(message.from_user.id)

        if res:
            await state.update_data(candidate_id=res['id'])
            await message.answer(
                f"👋 С возвращением, {res.get('full_name', 'кандидат')}!\n\n",
                parse_mode="HTML"
            )
            return

        await state.update_data(vacancy_id=start_param)

        answer_text = (
            "👋 Добро пожаловать!\n\n"
            "Я помогу вам пройти процесс отбора.\n\n"
            "📝 Приступим к сбору ваших данных.\n\n"
            "Пожалуйста, введите ваше <b>ФИО</b>:"
        )

        await state.set_state(RegistrationStates.waiting_for_name)
        await message.answer(answer_text, parse_mode="HTML")
    else:
        error_text = (
            "❌ <b>Ошибка</b>\n\n"
            "Для начала работы перейдите по ссылке от рекрутера.\n\n"
            "Обратитесь к HR-специалисту для получения корректной ссылки."
        )
        await message.answer(error_text, parse_mode="HTML")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Отмена текущего процесса"""
    await state.clear()
    await message.answer(
        "❌ Процесс отменен.\n\n"
        "Используйте ссылку от рекрутера, чтобы начать заново.",
        reply_markup=get_start_keyboard()
    )


@router.message(Command("questions"))
async def cmd_questions(message: Message):
    """Часто задаваемые вопросы"""
    await message.answer(
        "❓ <b>Часто задаваемые вопросы</b>\n\n"
        "Выберите интересующий вас вопрос:",
        parse_mode="HTML",
        reply_markup=get_quick_questions_keyboard()
    )


@router.message(Command("resume"))
async def cmd_resume(message: Message, state: FSMContext):
    """Продолжить с места остановки"""
    # Проверяем, есть ли незавершенное интервью
    pending = mock_db.get_pending_interview(message.from_user.id)

    if pending:
        # Есть незавершенное интервью
        candidate_data = pending.get('candidate_data', {})
        await message.answer(
            f"👋 С возвращением!\n\n"
            f"У вас есть незавершенное интервью на вакансию: "
            f"<b>{candidate_data.get('vacancy_name', 'не указана')}</b>\n\n"
            f"Готовы продолжить?",
            parse_mode="HTML",
            reply_markup=get_ready_for_interview_keyboard()
        )
        await state.set_state(InterviewStates.waiting_for_start)
    else:
        # Нет незавершенных интервью
        await message.answer(
            "У вас нет незавершенных интервью.\n\n"
            "Используйте ссылку от рекрутера, чтобы начать новое интервью.",
        )


# ==================== РЕГИСТРАЦИЯ ====================

@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Обработка отчества"""
    name = None if message.text == "-" else message.text
    await state.update_data(name=name)
    await state.set_state(RegistrationStates.waiting_for_phone)
    await message.answer(
        "✅ Принято!\n\n"
        "Введите ваш <b>номер телефона</b> (например: +79991234567):",
        parse_mode="HTML"
    )


@router.message(RegistrationStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    """Обработка номера телефона"""
    phone = message.text.strip()

    if not is_valid_phone(phone):
        await message.answer(
            "❌ <b>Неверный формат номера телефона!</b>\n\n"
            "Пожалуйста, введите номер в одном из форматов:\n"
            "• +79991234567\n"
            "Номер должен содержать 11 цифр после кода страны.",
            parse_mode="HTML"
        )
        return

    await state.update_data(phone=phone)

    telegram_username = message.from_user.username

    if telegram_username:
        await state.update_data(telegram_username=f"@{telegram_username}")
        await state.set_state(RegistrationStates.waiting_for_city)
        await message.answer(
            "✅ Принято!\n\n"
            "Введите ваш <b>город проживания</b>:",
            parse_mode="HTML"
        )
    else:
        await state.set_state(RegistrationStates.waiting_for_telegram_username)
        await message.answer(
            "✅ Принято!\n\n"
            "Пожалуйста, введите ваш <b>Telegram username</b> (например: @username):",
            parse_mode="HTML"
        )


@router.message(RegistrationStates.waiting_for_telegram_username)
async def process_telegram_username(message: Message, state: FSMContext):
    """Обработка Telegram username"""
    username = message.text.strip()

    # Добавляем @ в начало, если пользователь забыл
    if not username.startswith('@'):
        username = f"@{username}"

    await state.update_data(telegram_username=username)
    await state.set_state(RegistrationStates.waiting_for_city)
    await message.answer(
        "✅ Принято!\n\n"
        "Введите ваш <b>город проживания</b>:",
        parse_mode="HTML"
    )


@router.message(RegistrationStates.waiting_for_city)
async def process_city(message: Message, state: FSMContext):
    """Обработка города"""
    city = message.text.strip()
    await state.update_data(city=city)

    user_data = await state.get_data()
    candidate_data = {
        'telegram_id': message.from_user.id,
        'full_name': user_data.get('name'),
        'phone': user_data.get('phone'),
        'city': city
    }

    try:
        result = await backend_client.create_candidate(candidate_data)

        if result:
            await message.answer(
                "✅ Данные сохранены!\n\n"
                f"📎 Теперь отправьте ваше <b>резюме</b> в формате PDF или DOCX\n"
                f"(максимальный размер: {MAX_RESUME_SIZE_MB} МБ):",
                parse_mode="HTML"
            )
            await state.update_data(candidate_id=result['id'])
            await state.set_state(RegistrationStates.waiting_for_resume)
        else:
            error_msg = result.get('error', 'Unknown error') if result else 'No response'
            status_code = result.get('status_code', 'No status') if result else 'No status'
            logger.error(f"Failed to create candidate. Status: {status_code}, Error: {error_msg}")
            await message.answer("❌ Проблемы с подключением, повторите попытку позже")
            await state.clear()

    except Exception as e:
        logger.error(f"Exception in create_candidate: {e}")
        await message.answer("❌ Проблемы с подключением, повторите попытку позже")
        await state.clear()


@router.message(RegistrationStates.waiting_for_resume, F.document)
async def process_resume(message: Message, state: FSMContext):
    """Обработка резюме"""
    document = message.document

    # Проверяем формат файла
    if not (document.file_name.endswith('.pdf') or document.file_name.endswith('.docx')):
        await message.answer(
            "❌ Пожалуйста, отправьте файл в формате PDF или DOCX"
        )
        return

    # Проверяем размер файла (до 5 МБ)
    if document.file_size > MAX_RESUME_SIZE_BYTES:
        await message.answer(
            f"❌ Файл слишком большой!\n\n"
            f"Максимальный размер резюме: {MAX_RESUME_SIZE_MB} МБ\n"
            f"Размер вашего файла: {document.file_size / (1024 * 1024):.2f} МБ\n\n"
            f"Пожалуйста, уменьшите размер файла и отправьте снова."
        )
        return

    user_data = await state.get_data()
    vacancy_id = user_data["vacancy_id"]
    candidate_id = user_data["candidate_id"]

    # Сохраняем файл локально (временное хранение)
    file_path = os.path.join(RESUMES_DIR, f"{candidate_id}_{vacancy_id}")
    await message.bot.download(document, destination=file_path)

    # Загружаем файл в S3
    s3_key = None
    if storage_service.is_available():
        s3_key = storage_service.upload_file(file_path, candidate_id, vacancy_id)
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Can't delete temp file: {e}")
    else:
        logger.error("S3 unavailable")
        return

    await state.clear()

    # Подтверждение получения данных
    try:
        confirmation = (
            f"✅ Данные приняты!\n\n"
            f"👤 {user_data['name']}\n"
            f"📱 {user_data['phone']}\n"
            f"💬 {user_data.get('telegram_username', 'не указан')}\n"
            f"🏙 {user_data['city']}\n"
            f"📄 {document.file_name}"
        )
        if s3_key:
            confirmation += f"\n\n☁️ Резюме сохранено в облачном хранилище"
        else:
            confirmation += f"\n\n⚠️ Резюме сохранено локально (S3 недоступен)"

        await message.answer(confirmation)
    except Exception as e:
        logger.error(f"Error in s3: {e}")
        await message.answer("❌ Проблемы с подключением, повторите попытку позже")
        return

    # Запуск скрининга
    await backend_client.process_screening(candidate_id, vacancy_id)
    await asyncio.sleep(15)

    # Получаем результат скрининга
    screening_result = await backend_client.get_screening_result(candidate_id, vacancy_id)
    if screening_result:
        if screening_result['passed']:
            # Резюме прошло проверку - предлагаем интервью
            try:
                await message.answer("🎉 Хорошие новости!")
            except:
                pass

            try:
                await message.answer(f"{screening_result['feedback']}")
            except:
                pass

            try:
                await message.answer(
                    f"Приглашаем на интервью!\n"
                    f"Вопросов: {INTERVIEW_QUESTIONS_COUNT}\n"
                    f"Время на ответ: {INTERVIEW_TIME_LIMIT} сек",
                    reply_markup=get_ready_for_interview_keyboard()
                )
                await state.set_state(InterviewStates.waiting_for_start)
            except Exception as e:
                logger.error(f"error in send invitation to an interview: {e}")
                try:
                    await message.answer("Готовы к интервью? Напишите 'да'")
                    await state.set_state(InterviewStates.waiting_for_start)
                except:
                    logger.error("error in send invitation")
        else:
            # Резюме не прошло проверку
            try:
                await message.answer("😔 К сожалению...")
            except:
                pass

            try:
                await message.answer(f"{screening_result['feedback']}\n\nСпасибо за интерес!")
            except:
                pass
    else:
        logger.error(f"Empty in get screening result")
        await message.answer("❌ Проблемы с подключением, повторите попытку позже")


@router.message(RegistrationStates.waiting_for_resume)
async def wrong_resume_format(message: Message):
    """Обработка неправильного формата резюме"""
    await message.answer(
        "❌ Пожалуйста, отправьте файл резюме (PDF или DOCX), а не текст.\n\n"
        "Прикрепите файл через скрепку 📎"
    )


# ==================== ИНТЕРВЬЮ ====================

@router.callback_query(F.data == "start_interview", InterviewStates.waiting_for_start)
async def start_interview(callback: CallbackQuery, state: FSMContext):
    """Начало интервью"""
    await callback.answer()
    await start_interview_process(callback.message, state)


@router.message(F.text.lower().in_(["да", "готов", "готова", "начать"]), InterviewStates.waiting_for_start)
async def start_interview_text(message: Message, state: FSMContext):
    """Начало интервью по текстовой команде (альтернатива кнопке)"""
    await start_interview_process(message, state)


async def start_interview_process(message: Message, state: FSMContext):
    """Общая функция запуска интервью"""
    # Удаляем запись о незавершенном интервью, так как начинаем его проходить
    mock_db.remove_pending_interview(message.from_user.id)

    # Получаем вопросы из "базы данных" (заглушка)
    questions = mock_db.get_interview_questions()

    await state.update_data(
        questions=questions,
        current_question=0,
        answers=[]
    )

    try:
        await message.answer("🎯 Начинаем интервью!")
    except:
        pass

    try:
        await message.answer("Отвечайте текстовыми сообщениями.")
    except:
        pass

    await asyncio.sleep(1)
    await ask_question(message, state)


@router.callback_query(F.data == "not_ready", InterviewStates.waiting_for_start)
async def not_ready_for_interview(callback: CallbackQuery, state: FSMContext):
    """Кандидат не готов к интервью"""
    await callback.answer()

    # Получаем данные кандидата из сохраненных данных
    candidate = mock_db.candidates.get(callback.from_user.id)

    if candidate:
        # Сохраняем информацию о том, что кандидат ожидает прохождения интервью
        mock_db.save_pending_interview(callback.from_user.id, candidate)

    await state.clear()
    await callback.message.edit_text(
        "👌 Хорошо, вы можете пройти интервью позже.\n\n"
        "Когда будете готовы, используйте команду /resume чтобы продолжить."
    )


async def ask_question(message: Message, state: FSMContext):
    """Задать вопрос"""
    data = await state.get_data()
    questions = data['questions']
    current_q = data['current_question']

    if current_q >= len(questions):
        # Все вопросы заданы
        await finish_interview(message, state)
        return

    await state.set_state(InterviewStates.answering_question)

    question_msg = await message.answer(
        f"❓ <b>Вопрос {current_q + 1} из {len(questions)}:</b>\n\n"
        f"{questions[current_q]}\n\n"
        f"⏱ Обратите внимание! У вас {INTERVIEW_TIME_LIMIT} секунд на ответ.",
        parse_mode="HTML"
    )

    await state.update_data(question_time=asyncio.get_event_loop().time())

    # Запускаем таймер
    asyncio.create_task(question_timer(message, state, question_msg.message_id))


async def question_timer(message: Message, state: FSMContext, question_msg_id: int):
    """Таймер для вопроса"""
    await asyncio.sleep(INTERVIEW_TIME_LIMIT)

    current_state = await state.get_state()
    if current_state == InterviewStates.answering_question:
        data = await state.get_data()

        # Проверяем, не ответил ли пользователь за это время
        if len(data.get('answers', [])) == data['current_question']:
            # Время вышло, пропускаем вопрос
            await state.update_data(
                answers=data.get('answers', []) + ["[ПРОПУЩЕН]"],
                current_question=data['current_question'] + 1
            )

            mock_db.save_interview_answer(
                message.from_user.id,
                data['current_question'],
                "[ПРОПУЩЕН - время вышло]"
            )

            await message.answer(
                "⏰ <b>Время вышло!</b>\n\n"
                "Вопрос пропущен. Переходим к следующему...",
                parse_mode="HTML"
            )

            await asyncio.sleep(2)
            await ask_question(message, state)


@router.message(InterviewStates.answering_question)
async def process_answer(message: Message, state: FSMContext):
    """Обработка ответа на вопрос"""
    data = await state.get_data()

    # Проверяем, не истекло ли время
    elapsed = asyncio.get_event_loop().time() - data.get('question_time', 0)

    if elapsed > INTERVIEW_TIME_LIMIT:
        await message.answer(
            "⏰ К сожалению, время на ответ истекло.\n"
            "Этот ответ не будет учтен."
        )
        return

    # Сохраняем ответ
    answers = data.get('answers', [])
    answers.append(message.text)
    current_q = data['current_question']

    # Сохраняем в "базу данных" (заглушка)
    mock_db.save_interview_answer(message.from_user.id, current_q, message.text)

    await state.update_data(
        answers=answers,
        current_question=current_q + 1
    )

    await message.answer(
        "✅ Ответ принят!",
        parse_mode="HTML"
    )

    await asyncio.sleep(1)
    await ask_question(message, state)


async def finish_interview(message: Message, state: FSMContext):
    """Завершение интервью"""
    # Проверяем, не завершено ли уже интервью (защита от дублирования)
    current_state = await state.get_state()
    if current_state == InterviewStates.interview_completed or current_state is None:
        return  # Интервью уже завершено, выходим

    await state.set_state(InterviewStates.interview_completed)

    data = await state.get_data()
    answers = data.get('answers', [])
    answered = sum(1 for a in answers if a != "[ПРОПУЩЕН]")

    await message.answer(
        f"🎊 <b>Интервью завершено!</b>\n\n"
        f"📊 Статистика:\n"
        f"• Всего вопросов: {len(data['questions'])}\n"
        f"• Отвечено: {answered}\n"
        f"• Пропущено: {len(answers) - answered}\n\n"
        f"✅ Все ваши ответы сохранены и отправлены на анализ.\n\n"
        f"⏳ Пожалуйста, подождите результаты проверки...",
        parse_mode="HTML"
    )

    # Имитируем задержку анализа
    await asyncio.sleep(4)

    # Получаем результат интервью (заглушка)
    interview_result = mock_db.get_interview_result(message.from_user.id)

    if interview_result['passed']:
        # Прошел интервью
        await message.answer(
            f"🎉 <b>Поздравляем!</b>\n\n"
            f"{interview_result['feedback']}\n\n"
            f"📧 С вами свяжется наш HR-менеджер для обсуждения следующих шагов.\n\n"
            f"Спасибо за участие!",
            parse_mode="HTML"
        )
    else:
        # Не прошел интервью
        await message.answer(
            f"😔 <b>Результаты интервью</b>\n\n"
            f"{interview_result['feedback']}\n\n"
            f"Мы ценим ваше время и интерес к нашей компании.\n"
            f"Желаем успехов в карьере!",
            parse_mode="HTML"
        )

    await state.clear()


# ==================== БЫСТРЫЕ ВОПРОСЫ ====================

@router.callback_query(F.data == "q_status")
async def answer_status(callback: CallbackQuery):
    """Ответ на вопрос о статусе"""
    await callback.answer()

    # Получаем статус из "базы данных" (заглушка)
    status_data = mock_db.get_candidate_status(callback.from_user.id)

    await callback.message.answer(
        f"📊 <b>Ваш текущий статус:</b>\n\n"
        f"🔹 {status_data['text']}\n\n"
        f"{status_data['description']}\n\n"
        f"Мы уведомим вас о любых изменениях!",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "q_timing")
async def answer_timing(callback: CallbackQuery):
    """Ответ на вопрос о сроках"""
    await callback.answer()

    # Получаем информацию о сроках (заглушка)
    timing_info = mock_db.get_timing_info()

    await callback.message.answer(
        timing_info,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "q_contact")
async def answer_contact(callback: CallbackQuery):
    """Ответ на вопрос о контактах"""
    await callback.answer()

    # Получаем контактную информацию (заглушка)
    contact_info = mock_db.get_contact_info()

    await callback.message.answer(
        contact_info,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "q_close")
async def close_questions(callback: CallbackQuery):
    """Закрыть меню вопросов"""
    await callback.answer("Закрыто")
    try:
        await callback.message.delete()
    except:
        await callback.message.edit_text(
            "Меню закрыто.\n\n"
            "Используйте /questions чтобы открыть снова."
        )
