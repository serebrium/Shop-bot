from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from loader import get_dispatcher
from filters import IsAdmin, IsUser

# Создаем роутер для user обработчиков
router = Router()

# Получаем диспетчер
dp = get_dispatcher()

catalog = "🛍️ Каталог"
balance = "💰 Баланс"
cart = "🛒 Корзина"
delivery_status = "🚚 Статус заказа"

settings = "⚙️ Настройка каталога"
orders = "🚚 Заказы"
questions = "❓ Вопросы"


@router.message(IsAdmin(), Command("menu"))
async def admin_menu(message: Message):
    markup = ReplyKeyboardMarkup(
        selective=True,
        keyboard=[
            [KeyboardButton(text=settings)],
            [KeyboardButton(text=questions), KeyboardButton(text=orders)]
        ]
    )

    await message.answer("Меню", reply_markup=markup)


@router.message(IsUser(), Command("menu"))
async def user_menu(message: Message):
    markup = ReplyKeyboardMarkup(
        selective=True,
        keyboard=[
            [KeyboardButton(text=catalog)],
            [KeyboardButton(text=balance), KeyboardButton(text=cart)],
            [KeyboardButton(text=delivery_status)]
        ]
    )

    await message.answer("Меню", reply_markup=markup)
