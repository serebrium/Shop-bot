
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from states import CheckoutState
from loader import get_db
from filters import IsUser
from keyboards.inline.categories import categories_markup
from keyboards.inline.products_from_catalog import product_markup

# Создаем роутер для user обработчиков
router = Router()

# Получаем базу данных
db = get_db()

# Константы
catalog = '🛍️ Каталог'

@router.message(IsUser(), F.text == catalog)
async def process_catalog(message: Message):
    
    await message.answer('Выберите категорию:', reply_markup=categories_markup())


@router.callback_query(IsUser(), F.text.startswith('category_view_'))
async def category_callback_handler(query: CallbackQuery):
    
    category_idx = int(query.text.split('_')[-1])
    
    products = db.fetchall('''SELECT * FROM products product
    WHERE product.tag = (SELECT title FROM categories WHERE idx=?)''',
                           (category_idx,))
    
    await query.message.delete()
    await query.answer('Все товары в этой категории.')
    await show_products(query.message, products)


@router.callback_query(IsUser(), F.text.startswith('product_add_'))
async def add_product_callback_handler(query: CallbackQuery):
    
    product_idx = int(query.text.split('_')[-1])
    cid = query.message.chat.id
    
    db.query('INSERT INTO cart VALUES (?, ?, ?)', (cid, product_idx, 1))
    
    await query.answer('Товар добавлен в корзину!')


async def show_products(m, products):
    
    for idx, title, body, image, price, tag in products:
        
        text = f'<b>{title}</b>\n\n{body}\n\nЦена: {price} рублей.'
        
        markup = product_markup(idx, price)
        
        await m.answer_photo(photo=image,
                             caption=text,
                             reply_markup=markup)
