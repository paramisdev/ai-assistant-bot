from aiogram.fsm.state import State, StatesGroup


class SummarizeStates(StatesGroup):
    waiting_for_text = State()
