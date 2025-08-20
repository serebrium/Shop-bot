from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def product_markup(idx='', price=0):
    """Создает клавиатуру для товара в каталоге"""
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='🛒 Добавить в корзину', callback_data=f"product_add_{idx}")
        ]
    ])
    return markup