from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from loader import db

category_cb = CallbackData('category', 'id', 'action')


def categories_markup():

    global category_cb
    
    markup = InlineKeyboardMarkup(inline_keyboard=[])
    for idx, title in db.fetchall('SELECT * FROM categories'):
        markup.inline_keyboard.append([
            InlineKeyboardButton(text=title, callback_data=category_cb.new(id=idx, action='view'))
        ])

    return markup
