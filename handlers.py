"""
Бот
Обработчики команд и сообщений бота
"""
import asyncio
import os
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.exceptions import TelegramBadRequest

from states import RegistrationStates, InterviewStates
from keyboards import get_start_keyboard, get_ready_for_interview_keyboard, get_quick_questions_keyboard
from mock_data import mock_db
from config import RESUMES_DIR, INTERVIEW_TIME_LIMIT, INTERVIEW_QUESTIONS_COUNT

router = Router()


# ==================== КОМАНДЫ ====================

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start"""
    await state.clear()
    await state.set_state(RegistrationStates.waiting_for_vacancy)
    await message.answer(
        "👋 Добро пожаловать!\n\n"
        "Я помогу вам пройти процесс отбора.\n\n"
        "📋 Для начала укажите <b>название вакансии</b>, на которую вы откликаетесь.\n\n"
        "Введите название вакансии (например: Python-разработчик, HR-менеджер и т.д.):",
        parse_mode="HTML"
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Отмена текущего процесса"""
    await state.clear()
    await message.answer(
        "❌ Процесс отменен.\n\n"
        "Используйте /start чтобы начать заново.",
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


# ==================== РЕГИСТРАЦИЯ ====================

@router.message(RegistrationStates.waiting_for_vacancy)
async def process_vacancy(message: Message, state: FSMContext):
    """Обработка названия вакансии"""
    vacancy_name = message.text.strip()
    await state.update_data(vacancy_name=vacancy_name)
    await state.set_state(RegistrationStates.waiting_for_first_name)
    await message.answer(
        f"✅ Отлично! Вакансия: <b>{vacancy_name}</b>\n\n"
        "📝 Теперь приступим к сбору ваших данных.\n\n"
        "Пожалуйста, введите ваше <b>Имя</b>:",
        parse_mode="HTML"
    )


@router.message(RegistrationStates.waiting_for_first_name)
async def process_first_name(message: Message, state: FSMContext):
    """Обработка имени"""
    await state.update_data(first_name=message.text)
    await state.set_state(RegistrationStates.waiting_for_last_name)
    await message.answer(
        "✅ Принято!\n\n"
        "Теперь введите вашу <b>Фамилию</b>:",
        parse_mode="HTML"
    )


@router.message(RegistrationStates.waiting_for_last_name)
async def process_last_name(message: Message, state: FSMContext):
    """Обработка фамилии"""
    await state.update_data(last_name=message.text)
    await state.set_state(RegistrationStates.waiting_for_middle_name)
    await message.answer(
        "✅ Принято!\n\n"
        "Введите ваше <b>Отчество</b> (или отправьте '-' если нет):",
        parse_mode="HTML"
    )


@router.message(RegistrationStates.waiting_for_middle_name)
async def process_middle_name(message: Message, state: FSMContext):
    """Обработка отчества"""
    middle_name = None if message.text == "-" else message.text
    await state.update_data(middle_name=middle_name)
    await state.set_state(RegistrationStates.waiting_for_phone)
    await message.answer(
        "✅ Принято!\n\n"
        "Введите ваш <b>номер телефона</b> (например: +79991234567):",
        parse_mode="HTML"
    )


@router.message(RegistrationStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    """Обработка номера телефона"""
    # Здесь можно добавить валидацию номера
    await state.update_data(phone=message.text)
    await state.set_state(RegistrationStates.waiting_for_city)
    await message.answer(
        "✅ Принято!\n\n"
        "Введите ваш <b>город проживания</b>:",
        parse_mode="HTML"
    )


@router.message(RegistrationStates.waiting_for_city)
async def process_city(message: Message, state: FSMContext):
    """Обработка города"""
    await state.update_data(city=message.text)
    await state.set_state(RegistrationStates.waiting_for_resume)
    await message.answer(
        "✅ Принято!\n\n"
        "📎 Теперь отправьте ваше <b>резюме</b> в формате PDF или DOCX:",
        parse_mode="HTML"
    )


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
    
    # Сохраняем файл (заглушка, в будущем будет загрузка в S3 или хранилище)
    file_path = os.path.join(RESUMES_DIR, f"{message.from_user.id}_{document.file_name}")
    await message.bot.download(document, destination=file_path)
    
    # Получаем все данные
    user_data = await state.get_data()
    user_data['resume_path'] = file_path
    user_data['user_id'] = message.from_user.id
    user_data['username'] = message.from_user.username
    
    # Сохраняем в "базу данных" (заглушка)
    mock_db.save_candidate(message.from_user.id, user_data)
    
    await state.clear()
    
    # Подтверждение получения данных
    try:
        await message.answer(f"✅ Данные приняты!\n💼 Вакансия: {user_data.get('vacancy_name', 'не указана')}")
    except:
        pass
    
    try:
        await message.answer("🔄 Проверяем резюме...")
    except:
        pass
    
    # Получаем результат скрининга (заглушка)
    await asyncio.sleep(1)
    screening_result = mock_db.get_screening_result(message.from_user.id)
    
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
            print(f"[ERROR] Не удалось отправить приглашение на интервью: {e}")
            # Последняя попытка - без клавиатуры
            try:
                await message.answer("Готовы к интервью? Напишите 'да'")
                await state.set_state(InterviewStates.waiting_for_start)
            except:
                print("[ERROR] Полный отказ отправки сообщений")
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
    await state.clear()
    await callback.message.edit_text(
        "👌 Хорошо, вы можете пройти интервью позже.\n\n"
        "Используйте команду /start когда будете готовы."
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
        f"⏱ У вас {INTERVIEW_TIME_LIMIT} секунд на ответ.",
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

