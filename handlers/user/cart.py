import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
)
from states import CheckoutState
from loader import get_db
from filters import IsUser
from keyboards.default.markups import *
from keyboards.inline.products_from_cart import product_markup

# Создаем роутер для user обработчиков
router = Router()

# Получаем базу данных
db = get_db()

# Константы
cart = "🛒 Корзина"


@router.message(IsUser(), F.text == cart)
async def process_cart(message: Message, state: FSMContext):

    cid = message.chat.id

    cart_products = db.fetchall(
        """SELECT product.idx, product.title, product.price, cart.quantity 
    FROM cart product INNER JOIN cart cart ON product.idx = cart.idx 
    WHERE cart.cid = ?""",
        (cid,),
    )

    if len(cart_products) == 0:
        await message.answer("Корзина пуста!")
    else:
        await message.answer("Корзина:", reply_markup=ReplyKeyboardRemove())

        for idx, title, price, quantity in cart_products:

            markup = product_markup(idx, quantity)

            await message.answer(
                f"<b>{title}</b>\n\nЦена: {price} рублей\nКоличество: {quantity}",
                reply_markup=markup,
            )

        markup = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📦 Оформить заказ")]], resize_keyboard=True
        )

        await message.answer("Хотите оформить заказ?", reply_markup=markup)


@router.callback_query(IsUser(), F.text.startswith("product_"))
async def product_callback_handler(query: CallbackQuery, state: FSMContext):

    if query.message is None:
        return
    
    cid = query.message.chat.id
    callback_data = query.data
    if callback_data is None:
        return
        
    action = callback_data.split("_")[1]
    idx = int(callback_data.split("_")[2])

    if action == "count":
        await query.answer("Количество товара")
        await state.update_data(product_idx=idx)
        await state.set(CheckoutState.count)

        markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="1"), KeyboardButton(text="2"), KeyboardButton(text="3")],
                [KeyboardButton(text="4"), KeyboardButton(text="5"), KeyboardButton(text="6")],
                [KeyboardButton(text="7"), KeyboardButton(text="8"), KeyboardButton(text="9")],
                [KeyboardButton(text=back_message)],
            ],
            resize_keyboard=True,
        )

        if query.message:
            await query.message.answer("Укажите количество:", reply_markup=markup)

    elif action == "increase":
        quantity = db.fetchone(
            "SELECT quantity FROM cart WHERE cid = ? AND idx = ?", (cid, idx)
        )[0]
        db.query(
            "UPDATE cart SET quantity = ? WHERE cid = ? AND idx = ?",
            (quantity + 1, cid, idx),
        )
        await query.answer("Количество увеличено!")

    elif action == "decrease":
        quantity = db.fetchone(
            "SELECT quantity FROM cart WHERE cid = ? AND idx = ?", (cid, idx)
        )[0]
        if quantity <= 1:
            db.query("DELETE FROM cart WHERE cid = ? AND idx = ?", (cid, idx))
            await query.answer("Товар удален из корзины!")
        else:
            db.query(
                "UPDATE cart SET quantity = ? WHERE cid = ? AND idx = ?",
                (quantity - 1, cid, idx),
            )
            await query.answer("Количество уменьшено!")


@router.message(IsUser(), F.text == "📦 Оформить заказ")
async def process_checkout(message: Message, state: FSMContext):

    cid = message.chat.id

    cart_products = db.fetchall(
        """SELECT product.idx, product.title, product.price, cart.quantity 
    FROM cart product INNER JOIN cart cart ON product.idx = cart.idx 
    WHERE cart.cid = ?""",
        (cid,),
    )

    if len(cart_products) == 0:
        await message.answer("Корзина пуста!")
        return

    await checkout(message, state)


async def checkout(message, state):

    cid = message.chat.id

    cart_products = db.fetchall(
        """SELECT product.idx, product.title, product.price, cart.quantity 
    FROM cart product INNER JOIN cart cart ON product.idx = cart.idx 
    WHERE cart.cid = ?""",
        (cid,),
    )

    total_price = sum(price * quantity for _, _, price, quantity in cart_products)

    await state.update_data(total_price=total_price)
    await state.set(CheckoutState.check_cart)

    markup = check_markup()

    await message.answer(
        f"Общая стоимость: {total_price} рублей\n\nПодтвердите заказ:",
        reply_markup=markup,
    )


@router.message(
    IsUser(),
    lambda message: message.text not in [all_right_message, back_message],
    state=CheckoutState.check_cart,
)
async def process_check_cart_invalid(message: Message):
    await message.answer("Такого варианта не было.")


@router.message(IsUser(), F.text == back_message, state=CheckoutState.check_cart)
async def process_check_cart_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Оформление заказа отменено!", reply_markup=ReplyKeyboardRemove()
    )


@router.message(IsUser(), F.text == all_right_message, state=CheckoutState.check_cart)
async def process_check_cart_all_right(message: Message, state: FSMContext):

    await state.set(CheckoutState.name)

    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=back_message)]], resize_keyboard=True)

    await message.answer("Как вас зовут?", reply_markup=markup)


@router.message(IsUser(), F.text == back_message, state=CheckoutState.name)
async def process_name_back(message: Message, state: FSMContext):

    await state.set(CheckoutState.check_cart)

    data = await state.get_data()
    total_price = data["total_price"]

    markup = check_markup()

    await message.answer(
        f"Общая стоимость: {total_price} рублей\n\nПодтвердите заказ:",
        reply_markup=markup,
    )


@router.message(IsUser(), state=CheckoutState.name)
async def process_name(message: Message, state: FSMContext):

    data = await state.get_data()
    data["name"] = message.text
    await state.update_data(**data)

    await state.set(CheckoutState.address)

    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=back_message)]], resize_keyboard=True)

    await message.answer("Укажите адрес доставки:", reply_markup=markup)


@router.message(IsUser(), F.text == back_message, state=CheckoutState.address)
async def process_address_back(message: Message, state: FSMContext):

    await state.set(CheckoutState.name)

    data = await state.get_data()
    name = data["name"]

    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=back_message)]], resize_keyboard=True)

    await message.answer(f"Изменить имя с <b>{name}</b>?", reply_markup=markup)


@router.message(IsUser(), state=CheckoutState.address)
async def process_address(message: Message, state: FSMContext):

    data = await state.get_data()
    data["address"] = message.text
    await state.update_data(**data)

    await state.set(CheckoutState.confirm)

    await confirm(message, state)


async def confirm(message, state):

    data = await state.get_data()
    name = data["name"]
    address = data["address"]

    markup = confirm_markup()

    await message.answer(
        f"Имя: <b>{name}</b>\nАдрес: <b>{address}</b>\n\nВсе верно?",
        reply_markup=markup,
    )


@router.message(
    IsUser(),
    lambda message: message.text not in [confirm_message, back_message],
    state=CheckoutState.confirm,
)
async def process_confirm_invalid(message: Message):
    await message.answer("Такого варианта не было.")


@router.message(IsUser(), F.text == back_message, state=CheckoutState.confirm)
async def process_confirm_back(message: Message, state: FSMContext):

    await state.set(CheckoutState.address)

    data = await state.get_data()
    address = data["address"]

    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=back_message)]], resize_keyboard=True)

    await message.answer(f"Изменить адрес с <b>{address}</b>?", reply_markup=markup)


@router.message(IsUser(), F.text == confirm_message, state=CheckoutState.confirm)
async def process_confirm(message: Message, state: FSMContext):

    data = await state.get_data()
    name = data["name"]
    address = data["address"]
    total_price = data["total_price"]

    cid = message.chat.id

    cart_products = db.fetchall(
        """SELECT product.title, cart.quantity 
    FROM cart product INNER JOIN cart cart ON product.idx = cart.idx 
    WHERE cart.cid = ?""",
        (cid,),
    )

    products_text = ""
    for title, quantity in cart_products:
        products_text += f"{title} x{quantity}\n"

    db.query(
        "INSERT INTO orders VALUES (?, ?, ?, ?)", (cid, name, address, products_text)
    )
    db.query("DELETE FROM cart WHERE cid = ?", (cid,))

    await state.clear()
    await message.answer("Заказ оформлен!", reply_markup=ReplyKeyboardRemove())
