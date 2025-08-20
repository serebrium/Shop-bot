from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def product_markup(idx, count):
    """Создает клавиатуру для товара в корзине"""
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='➖', callback_data=f"product_decrease_{idx}"),
            InlineKeyboardButton(text=f'{count}', callback_data=f"product_count_{idx}"),
            InlineKeyboardButton(text='➕', callback_data=f"product_increase_{idx}")
        ]
    ])
    return markup