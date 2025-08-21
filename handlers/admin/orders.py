from aiogram import Router, F
from aiogram.types import Message
from loader import get_db
from filters import IsAdmin

# Создаем роутер для admin обработчиков
router = Router()

# Получаем базу данных
db = get_db()

orders = "🚚 Заказы"


@router.message(IsAdmin(), F.text == orders)
async def process_orders(message: Message):
    orders = db.fetchall("SELECT * FROM orders")

    if len(orders) == 0:
        await message.answer("Заказов пока нет.")
    else:
        await order_answer(message, orders)


async def order_answer(message, orders):
    res = ""

    for order in orders:
        res += f'Заказ #{order[0]}\n\nПокупатель: {order[1]}\nАдрес: {order[2]}\n\nТовары:\n{order[3]}\n\n{"="*50}\n\n'

    await message.answer(res)
