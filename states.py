"""
Состояния FSM для бота
"""
from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """Состояния для регистрации кандидата"""
    waiting_for_vacancy = State()
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_telegram_username = State()
    waiting_for_city = State()
    waiting_for_resume = State()


class InterviewStates(StatesGroup):
    """Состояния для интервью"""
    waiting_for_start = State()
    answering_question = State()
    interview_completed = State()
    rejected = State()
    passed = State()
