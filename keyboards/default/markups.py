from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from typing import List

# Константы для сообщений
back_message = "👈 Назад"
confirm_message = "✅ Подтвердить заказ"
all_right_message = "✅ Все верно"
cancel_message = "🚫 Отменить"


def confirm_markup() -> ReplyKeyboardMarkup:
    """Создает клавиатуру для подтверждения заказа"""
    markup = ReplyKeyboardMarkup(
        resize_keyboard=True,
        selective=True,
        keyboard=[
            [KeyboardButton(text=confirm_message)],
            [KeyboardButton(text=back_message)],
        ],
    )
    return markup


def back_markup() -> ReplyKeyboardMarkup:
    """Создает клавиатуру с кнопкой назад"""
    markup = ReplyKeyboardMarkup(
        resize_keyboard=True,
        selective=True,
        keyboard=[[KeyboardButton(text=back_message)]],
    )
    return markup


def check_markup() -> ReplyKeyboardMarkup:
    """Создает клавиатуру для проверки данных"""
    markup = ReplyKeyboardMarkup(
        resize_keyboard=True,
        selective=True,
        keyboard=[
            [KeyboardButton(text=back_message), KeyboardButton(text=all_right_message)]
        ],
    )
    return markup


def submit_markup() -> ReplyKeyboardMarkup:
    """Создает клавиатуру для отправки"""
    markup = ReplyKeyboardMarkup(
        resize_keyboard=True,
        selective=True,
        keyboard=[
            [
                KeyboardButton(text=cancel_message),
                KeyboardButton(text=all_right_message),
            ]
        ],
    )
    return markup


def create_markup_from_list(
    buttons: List[str], row_width: int = 2
) -> ReplyKeyboardMarkup:
    """Создает клавиатуру из списка кнопок"""
    keyboard = []

    for i in range(0, len(buttons), row_width):
        row = buttons[i : i + row_width]
        keyboard.append([KeyboardButton(text=btn) for btn in row])

    return ReplyKeyboardMarkup(resize_keyboard=True, selective=True, keyboard=keyboard)
