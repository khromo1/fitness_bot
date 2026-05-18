import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "8994766961:AAEcIpZpaJm1FIsZRn77N1B-uSa-fS-jCfs"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# статы

class UserData(StatesGroup):
    gender = State()
    age = State()
    weight = State()
    height = State()
    activity = State()
    goal = State()

# интерфейс

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💪 Силовые тренировки")],
        [KeyboardButton(text="🏃 Кардио тренировки")],
        [KeyboardButton(text="🔥 Калькулятор калорий")]
    ],
    resize_keyboard=True
)

difficulty_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Легкий")],
        [KeyboardButton(text="Средний")],
        [KeyboardButton(text="Сложный")]
    ],
    resize_keyboard=True
)

gender_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Мужчина")],
        [KeyboardButton(text="Женщина")]
    ],
    resize_keyboard=True
)

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Добро пожаловать в Fitness Bot 💪\n\n"
        "Выберите нужный раздел:",
        reply_markup=main_keyboard
    )

# силовые

@dp.message(F.text == "💪 Силовые тренировки")
async def strength(message: Message):
    await message.answer(
        "Выберите уровень подготовки:",
        reply_markup=difficulty_keyboard
    )

@dp.message(F.text == "Легкий")
async def easy_strength(message: Message):
    await message.answer(
        "💪 ЛЕГКАЯ СИЛОВАЯ ПРОГРАММА\n\n"
        "1. Приседания — 3x10\n"
        "2. Отжимания от колен — 3x8\n"
        "3. Планка — 3x30 сек\n"
        "4. Выпады — 3x10\n"
        "5. Скручивания — 3x15"
    )

@dp.message(F.text == "Средний")
async def medium_strength(message: Message):
    await message.answer(
        "💪 СРЕДНЯЯ СИЛОВАЯ ПРОГРАММА\n\n"
        "1. Приседания — 4x12\n"
        "2. Отжимания — 4x12\n"
        "3. Планка — 4x45 сек\n"
        "4. Берпи — 3x10\n"
        "5. Подтягивания — 3x6"
    )

@dp.message(F.text == "Сложный")
async def hard_strength(message: Message):
    await message.answer(
        "💪 СЛОЖНАЯ СИЛОВАЯ ПРОГРАММА\n\n"
        "1. Приседания с весом — 5x10\n"
        "2. Подтягивания — 5x10\n"
        "3. Отжимания на брусьях — 5x12\n"
        "4. Берпи — 5x15\n"
        "5. Планка — 5x1 мин"
    )

# кардио

@dp.message(F.text == "🏃 Кардио тренировки")
async def cardio(message: Message):
    await message.answer(
        "Выберите уровень подготовки:",
        reply_markup=difficulty_keyboard
    )

# счетчик калорий

@dp.message(F.text == "🔥 Калькулятор калорий")
async def calories(message: Message, state: FSMContext):
    await state.set_state(UserData.gender)
    await message.answer(
        "Выберите пол:",
        reply_markup=gender_keyboard
    )

@dp.message(UserData.gender)
async def get_gender(message: Message, state: FSMContext):
    await state.update_data(gender=message.text)
    await state.set_state(UserData.age)
    await message.answer("Введите возраст:")

@dp.message(UserData.age)
async def get_age(message: Message, state: FSMContext):
    await state.update_data(age=int(message.text))
    await state.set_state(UserData.weight)
    await message.answer("Введите вес (кг):")

@dp.message(UserData.weight)
async def get_weight(message: Message, state: FSMContext):
    await state.update_data(weight=float(message.text))
    await state.set_state(UserData.height)
    await message.answer("Введите рост (см):")

@dp.message(UserData.height)
async def get_height(message: Message, state: FSMContext):
    await state.update_data(height=float(message.text))
    data = await state.get_data()

    gender = data["gender"]
    age = data["age"]
    weight = data["weight"]
    height = data["height"]

    # Формула Миффлина-Сан-Жеора
    if gender == "Мужчина":
        calories = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        calories = (10 * weight) + (6.25 * height) - (5 * age) - 161

    await message.answer(
        f"🔥 Ваша дневная норма калорий:\n\n"
        f"{round(calories)} ккал"
    )

    await state.clear()

# run bot

async def main():
    print("Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())