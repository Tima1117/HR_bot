"""
Клавиатуры для бота
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_start_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для начала работы"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Продолжить")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_ready_for_interview_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения готовности к интервью"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Готов пройти интервью", callback_data="start_interview")],
            [InlineKeyboardButton(text="Пока не готов", callback_data="not_ready")]
        ]
    )
    return keyboard


def get_answer_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для ответа на вопрос"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Ответить", callback_data="answer_question")]
        ]
    )
    return keyboard


def get_quick_questions_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с быстрыми вопросами"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏰ Когда ждать ответа?", callback_data="q_timing")],
            [InlineKeyboardButton(text="📞 Сообщить о технической проблеме", callback_data="q_contact")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="q_close")]
        ]
    )
    return keyboard

