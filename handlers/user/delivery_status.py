from aiogram import Router, F
from aiogram.types import Message
from loader import get_db
from filters import IsUser

# Создаем роутер для user обработчиков
router = Router()

# Получаем базу данных
db = get_db()

delivery_status = "🚚 Статус заказа"


@router.message(IsUser(), F.text == delivery_status)
async def process_delivery_status(message: Message):

    cid = message.chat.id

    orders = db.fetchall("SELECT * FROM orders WHERE cid = ?", (cid,))

    if len(orders) == 0:
        await message.answer("У вас нет заказов.")
    else:
        await delivery_status_answer(message, orders)


async def delivery_status_answer(message, orders):
    res = ""

    for order in orders:
        res += f'Заказ #{order[0]}\n\nПокупатель: {order[1]}\nАдрес: {order[2]}\n\nТовары:\n{order[3]}\n\n{"="*50}\n\n'

    await message.answer(res)
