
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from loader import get_db
from filters import IsUser
from keyboards.default.markups import *

# Создаем роутер для user обработчиков
router = Router()

# Получаем базу данных
db = get_db()

balance = '💰 Баланс'

@router.message(IsUser(), F.text == balance)
async def process_balance(message: Message, state: FSMContext):
    
    cid = message.chat.id
    
    wallet = db.fetchone('SELECT balance FROM wallet WHERE cid = ?', (cid,))
    
    if wallet is None:
        db.query('INSERT INTO wallet VALUES (?, ?)', (cid, 0))
        balance_amount = 0
    else:
        balance_amount = wallet[0]
    
    await message.answer(f'Ваш баланс: {balance_amount} рублей')

