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
from config import INTERVIEW_QUESTIONS_COUNT, MAX_RESUME_SIZE_BYTES, \
    MAX_RESUME_SIZE_MB, RESUMES_DIR
from keyboards import get_ready_for_interview_keyboard, get_quick_questions_keyboard
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
            await state.update_data(
                candidate_id=res['id'],
                vacancy_id=start_param,
            )
            await cmd_resume(message, state)
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
    try:
        # Получаем данные из состояния
        data = await state.get_data()
        vacancy_id = data.get("vacancy_id")
        candidate_id = data.get("candidate_id")

        # Если нет данных в состоянии, пытаемся найти кандидата
        if not candidate_id:
            candidate_data = await backend_client.get_candidate(message.from_user.id)
            if candidate_data:
                candidate_id = candidate_data['id']
                await state.update_data(
                    candidate_id=candidate_id,
                    vacancy_id=vacancy_id
                )

        # Если все еще нет candidate_id или vacancy_id, значит нет активного интервью
        if not candidate_id or not vacancy_id:
            await message.answer(
                "У вас нет активных интервью.\n\n"
                "Используйте ссылку от рекрутера, чтобы начать новое интервью.",
            )
            return

        # Проверяем статус скрининга
        meta = await backend_client.get_screening_status(candidate_id, vacancy_id)

        if not meta:
            await message.answer(
                "❌ Не удалось получить информацию о вашем интервью.\n\n"
                "Пожалуйста, используйте ссылку от рекрутера для начала нового интервью.",
            )
            return

        status = meta.get('status', '')

        # Обрабатываем все возможные статусы
        if status == "screening_ok":
            # Скрининг пройден, можно начинать интервью
            await message.answer(
                f"👋 С возвращением!\n\n"
                f"Вы прошли скрининг резюме.\n"
                f"Готовы начать интервью?",
                parse_mode="HTML",
                reply_markup=get_ready_for_interview_keyboard()
            )
            await state.set_state(InterviewStates.waiting_for_start)

        elif status == "screening_failed":
            # Скрининг не пройден
            await message.answer(
                "😔 К сожалению, вы не прошли этап скрининга резюме.\n\n"
                "Для участия в других вакансиях используйте новую ссылку от рекрутера.",
            )
        elif status == "interview_ok":
            # Интервью пройдено успешно
            await message.answer(
                f"🎉 Поздравляем! Вы успешно прошли интервью!\n\n"
                f"📧 С вами свяжется наш HR-менеджер для обсуждения следующих шагов.",
                parse_mode="HTML"
            )
        elif status == "interview_failed":
            # Интервью не пройдено
            await message.answer(
                f"😔 К сожалению, вы не прошли интервью.\n\n"
                f"Мы ценим ваше время и интерес к нашей компании.\n"
                f"Желаем успехов в поиске работы!",
                parse_mode="HTML"
            )

        else:
            # Неизвестный статус или процесс еще не начат
            await message.answer(
                "У вас нет активных интервью.\n\n"
                "Используйте ссылку от рекрутера, чтобы начать новый процесс отбора.",
            )
    except Exception as e:
        logger.error(f"Error in /resume command: {e}")
        await message.answer(
            "❌ Произошла ошибка при проверке статуса интервью.\n\n"
            "Пожалуйста, попробуйте позже или используйте ссылку от рекрутера для нового интервью.",
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
                f"📎 Теперь отправьте ваше <b>резюме</b> в формате PDF\n"
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

    except Exception as e:
        logger.error(f"Exception in create_candidate: {e}")
        await message.answer("❌ Проблемы с подключением, повторите попытку позже")


@router.message(RegistrationStates.waiting_for_resume, F.document)
async def process_resume(message: Message, state: FSMContext):
    """Обработка резюме"""
    document = message.document

    # Проверяем формат файла
    if not (document.file_name.endswith('.pdf')):
        await message.answer(
            "❌ Пожалуйста, отправьте файл в формате PDF"
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

    # Получаем результат скрининга
    screening_result = await backend_client.get_screening_status(candidate_id, vacancy_id)
    if screening_result:
        if screening_result['status'] == "screening_ok":
            # Резюме прошло проверку - предлагаем интервью
            try:
                await message.answer("🎉 Хорошие новости!")
            except:
                pass

            try:
                await message.answer(
                    f"Приглашаем на интервью!\n"
                    f"Вопросов: {INTERVIEW_QUESTIONS_COUNT}\n"
                    f"Время на каждый вопрос будет ограничено.",
                    reply_markup=get_ready_for_interview_keyboard()
                )
                await state.set_state(InterviewStates.waiting_for_start)
            except Exception as e:
                logger.error(f"error in send invitation to an interview: {e}")
        else:
            # Резюме не прошло проверку
            try:
                await message.answer("😔 К сожалению вы не подходите для данной вакансии.")
                await state.set_state(InterviewStates.rejected)
            except:
                pass
    else:
        logger.error(f"Empty in get screening result")
        await message.answer("❌ Проблемы с подключением, повторите попытку позже")


@router.message(RegistrationStates.waiting_for_resume)
async def wrong_resume_format(message: Message):
    """Обработка неправильного формата резюме"""
    await message.answer(
        "❌ Пожалуйста, отправьте файл резюме (PDF), а не текст.\n\n"
        "Прикрепите файл через скрепку 📎"
    )


# ==================== ИНТЕРВЬЮ ====================

@router.callback_query(F.data == "start_interview", InterviewStates.waiting_for_start)
async def start_interview(callback: CallbackQuery, state: FSMContext):
    """Начало интервью"""
    await callback.answer()
    await start_interview_process(callback.message, state)


async def start_interview_process(message: Message, state: FSMContext):
    """Общая функция запуска интервью"""
    user_data = await state.get_data()
    vacancy_id = user_data["vacancy_id"]

    questions = await backend_client.get_questions_by_vacancy_id(vacancy_id)

    await state.update_data(
        questions=questions,
        question_num=0,
        answers=[],
        question_start_time=None
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

    await callback.message.edit_text(
        "👌 Хорошо, вы можете пройти интервью позже.\n\n"
        "Когда будете готовы, используйте команду /resume чтобы продолжить."
    )


async def ask_question(message: Message, state: FSMContext):
    """Задать вопрос"""
    data = await state.get_data()
    questions = data['questions']
    question_num = data['question_num']

    if question_num >= len(questions):
        await finish_interview(message, state)
        return

    time_limit = questions[question_num]['time_limit']
    question_start_time = asyncio.get_event_loop().time()

    await state.update_data(
        question=questions[question_num],
        current_time_limit=time_limit,
        question_start_time=question_start_time,
        timer_active=True
    )
    await state.set_state(InterviewStates.answering_question)

    question_msg = await message.answer(
        f"❓ <b>Вопрос {question_num + 1} из {len(questions)}:</b>\n\n"
        f"{questions[question_num]['content']}\n\n"
        f"⏱ Обратите внимание! У вас {time_limit} секунд на ответ.",
        parse_mode="HTML"
    )

    await state.update_data(question_message_id=question_msg.message_id)

    asyncio.create_task(question_timer(message, state, time_limit, question_num))


async def question_timer(message: Message, state: FSMContext, time_limit: int, question_num: int):
    """Таймер для вопроса"""
    await asyncio.sleep(time_limit)

    current_state = await state.get_state()
    if current_state == InterviewStates.answering_question:
        data = await state.get_data()

        # Проверяем, что мы все еще на том же вопросе
        if data.get('question_num') == question_num and data.get('timer_active', True):
            # Время вышло, пропускаем вопрос
            answers = data.get('answers', [])
            # Убедимся, что для этого вопроса еще нет ответа
            if len(answers) <= question_num:
                answers.append("skipped")

                await backend_client.post_answer_by_question_id(
                    data['candidate_id'],
                    data['question']['id'],
                    "skipped",
                    time_limit  # отправляем полное время как затраченное
                )

                await state.update_data(
                    answers=answers,
                    question_num=data['question_num'] + 1,
                    timer_active=False
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

    question_start_time = data.get('question_start_time')
    if not question_start_time:
        await message.answer("❌ Ошибка: время начала вопроса не установлено")
        return

    elapsed = asyncio.get_event_loop().time() - question_start_time
    time_limit = data.get('current_time_limit', 0)

    if elapsed > time_limit:
        await message.answer(
            "⏰ К сожалению, время на ответ истекло.\n"
            "Этот ответ не будет учтен."
        )
        return

    await state.update_data(timer_active=False)

    answers = data.get('answers', [])
    current_q = data['question_num']

    if len(answers) <= current_q:
        answers.append(message.text)
    else:
        answers[current_q] = message.text

    await backend_client.post_answer_by_question_id(
        data['candidate_id'],
        data['question']['id'],
        message.text,
        int(elapsed),
    )

    await state.update_data(
        answers=answers,
        question_num=current_q + 1
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
    questions = data.get('questions', [])

    while len(answers) < len(questions):
        answers.append("skipped")

    answered = sum(1 for a in answers if a != "skipped")

    await message.answer(
        f"🎊 <b>Интервью завершено!</b>\n\n"
        f"📊 Статистика:\n"
        f"• Всего вопросов: {len(questions)}\n"
        f"• Отвечено: {answered}\n"
        f"• Пропущено: {len(answers) - answered}\n\n"
        f"✅ Все ваши ответы сохранены и отправлены на анализ.\n\n"
        f"⏳ Пожалуйста, подождите результаты проверки...",
        parse_mode="HTML"
    )

    candidate_id = data['candidate_id']
    vacancy_id = data['vacancy_id']

    # Получаем результат интервью
    await backend_client.post_update_status(candidate_id, vacancy_id)
    interview_result = await backend_client.get_screening_status(candidate_id, vacancy_id)
    if interview_result['status'] == "interview_ok":
        # Прошел интервью
        await state.set_state(InterviewStates.passed)
        await message.answer(
            f"🎉 <b>Поздравляем!</b>\n\n"
            f"📧 С вами свяжется наш HR-менеджер для обсуждения следующих шагов.\n\n"
            f"Спасибо за участие!",
            parse_mode="HTML"
        )
    else:
        # Не прошел интервью
        await state.set_state(InterviewStates.rejected)
        await message.answer(
            f"😔 <b>К сожалению вы не подходите для данной вакансии.</b>\n\n"
            f"Мы ценим ваше время и интерес к нашей компании.\n"
            f"Желаем успехов в карьере!",
            parse_mode="HTML"
        )


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
