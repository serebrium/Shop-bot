from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
)
from states import AnswerState
from loader import get_db
from filters import IsAdmin
from keyboards.default.markups import *
from utils.validators import validate_text_input

# Создаем роутер для admin обработчиков
router = Router()

# Получаем базу данных
db = get_db()

# Константы
questions = "❓ Вопросы"


@router.message(IsAdmin(), F.text == questions)
async def process_questions(message: Message):

    questions = db.fetchall("SELECT * FROM questions")

    if len(questions) == 0:
        await message.answer("Вопросов пока нет.")
    else:
        await questions_answer(message, questions)


async def questions_answer(message, questions):
    res = ""

    for question in questions:
        res += f'Вопрос #{question[0]}\n\n{question[1]}\n\n{"="*50}\n\n'

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Ответить", callback_data=f"question_answer_{question[0]}"
                )
            ]
        ]
    )

    await message.answer(res, reply_markup=markup)


@router.callback_query(IsAdmin(), F.data.startswith("question_answer_"))
async def process_answer(query: CallbackQuery, state: FSMContext):

    if query.data is None:
        return
        
    try:
        question_id = int(query.data.split("_")[-1])
    except (ValueError, IndexError):
        await query.answer("Некорректные данные")
        return

    await state.update_data(question_id=question_id)
    await state.set(AnswerState.answer)

    if query.message:
        await query.message.answer("Введите ответ на вопрос:")
    await query.answer()


@router.message(IsAdmin(), AnswerState.answer)
async def process_submit(message: Message, state: FSMContext):

    data = await state.get_data()
    answer = validate_text_input(message.text, max_length=1000)
    if not answer:
        await message.answer("Ответ некорректный (до 1000 символов)")
        return

    await state.update_data(answer=answer)
    await state.set(AnswerState.submit)

    await message.answer(f"Ответ: {answer}\n\nОтправить?", reply_markup=submit_markup())


@router.message(IsAdmin(), F.text == cancel_message, AnswerState.submit)
async def process_cancel_answer(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено!", reply_markup=ReplyKeyboardRemove())


@router.message(IsAdmin(), F.text == all_right_message, AnswerState.submit)
async def process_send_answer(message: Message, state: FSMContext):

    data = await state.get_data()
    question_id = data["question_id"]
    answer = data["answer"]

    # Здесь должна быть логика отправки ответа пользователю
    # Пока просто удаляем вопрос из базы
    db.query("DELETE FROM questions WHERE id=?", (question_id,))

    await state.clear()
    await message.answer("Ответ отправлен!", reply_markup=ReplyKeyboardRemove())
