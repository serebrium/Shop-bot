
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup
from aiogram.filters import Command
from loader import get_dispatcher
from filters import IsAdmin, IsUser

# Создаем роутер для user обработчиков
router = Router()

# Получаем диспетчер
dp = get_dispatcher()

catalog = '🛍️ Каталог'
balance = '💰 Баланс'
cart = '🛒 Корзина'
delivery_status = '🚚 Статус заказа'

settings = '⚙️ Настройка каталога'
orders = '🚚 Заказы'
questions = '❓ Вопросы'

@router.message(IsAdmin(), Command('menu'))
async def admin_menu(message: Message):
    markup = ReplyKeyboardMarkup(selective=True)
    markup.add(settings)
    markup.add(questions, orders)

    await message.answer('Меню', reply_markup=markup)

@router.message(IsUser(), Command('menu'))
async def user_menu(message: Message):
    markup = ReplyKeyboardMarkup(selective=True)
    markup.add(catalog)
    markup.add(balance, cart)
    markup.add(delivery_status)

    await message.answer('Меню', reply_markup=markup)
