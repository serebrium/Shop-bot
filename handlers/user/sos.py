from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from states import SosState
from loader import get_db
from keyboards.default.markups import *

# Создаем роутер для user обработчиков
router = Router()

# Получаем базу данных
db = get_db()


@router.message(Command("sos"))
async def cmd_sos(message: Message, state: FSMContext):
    await message.answer("Опишите вашу проблему:")
    await state.set(SosState.question)


@router.message(SosState.question)
async def process_question(message: Message, state: FSMContext):

    question = message.text
    await state.update_data(question=question)
    await state.set(SosState.submit)

    await message.answer(
        f"Вопрос: {question}\n\nОтправить?", reply_markup=submit_markup()
    )


@router.message(
    F.text.not_in([cancel_message, all_right_message]),
    SosState.submit,
)
async def process_price_invalid(message: Message):
    await message.answer("Такого варианта не было.")


@router.message(F.text == cancel_message, SosState.submit)
async def process_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено!", reply_markup=ReplyKeyboardRemove())


@router.message(F.text == all_right_message, SosState.submit)
async def process_submit(message: Message, state: FSMContext):

    data = await state.get_data()
    question = data["question"]
    cid = message.chat.id

    db.query("INSERT INTO questions VALUES (?, ?)", (cid, question))

    await state.clear()
    await message.answer("Вопрос отправлен!", reply_markup=ReplyKeyboardRemove())
