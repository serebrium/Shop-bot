
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ContentType, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters.callback_data import CallbackData
from aiogram import F
from keyboards.default.markups import *
from states import ProductState, CategoryState
from aiogram.types import ChatAction
from handlers.user.menu import settings
from loader import get_dispatcher, db, get_bot
from filters import IsAdmin
from hashlib import md5

# Получаем диспетчер
dp = get_dispatcher()
bot = get_bot()


category_cb = CallbackData('category', 'id', 'action')
product_cb = CallbackData('product', 'id', 'action')

add_product = '➕ Добавить товар'
delete_category = '🗑️ Удалить категорию'


@dp.message(IsAdmin(), F.text == settings)
async def process_settings(message: Message):

    markup = InlineKeyboardMarkup(inline_keyboard=[])

    for idx, title in db.fetchall('SELECT * FROM categories'):
        markup.inline_keyboard.append([
            InlineKeyboardButton(
                text=title, callback_data=category_cb.new(id=idx, action='view'))
        ])

    markup.inline_keyboard.append([
        InlineKeyboardButton(
            text='+ Добавить категорию', callback_data='add_category')
    ])

    await message.answer('Настройка категорий:', reply_markup=markup)


@dp.callback_query(IsAdmin(), category_cb.filter(action='view'))
async def category_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):

    category_idx = callback_data['id']

    products = db.fetchall('''SELECT * FROM products product
    WHERE product.tag = (SELECT title FROM categories WHERE idx=?)''',
                           (category_idx,))

    await query.message.delete()
    await query.answer('Все добавленные товары в эту категорию.')
    await state.update_data(category_index=category_idx)
    await show_products(query.message, products, category_idx)


# category


@dp.callback_query(IsAdmin(), F.text == 'add_category')
async def add_category_callback_handler(query: CallbackQuery):
    await query.message.delete()
    await query.message.answer('Название категории?')
    await CategoryState.title.set()


@dp.message(IsAdmin(), state=CategoryState.title)
async def set_category_title_handler(message: Message, state: FSMContext):

    category = message.text
    idx = md5(category.encode('utf-8')).hexdigest()
    db.query('INSERT INTO categories VALUES (?, ?)', (idx, category))

    await state.clear()
    await process_settings(message)


@dp.message(IsAdmin(), F.text == delete_category)
async def delete_category_handler(message: Message, state: FSMContext):

    data = await state.get_data()

    if 'category_index' in data.keys():

        idx = data['category_index']

            db.query(
                'DELETE FROM products WHERE tag IN (SELECT title FROM categories WHERE idx=?)', (idx,))
            db.query('DELETE FROM categories WHERE idx=?', (idx,))

            await message.answer('Готово!', reply_markup=ReplyKeyboardRemove())
            await process_settings(message)


# add product


@dp.message(IsAdmin(), F.text == add_product)
async def process_add_product(message: Message):

    await ProductState.title.set()

    markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[cancel_message]])

    await message.answer('Название?', reply_markup=markup)


@dp.message(IsAdmin(), F.text == cancel_message, state=ProductState.title)
async def process_cancel(message: Message, state: FSMContext):

    await message.answer('Ок, отменено!', reply_markup=ReplyKeyboardRemove())
    await state.clear()

    await process_settings(message)


@dp.message(IsAdmin(), F.text == back_message, state=ProductState.title)
async def process_title_back(message: Message, state: FSMContext):
    await process_add_product(message)


@dp.message(IsAdmin(), state=ProductState.title)
async def process_title(message: Message, state: FSMContext):

    data = await state.get_data()
    data['title'] = message.text
    await state.update_data(**data)

    await ProductState.next()
    await message.answer('Описание?', reply_markup=back_markup())


@dp.message(IsAdmin(), F.text == back_message, state=ProductState.body)
async def process_body_back(message: Message, state: FSMContext):

    await ProductState.title.set()

    data = await state.get_data()

    await message.answer(f"Изменить название с <b>{data['title']}</b>?", reply_markup=back_markup())


@dp.message(IsAdmin(), state=ProductState.body)
async def process_body(message: Message, state: FSMContext):

    data = await state.get_data()
    data['body'] = message.text
    await state.update_data(**data)

    await ProductState.next()
    await message.answer('Фото?', reply_markup=back_markup())


@dp.message(IsAdmin(), F.content_type == "photo", state=ProductState.image)
async def process_image_photo(message: Message, state: FSMContext):

    fileID = message.photo[-1].file_id
    file_info = await bot.get_file(fileID)
    downloaded_file = (await bot.download_file(file_info.file_path)).read()

    data = await state.get_data()
    data['image'] = downloaded_file
    await state.update_data(**data)

    await ProductState.next()
    await message.answer('Цена?', reply_markup=back_markup())


@dp.message(IsAdmin(), F.content_type == "text", state=ProductState.image)
async def process_image_url(message: Message, state: FSMContext):

    if message.text == back_message:

        await ProductState.body.set()

        data = await state.get_data()

        await message.answer(f"Изменить описание с <b>{data['body']}</b>?", reply_markup=back_markup())

    else:

        await message.answer('Вам нужно прислать фото товара.')


@dp.message(IsAdmin(), F.text.regex(r"^[^0-9]+$"), state=ProductState.price)
async def process_price_invalid(message: Message, state: FSMContext):

    if message.text == back_message:

        await ProductState.image.set()

        data = await state.get_data()

        await message.answer("Другое изображение?", reply_markup=back_markup())

    else:

        await message.answer('Укажите цену в виде числа!')


@dp.message(IsAdmin(), F.text.regex(r"^[0-9]+$"), state=ProductState.price)
async def process_price(message: Message, state: FSMContext):

    data = await state.get_data()
    data['price'] = message.text
    await state.update_data(**data)

        title = data['title']
        body = data['body']
        price = data['price']

        await ProductState.next()
        text = f'<b>{title}</b>\n\n{body}\n\nЦена: {price} рублей.'

        markup = check_markup()

        await message.answer_photo(photo=data['image'],
                                   caption=text,
                                   reply_markup=markup)


@dp.message(IsAdmin(), F.text.not_in([back_message, all_right_message]), state=ProductState.confirm)
async def process_confirm_invalid(message: Message, state: FSMContext):
    await message.answer('Такого варианта не было.')


@dp.message(IsAdmin(), F.text == back_message, state=ProductState.confirm)
async def process_confirm_back(message: Message, state: FSMContext):

    await ProductState.price.set()

    data = await state.get_data()

    await message.answer(f"Изменить цену с <b>{data['price']}</b>?", reply_markup=back_markup())


@dp.message(IsAdmin(), F.text == all_right_message, state=ProductState.confirm)
async def process_confirm(message: Message, state: FSMContext):

    data = await state.get_data()

    title = data['title']
    body = data['body']
    image = data['image']
    price = data['price']

    tag = db.fetchone(
        'SELECT title FROM categories WHERE idx=?', (data['category_index'],))[0]
    idx = md5(' '.join([title, body, price, tag]
                       ).encode('utf-8')).hexdigest()

    db.query('INSERT INTO products VALUES (?, ?, ?, ?, ?, ?)',
             (idx, title, body, image, int(price), tag))

    await state.clear()
    await message.answer('Готово!', reply_markup=ReplyKeyboardRemove())
    await process_settings(message)


# delete product


@dp.callback_query(IsAdmin(), product_cb.filter(action='delete'))
async def delete_product_callback_handler(query: CallbackQuery, callback_data: dict):

    product_idx = callback_data['id']
    db.query('DELETE FROM products WHERE idx=?', (product_idx,))
    await query.answer('Удалено!')
    await query.message.delete()


async def show_products(m, products, category_idx):

    await bot.send_chat_action(m.chat.id, "typing")

    for idx, title, body, image, price, tag in products:

        text = f'<b>{title}</b>\n\n{body}\n\nЦена: {price} рублей.'

        markup = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text='🗑️ Удалить', callback_data=product_cb.new(id=idx, action='delete'))
        ]])

        await m.answer_photo(photo=image,
                             caption=text,
                             reply_markup=markup)

    markup = ReplyKeyboardMarkup(keyboard=[[add_product], [delete_category]])

    await m.answer('Хотите что-нибудь добавить или удалить?', reply_markup=markup)
