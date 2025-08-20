from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ContentType,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
)
from keyboards.default.markups import *
from states import ProductState, CategoryState
from aiogram.enums import ChatAction
from handlers.user.menu import settings
from loader import get_db, get_bot
from filters import IsAdmin
from hashlib import md5

# Создаем роутер для admin обработчиков
router = Router()

# Получаем базу данных и бота
db = get_db()

# Константы
add_product = "➕ Добавить товар"
delete_category = "🗑️ Удалить категорию"


@router.message(IsAdmin(), F.text == settings)
async def process_settings(message: Message):

    markup = InlineKeyboardMarkup(inline_keyboard=[])

    for idx, title in db.fetchall("SELECT * FROM categories"):
        markup.inline_keyboard.append(
            [InlineKeyboardButton(text=title, callback_data=f"category_view_{idx}")]
        )

    markup.inline_keyboard.append(
        [
            InlineKeyboardButton(
                text="+ Добавить категорию", callback_data="add_category"
            )
        ]
    )

    await message.answer("Настройка категорий:", reply_markup=markup)


@router.callback_query(IsAdmin(), F.data.startswith("category_view_"))
async def category_callback_handler(query: CallbackQuery, state: FSMContext):

    if query.data is None:
        return
        
    category_idx = int(query.data.split("_")[-1])

    products = db.fetchall(
        """SELECT * FROM products product
    WHERE product.tag = (SELECT title FROM categories WHERE idx=?)""",
        (category_idx,),
    )

    if query.message:
        await query.message.delete()
    await query.answer("Все добавленные товары в эту категорию.")
    await state.update_data(category_index=category_idx)
    if query.message:
        await show_products(query.message, products, category_idx)


# category


@router.callback_query(IsAdmin(), F.data == "add_category")
async def add_category_callback_handler(query: CallbackQuery, state: FSMContext):
    if query.message:
        await query.message.delete()
        await query.message.answer("Название категории?")
        await state.set(CategoryState.title)


@router.message(IsAdmin(), state=CategoryState.title)
async def set_category_title_handler(message: Message, state: FSMContext):

    category = message.text
    idx = md5(category.encode("utf-8")).hexdigest()
    db.query("INSERT INTO categories VALUES (?, ?)", (idx, category))

    await state.clear()
    await process_settings(message)


@router.message(IsAdmin(), F.text == delete_category)
async def delete_category_handler(message: Message, state: FSMContext):

    data = await state.get_data()

    if "category_index" in data.keys():

        idx = data["category_index"]

        db.query(
            "DELETE FROM products WHERE tag IN (SELECT title FROM categories WHERE idx=?)",
            (idx,),
        )
        db.query("DELETE FROM categories WHERE idx=?", (idx,))

        await message.answer("Готово!", reply_markup=ReplyKeyboardRemove())
        await process_settings(message)


# add product


@router.message(IsAdmin(), F.text == add_product)
async def process_add_product(message: Message, state: FSMContext):

    await state.set(ProductState.title)

    markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text=cancel_message)]])

    await message.answer("Название?", reply_markup=markup)


@router.message(IsAdmin(), F.text == cancel_message, state=ProductState.title)
async def process_cancel(message: Message, state: FSMContext):

    await message.answer("Ок, отменено!", reply_markup=ReplyKeyboardRemove())
    await state.clear()

    await process_settings(message)


@router.message(IsAdmin(), F.text == back_message, state=ProductState.title)
async def process_title_back(message: Message, state: FSMContext):
    await process_add_product(message)


@router.message(IsAdmin(), state=ProductState.title)
async def process_title(message: Message, state: FSMContext):

    data = await state.get_data()
    data["title"] = message.text
    await state.update_data(**data)

    await state.set(ProductState.body)
    await message.answer("Описание?", reply_markup=back_markup())


@router.message(IsAdmin(), F.text == back_message, state=ProductState.body)
async def process_body_back(message: Message, state: FSMContext):

    await state.set(ProductState.title)

    data = await state.get_data()

    await message.answer(
        f"Изменить название с <b>{data['title']}</b>?", reply_markup=back_markup()
    )


@router.message(IsAdmin(), state=ProductState.body)
async def process_body(message: Message, state: FSMContext):

    data = await state.get_data()
    data["body"] = message.text
    await state.update_data(**data)

    await state.set(ProductState.image)
    await message.answer("Фото?", reply_markup=back_markup())


@router.message(IsAdmin(), F.content_type == "photo", state=ProductState.image)
async def process_image_photo(message: Message, state: FSMContext):

    fileID = message.photo[-1].file_id
    file_info = await get_bot().get_file(fileID)
    downloaded_file = (await get_bot().download_file(file_info.file_path)).read()

    data = await state.get_data()
    data["image"] = downloaded_file
    await state.update_data(**data)

    await ProductState.next()
    await message.answer("Цена?", reply_markup=back_markup())


@router.message(IsAdmin(), F.content_type == "text", state=ProductState.image)
async def process_image_url(message: Message, state: FSMContext):

    if message.text == back_message:

        await state.set(ProductState.body)

        data = await state.get_data()

        await message.answer(
            f"Изменить описание с <b>{data['body']}</b>?", reply_markup=back_markup()
        )

    else:

        await message.answer("Вам нужно прислать фото товара.")


@router.message(IsAdmin(), F.text.regex(r"^[^0-9]+$"), state=ProductState.price)
async def process_price_invalid(message: Message, state: FSMContext):

    if message.text == back_message:

        await state.set(ProductState.image)

        data = await state.get_data()

        await message.answer("Другое изображение?", reply_markup=back_markup())

    else:

        await message.answer("Укажите цену в виде числа!")


@router.message(IsAdmin(), F.text.regex(r"^[0-9]+$"), state=ProductState.price)
async def process_price(message: Message, state: FSMContext):

    data = await state.get_data()
    data["price"] = message.text
    await state.update_data(**data)

    title = data["title"]
    body = data["body"]
    price = data["price"]

    await state.set(ProductState.confirm)
    text = f"<b>{title}</b>\n\n{body}\n\nЦена: {price} рублей."

    markup = check_markup()

    await message.answer_photo(photo=data["image"], caption=text, reply_markup=markup)


@router.message(
    IsAdmin(),
    F.text.not_in([back_message, all_right_message]),
    state=ProductState.confirm,
)
async def process_confirm_invalid(message: Message, state: FSMContext):
    await message.answer("Такого варианта не было.")


@router.message(IsAdmin(), F.text == back_message, state=ProductState.confirm)
async def process_confirm_back(message: Message, state: FSMContext):

    await state.set(ProductState.price)

    data = await state.get_data()

    await message.answer(
        f"Изменить цену с <b>{data['price']}</b>?", reply_markup=back_markup()
    )


@router.message(IsAdmin(), F.text == all_right_message, state=ProductState.confirm)
async def process_confirm(message: Message, state: FSMContext):

    data = await state.get_data()

    title = data["title"]
    body = data["body"]
    image = data["image"]
    price = data["price"]

    tag = db.fetchone(
        "SELECT title FROM categories WHERE idx=?", (data["category_index"],)
    )[0]
    idx = md5(" ".join([title, body, price, tag]).encode("utf-8")).hexdigest()

    db.query(
        "INSERT INTO products VALUES (?, ?, ?, ?, ?, ?)",
        (idx, title, body, image, int(price), tag),
    )

    await state.clear()
    await message.answer("Готово!", reply_markup=ReplyKeyboardRemove())
    await process_settings(message)


# delete product


@router.callback_query(IsAdmin(), F.data.startswith("product_delete_"))
async def delete_product_callback_handler(query: CallbackQuery, state: FSMContext):

    if query.data is None:
        return
        
    product_idx = int(query.data.split("_")[-1])
    db.query("DELETE FROM products WHERE idx=?", (product_idx,))
    await query.answer("Удалено!")
    if query.message:
        await query.message.delete()


async def show_products(m, products, category_idx):
    from loader import get_bot

    bot = get_bot()

    await bot.send_chat_action(m.chat.id, "typing")

    for idx, title, body, image, price, tag in products:

        text = f"<b>{title}</b>\n\n{body}\n\nЦена: {price} рублей."

        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🗑️ Удалить", callback_data=f"product_delete_{idx}"
                    )
                ]
            ]
        )

        await m.answer_photo(photo=image, caption=text, reply_markup=markup)

    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=add_product)], [KeyboardButton(text=delete_category)]])

    await m.answer("Хотите что-нибудь добавить или удалить?", reply_markup=markup)
