import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage


TOKEN = os.getenv("BOT_TOKEN", "8994766961:AAEYpW0jr2PcFX9d1IR583qvGn5l5Iktf54")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# статы
class WorkoutState(StatesGroup):
    choosing_strength_level = State()
    choosing_cardio_level   = State()

class CalcState(StatesGroup):
    gender   = State()
    age      = State()
    weight   = State()
    height   = State()
    activity = State()
    goal     = State()


# интерфейс
def kb(*rows):
    """Быстрое создание клавиатуры."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t) for t in row] for row in rows],
        resize_keyboard=True
    )

main_kb = kb(
    ["💪 Силовые тренировки"],
    ["🏃 Кардио тренировки"],
    ["🔥 Калькулятор калорий"],
)

level_kb = kb(["🟢 Легкий", "🟡 Средний", "🔴 Сложный"], ["🏠 Главное меню"])

gender_kb = kb(["👨 Мужчина", "👩 Женщина"], ["🏠 Главное меню"])

activity_kb = kb(
    ["🛋️ Минимальная (сидячий образ жизни)"],
    ["🚶 Низкая (1–3 тренировки в неделю)"],
    ["🏋️ Средняя (3–5 тренировок в неделю)"],
    ["🔥 Высокая (6–7 тренировок в неделю)"],
    ["⚡ Очень высокая (физический труд)"],
    ["🏠 Главное меню"],
)

goal_kb = kb(
    ["📉 Похудеть"],
    ["⚖️ Поддержать вес"],
    ["📈 Набрать массу"],
    ["🏠 Главное меню"],
)

ACTIVITY_MAP = {
    "🛋️ Минимальная (сидячий образ жизни)":    1.2,
    "🚶 Низкая (1–3 тренировки в неделю)":      1.375,
    "🏋️ Средняя (3–5 тренировок в неделю)":    1.55,
    "🔥 Высокая (6–7 тренировок в неделю)":     1.725,
    "⚡ Очень высокая (физический труд)":        1.9,
}

GOAL_MAP = {
    "📉 Похудеть":        -500,
    "⚖️ Поддержать вес":    0,
    "📈 Набрать массу":   +300,
}

# программы тренировок
STRENGTH = {
    "🟢 Легкий": (
        "💪 ЛЕГКАЯ СИЛОВАЯ ПРОГРАММА\n\n"
        "1. Приседания — 3×10\n"
        "2. Отжимания от колен — 3×8\n"
        "3. Планка — 3×30 сек\n"
        "4. Выпады — 3×10 (каждая нога)\n"
        "5. Скручивания — 3×15\n\n"
        "⏱ Отдых между подходами: 60–90 сек\n"
        "📅 Рекомендуется: 3 раза в неделю"
    ),
    "🟡 Средний": (
        "💪 СРЕДНЯЯ СИЛОВАЯ ПРОГРАММА\n\n"
        "1. Приседания — 4×12\n"
        "2. Отжимания — 4×12\n"
        "3. Планка — 4×45 сек\n"
        "4. Берпи — 3×10\n"
        "5. Подтягивания — 3×6\n"
        "6. Румынская тяга (с гантелями) — 3×12\n\n"
        "⏱ Отдых между подходами: 45–60 сек\n"
        "📅 Рекомендуется: 4 раза в неделю"
    ),
    "🔴 Сложный": (
        "💪 СЛОЖНАЯ СИЛОВАЯ ПРОГРАММА\n\n"
        "1. Приседания со штангой — 5×10\n"
        "2. Подтягивания с весом — 5×8\n"
        "3. Отжимания на брусьях — 5×12\n"
        "4. Берпи — 5×15\n"
        "5. Планка — 5×60 сек\n"
        "6. Жим штанги лёжа — 5×10\n\n"
        "⏱ Отдых между подходами: 30–45 сек\n"
        "📅 Рекомендуется: 5 раз в неделю"
    ),
}

CARDIO = {
    "🟢 Легкий": (
        "🏃 ЛЕГКАЯ КАРДИО ПРОГРАММА\n\n"
        "1. Ходьба быстрым шагом — 20 мин\n"
        "2. Прыжки на скакалке — 3×1 мин\n"
        "3. Лёгкий бег на месте — 2×3 мин\n"
        "4. Велотренажёр — 10 мин\n\n"
        "🎯 Целевой пульс: 50–60% от максимального\n"
        "📅 Рекомендуется: 3–4 раза в неделю"
    ),
    "🟡 Средний": (
        "🏃 СРЕДНЯЯ КАРДИО ПРОГРАММА\n\n"
        "1. Разминка — 5 мин ходьба\n"
        "2. Бег — 20 мин (умеренный темп)\n"
        "3. Прыжки на скакалке — 3×2 мин\n"
        "4. Джампинг джек — 3×30 раз\n"
        "5. Заминка — 5 мин растяжка\n\n"
        "🎯 Целевой пульс: 60–70% от максимального\n"
        "📅 Рекомендуется: 4–5 раз в неделю"
    ),
    "🔴 Сложный": (
        "🏃 СЛОЖНАЯ КАРДИО ПРОГРАММА\n\n"
        "1. Разминка — 5 мин\n"
        "2. Интервальный бег (HIIT):\n"
        "   — Спринт 30 сек / отдых 30 сек × 10\n"
        "3. Берпи — 4×20\n"
        "4. Прыжки на скакалке — 5×2 мин\n"
        "5. Горная лыжа (Mountain climbers) — 4×30\n"
        "6. Заминка — 5 мин\n\n"
        "🎯 Целевой пульс: 80–90% от максимального\n"
        "📅 Рекомендуется: 5–6 раз в неделю"
    ),
}


# хелперы

async def go_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_kb)


# менюшка
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Добро пожаловать в Fitness Bot 💪\n"
        "Выберите нужный раздел:",
        reply_markup=main_kb
    )

@dp.message(F.text == "🏠 Главное меню")
async def to_main(message: Message, state: FSMContext):
    await go_main(message, state)


# силовые
@dp.message(F.text == "💪 Силовые тренировки")
async def strength_menu(message: Message, state: FSMContext):
    await state.set_state(WorkoutState.choosing_strength_level)
    await message.answer("Выберите уровень подготовки:", reply_markup=level_kb)

@dp.message(WorkoutState.choosing_strength_level, F.text.in_(STRENGTH))
async def strength_program(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(STRENGTH[message.text], reply_markup=main_kb)


# кардио
@dp.message(F.text == "🏃 Кардио тренировки")
async def cardio_menu(message: Message, state: FSMContext):
    await state.set_state(WorkoutState.choosing_cardio_level)
    await message.answer("Выберите уровень подготовки:", reply_markup=level_kb)

@dp.message(WorkoutState.choosing_cardio_level, F.text.in_(CARDIO))
async def cardio_program(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(CARDIO[message.text], reply_markup=main_kb)


# калькулятор калорий
@dp.message(F.text == "🔥 Калькулятор калорий")
async def calc_start(message: Message, state: FSMContext):
    await state.set_state(CalcState.gender)
    await message.answer("Шаг 1/5 — Выберите пол:", reply_markup=gender_kb)

@dp.message(CalcState.gender, F.text.in_(["👨 Мужчина", "👩 Женщина"]))
async def get_gender(message: Message, state: FSMContext):
    await state.update_data(gender=message.text)
    await state.set_state(CalcState.age)
    await message.answer("Шаг 2/5 — Введите ваш возраст (лет):", reply_markup=ReplyKeyboardRemove())

@dp.message(CalcState.age)
async def get_age(message: Message, state: FSMContext):
    if not message.text.isdigit() or not (10 <= int(message.text) <= 100):
        await message.answer("⚠️ Пожалуйста, введите корректный возраст (от 10 до 100):")
        return
    await state.update_data(age=int(message.text))
    await state.set_state(CalcState.weight)
    await message.answer("Шаг 3/5 — Введите ваш вес (кг):")

@dp.message(CalcState.weight)
async def get_weight(message: Message, state: FSMContext):
    try:
        w = float(message.text.replace(",", "."))
        assert 20 <= w <= 300
    except (ValueError, AssertionError):
        await message.answer("⚠️ Пожалуйста, введите корректный вес (от 20 до 300 кг):")
        return
    await state.update_data(weight=w)
    await state.set_state(CalcState.height)
    await message.answer("Шаг 4/5 — Введите ваш рост (см):")

@dp.message(CalcState.height)
async def get_height(message: Message, state: FSMContext):
    try:
        h = float(message.text.replace(",", "."))
        assert 100 <= h <= 250
    except (ValueError, AssertionError):
        await message.answer("⚠️ Пожалуйста, введите корректный рост (от 100 до 250 см):")
        return
    await state.update_data(height=h)
    await state.set_state(CalcState.activity)
    await message.answer("Шаг 5/5 — Выберите уровень активности:", reply_markup=activity_kb)

@dp.message(CalcState.activity, F.text.in_(ACTIVITY_MAP))
async def get_activity(message: Message, state: FSMContext):
    await state.update_data(activity=message.text)
    await state.set_state(CalcState.goal)
    await message.answer("Какова ваша цель?", reply_markup=goal_kb)

@dp.message(CalcState.goal, F.text.in_(GOAL_MAP))
async def get_goal(message: Message, state: FSMContext):
    data = await state.get_data()
    gender   = data["gender"]
    age      = data["age"]
    weight   = data["weight"]
    height   = data["height"]
    activity = data["activity"]
    goal     = message.text

    # Формула Миффлина–Сен-Жеора
    if "Мужчина" in gender:
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    tdee   = bmr * ACTIVITY_MAP[activity]
    target = tdee + GOAL_MAP[goal]

    protein = round(weight * 2.0)   # г/кг
    fat     = round(weight * 1.0)
    carbs   = round((target - protein * 4 - fat * 9) / 4)

    await state.clear()
    await message.answer(
        f"✅ РЕЗУЛЬТАТЫ РАСЧЁТА\n\n"
        f"🔥 Базовый обмен (BMR): {round(bmr)} ккал\n"
        f"⚡ С учётом активности (TDEE): {round(tdee)} ккал\n"
        f"🎯 Цель «{goal}»: {round(target)} ккал/день\n\n"
        f"📊 РЕКОМЕНДУЕМОЕ БЖУК:\n"
        f"  • Белки: {protein} г ({protein * 4} ккал)\n"
        f"  • Жиры: {fat} г ({fat * 9} ккал)\n"
        f"  • Углеводы: {carbs} г ({carbs * 4} ккал)\n\n"
        f"💡 Совет: взвешивайтесь раз в неделю утром натощак "
        f"и корректируйте калории на ±100 ккал при необходимости.",
        reply_markup=main_kb
    )

# ловилка ошибок
@dp.message(CalcState.gender)
async def wrong_gender(message: Message):
    await message.answer("⚠️ Пожалуйста, выберите пол кнопкой выше.")

@dp.message(CalcState.activity)
async def wrong_activity(message: Message):
    await message.answer("⚠️ Пожалуйста, выберите уровень активности кнопкой выше.")

@dp.message(CalcState.goal)
async def wrong_goal(message: Message):
    await message.answer("⚠️ Пожалуйста, выберите цель кнопкой выше.")


# запуск
async def main():
    print("✅ Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())