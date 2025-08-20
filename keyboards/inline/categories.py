from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from loader import get_db

# Получаем базу данных
db = get_db()

def categories_markup():
    """Создает клавиатуру с категориями"""
    markup = InlineKeyboardMarkup(inline_keyboard=[])
    
    categories = db.fetchall('SELECT * FROM categories')
    for idx, title in categories:
        markup.inline_keyboard.append([
            InlineKeyboardButton(text=title, callback_data=f"category_view_{idx}")
        ])

    return markup
