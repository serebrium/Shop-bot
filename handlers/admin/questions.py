
from handlers.user.menu import questions
from aiogram.fsm.context import FSMContext
from aiogram.filters.callback_data import CallbackData
from aiogram import F
from keyboards.default.markups import all_right_message, cancel_message, submit_markup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.types import ChatAction
from states import AnswerState
from loader import get_dispatcher, db, get_bot
from filters import IsAdmin

# Получаем диспетчер
dp = get_dispatcher()
bot = get_bot()


question_cb = CallbackData('question', 'cid', 'action')


@dp.message(IsAdmin(), F.text == questions)
async def process_questions(message: Message):

    await bot.send_chat_action(message.chat.id, "typing")
    questions = db.fetchall('SELECT * FROM questions')

    if len(questions) == 0:

        await message.answer('Нет вопросов.')

    else:

        for cid, question in questions:

                    markup = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text='Ответить', callback_data=question_cb.new(cid=cid, action='answer'))
        ]])

            await message.answer(question, reply_markup=markup)


@dp.callback_query(IsAdmin(), question_cb.filter(action='answer'))
async def process_answer(query: CallbackQuery, callback_data: dict, state: FSMContext):

    data = await state.get_data()
    data['cid'] = callback_data['cid']
    await state.update_data(**data)

    await query.message.answer('Напиши ответ.', reply_markup=ReplyKeyboardRemove())
    await AnswerState.answer.set()


@dp.message(IsAdmin(), state=AnswerState.answer)
async def process_submit(message: Message, state: FSMContext):

    data = await state.get_data()
    data['answer'] = message.text
    await state.update_data(**data)

    await AnswerState.next()
    await message.answer('Убедитесь, что не ошиблись в ответе.', reply_markup=submit_markup())


@dp.message(IsAdmin(), F.text == cancel_message, state=AnswerState.submit)
async def process_send_answer(message: Message, state: FSMContext):
    await message.answer('Отменено!', reply_markup=ReplyKeyboardRemove())
    await state.clear()


@dp.message(IsAdmin(), F.text == all_right_message, state=AnswerState.submit)
async def process_send_answer(message: Message, state: FSMContext):

    data = await state.get_data()

    answer = data['answer']
    cid = data['cid']

        question = db.fetchone(
            'SELECT question FROM questions WHERE cid=?', (cid,))[0]
        db.query('DELETE FROM questions WHERE cid=?', (cid,))
        text = f'Вопрос: <b>{question}</b>\n\nОтвет: <b>{answer}</b>'

        await message.answer('Отправлено!', reply_markup=ReplyKeyboardRemove())
        await bot.send_message(cid, text)

    await state.clear()
