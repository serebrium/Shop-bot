from aiogram.fsm.state import StatesGroup, State


class CheckoutState(StatesGroup):
    check_cart = State()
    count = State()
    name = State()
    address = State()
    confirm = State()
