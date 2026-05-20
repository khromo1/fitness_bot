import asyncio
import os
import logging
import functools
from dataclasses import dataclass
from typing import Generator

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")

#декораторы
def log_handler(func):
    """Декоратор: логирует каждый вызов хэндлера."""
    @functools.wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        logger.info(
            "user=%s | handler=%s | text=%r",
            message.from_user.id,
            func.__name__,
            message.text,
        )
        return await func(message, *args, **kwargs)
    return wrapper


def validate_number(min_val: float, max_val: float, label: str):
    """Декоратор-фабрика: проверяет что текст сообщения — число в диапазоне."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(message: Message, state: FSMContext, *args, **kwargs):
            try:
                value = float(message.text.replace(",", "."))
                assert min_val <= value <= max_val
            except (ValueError, AssertionError):
                await message.answer(
                    f"⚠️ Введите корректное значение для «{label}» "
                    f"({min_val}–{max_val}):"
                )
                return
            return await func(message, state, *args, **kwargs)
        return wrapper
    return decorator

# итераторы

@dataclass
class Exercise:
    name: str
    sets: int
    reps: str
    emoji: str = "•"

    def __str__(self) -> str:
        return f"{self.emoji} {self.name} — {self.sets}×{self.reps}"


class WorkoutIterator:
    """Итератор: перебирает упражнения программы тренировки одно за другим."""

    def __init__(self, exercises: list):
        self._exercises = exercises
        self._index = 0

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self) -> Exercise:
        if self._index >= len(self._exercises):
            raise StopIteration
        exercise = self._exercises[self._index]
        self._index += 1
        return exercise

    def as_text(self) -> str:
        return "\n".join(
            f"{i}. {ex}" for i, ex in enumerate(self, start=1)
        )
    
#генераторы

def nutrition_tips_generator() -> Generator[str, None, None]:
    """Генератор: бесконечно выдаёт советы по питанию по кругу."""
    tips = [
        "💧 Пейте 30 мл воды на каждый кг веса в день.",
        "🥗 Ешьте овощи с каждым приёмом пищи.",
        "⏰ Не пропускайте завтрак — он запускает метаболизм.",
        "🍗 Добавляйте белок в каждый приём пищи.",
        "🚫 Избегайте еды за 2–3 часа до сна.",
        "🥜 Перекусывайте орехами, а не сладким.",
        "🍽️ Ешьте медленно — мозгу нужно 20 мин чтобы понять сытость.",
    ]
    index = 0
    while True:
        yield tips[index % len(tips)]
        index += 1


def macro_breakdown_generator(
    calories: float, protein_g: float, fat_g: float, carbs_g: float
) -> Generator[str, None, None]:
    """Генератор: пошагово выдаёт строки отчёта о макронутриентах."""
    yield f"🥩 Белки:    {round(protein_g)} г  ({round(protein_g * 4)} ккал)"
    yield f"🧈 Жиры:     {round(fat_g)} г  ({round(fat_g * 9)} ккал)"
    yield f"🍞 Углеводы: {round(carbs_g)} г  ({round(carbs_g * 4)} ккал)"

@dataclass
class WorkoutProgram:
    """Программа тренировки: название, тип, уровень, список упражнений."""
    title: str
    kind: str
    level: str
    exercises: list
    rest_seconds: int
    days_per_week: int
    target_hr: str = ""

    def summary(self) -> str:
        iterator = WorkoutIterator(self.exercises)
        level_emoji = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}[self.level]
        lines = [
            f"{level_emoji} {self.title}\n",
            iterator.as_text(),
            f"\n⏱ Отдых: {self.rest_seconds} сек",
            f"📅 {self.days_per_week} раз в неделю",
        ]
        if self.target_hr:
            lines.append(f"🎯 Пульс: {self.target_hr}")
        return "\n".join(lines)


@dataclass
class UserProfile:
    """Профиль пользователя для калькулятора калорий."""
    gender: str
    age: int
    weight: float
    height: float
    activity_factor: float
    goal_delta: int

    def bmr(self) -> float:
        """Базовый обмен по формуле Миффлина–Сен-Жеора."""
        base = 10 * self.weight + 6.25 * self.height - 5 * self.age
        return base + 5 if "Мужчина" in self.gender else base - 161

    def tdee(self) -> float:
        return self.bmr() * self.activity_factor

    def target_calories(self) -> float:
        return self.tdee() + self.goal_delta

    def macros(self) -> tuple:
        """Возвращает (белки г, жиры г, углеводы г)."""
        cal = self.target_calories()
        protein = self.weight * 2.0
        fat = self.weight * 1.0
        carbs = (cal - protein * 4 - fat * 9) / 4
        return protein, fat, carbs

#каталог

class WorkoutCatalog:
    """Хранит все программы тренировок и выдаёт их по типу и уровню."""

    def __init__(self):
        self._programs: dict = {}
        self._fill()

    def get(self, kind: str, level: str):
        return self._programs.get((kind, level))

    def _add(self, program: WorkoutProgram):
        self._programs[(program.kind, program.level)] = program

    def _fill(self):
        # силовые
        self._add(WorkoutProgram(
            title="ЛЁГКАЯ СИЛОВАЯ ПРОГРАММА",
            kind="strength", level="easy",
            rest_seconds=90, days_per_week=3,
            exercises=[
                Exercise("Приседания",           3, "10",     "🏋️"),
                Exercise("Отжимания от колен",   3, "8",      "💪"),
                Exercise("Планка",               3, "30 сек", "🧱"),
                Exercise("Выпады",               3, "10",     "🦵"),
                Exercise("Скручивания",          3, "15",     "🔄"),
            ],
        ))
        self._add(WorkoutProgram(
            title="СРЕДНЯЯ СИЛОВАЯ ПРОГРАММА",
            kind="strength", level="medium",
            rest_seconds=60, days_per_week=4,
            exercises=[
                Exercise("Приседания",               4, "12",     "🏋️"),
                Exercise("Отжимания",                4, "12",     "💪"),
                Exercise("Планка",                   4, "45 сек", "🧱"),
                Exercise("Берпи",                    3, "10",     "🔥"),
                Exercise("Подтягивания",             3, "6",      "🏅"),
                Exercise("Румынская тяга (гантели)", 3, "12",     "🦵"),
            ],
        ))
        self._add(WorkoutProgram(
            title="СЛОЖНАЯ СИЛОВАЯ ПРОГРАММА",
            kind="strength", level="hard",
            rest_seconds=40, days_per_week=5,
            exercises=[
                Exercise("Приседания со штангой",    5, "10",     "🏋️"),
                Exercise("Подтягивания с весом",     5, "8",      "🏅"),
                Exercise("Отжимания на брусьях",     5, "12",     "💪"),
                Exercise("Берпи",                    5, "15",     "🔥"),
                Exercise("Планка",                   5, "60 сек", "🧱"),
                Exercise("Жим штанги лёжа",          5, "10",     "🏋️"),
            ],
        ))
        # кардио
        self._add(WorkoutProgram(
            title="ЛЁГКАЯ КАРДИО ПРОГРАММА",
            kind="cardio", level="easy",
            rest_seconds=90, days_per_week=3,
            target_hr="50–60% от макс.",
            exercises=[
                Exercise("Ходьба быстрым шагом",  1, "20 мин", "🚶"),
                Exercise("Прыжки на скакалке",    3, "1 мин",  "🪢"),
                Exercise("Бег на месте",          2, "3 мин",  "🏃"),
                Exercise("Велотренажёр",          1, "10 мин", "🚴"),
            ],
        ))
        self._add(WorkoutProgram(
            title="СРЕДНЯЯ КАРДИО ПРОГРАММА",
            kind="cardio", level="medium",
            rest_seconds=60, days_per_week=4,
            target_hr="60–70% от макс.",
            exercises=[
                Exercise("Разминка — ходьба",     1, "5 мин",  "🚶"),
                Exercise("Бег",                   1, "20 мин", "🏃"),
                Exercise("Прыжки на скакалке",    3, "2 мин",  "🪢"),
                Exercise("Джампинг джек",         3, "30 раз", "⭐"),
                Exercise("Заминка — растяжка",    1, "5 мин",  "🧘"),
            ],
        ))
        self._add(WorkoutProgram(
            title="СЛОЖНАЯ КАРДИО ПРОГРАММА",
            kind="cardio", level="hard",
            rest_seconds=30, days_per_week=5,
            target_hr="80–90% от макс.",
            exercises=[
                Exercise("HIIT спринт 30с/отдых 30с", 10, "1 цикл", "⚡"),
                Exercise("Берпи",                      4,  "20",     "🔥"),
                Exercise("Прыжки на скакалке",         5,  "2 мин",  "🪢"),
                Exercise("Mountain climbers",           4,  "30",     "🧗"),
                Exercise("Заминка",                    1,  "5 мин",  "🧘"),
            ],
        ))

class FitnessBot:
    """Главный класс: инициализирует бота, регистрирует хэндлеры."""

    ACTIVITY_MAP: dict = {
        "🛋️ Минимальная":  1.2,
        "🚶 Низкая":        1.375,
        "🏋️ Средняя":      1.55,
        "🔥 Высокая":       1.725,
        "⚡ Очень высокая": 1.9,
    }
    GOAL_MAP: dict = {
        "📉 Похудеть":       -500,
        "⚖️ Поддержать вес":    0,
        "📈 Набрать массу":  +300,
    }
    LEVEL_MAP: dict = {
        "🟢 Легкий":  "easy",
        "🟡 Средний": "medium",
        "🔴 Сложный": "hard",
    }

    def __init__(self, token: str):
        self.bot     = Bot(token=token)
        self.dp      = Dispatcher(storage=MemoryStorage())
        self.catalog = WorkoutCatalog()
        self._tips   = nutrition_tips_generator()   # бесконечный генератор советов
        self._register_handlers()

    # интерфейс
    @staticmethod
    def _kb(*rows) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=t) for t in row] for row in rows],
            resize_keyboard=True,
        )

    @property
    def main_kb(self):
        return self._kb(
            ["💪 Силовые тренировки"],
            ["🏃 Кардио тренировки"],
            ["🔥 Калькулятор калорий"],
        )

    @property
    def level_kb(self):
        return self._kb(["🟢 Легкий", "🟡 Средний", "🔴 Сложный"], ["🏠 Главное меню"])

    @property
    def gender_kb(self):
        return self._kb(["👨 Мужчина", "👩 Женщина"], ["🏠 Главное меню"])

    @property
    def activity_kb(self):
        return self._kb(
            ["🛋️ Минимальная"], ["🚶 Низкая"], ["🏋️ Средняя"],
            ["🔥 Высокая"], ["⚡ Очень высокая"], ["🏠 Главное меню"],
        )

    @property
    def goal_kb(self):
        return self._kb(
            ["📉 Похудеть"], ["⚖️ Поддержать вес"], ["📈 Набрать массу"], ["🏠 Главное меню"],
        )

    # FSM состояния

    class WorkoutState(StatesGroup):
        choosing_strength = State()
        choosing_cardio   = State()

    class CalcState(StatesGroup):
        gender   = State()
        age      = State()
        weight   = State()
        height   = State()
        activity = State()
        goal     = State()

    # регистрация хэндлеров
    def _register_handlers(self):
        dp = self.dp
        WS = self.WorkoutState
        CS = self.CalcState

        dp.message.register(self.cmd_start,        CommandStart())
        dp.message.register(self.to_main,          F.text == "🏠 Главное меню")

        dp.message.register(self.strength_menu,    F.text == "💪 Силовые тренировки")
        dp.message.register(self.strength_program, WS.choosing_strength, F.text.in_(self.LEVEL_MAP))

        dp.message.register(self.cardio_menu,      F.text == "🏃 Кардио тренировки")
        dp.message.register(self.cardio_program,   WS.choosing_cardio,   F.text.in_(self.LEVEL_MAP))

        dp.message.register(self.calc_start,       F.text == "🔥 Калькулятор калорий")
        dp.message.register(self.get_gender,       CS.gender,   F.text.in_(["👨 Мужчина", "👩 Женщина"]))
        dp.message.register(self.get_age,          CS.age)
        dp.message.register(self.get_weight,       CS.weight)
        dp.message.register(self.get_height,       CS.height)
        dp.message.register(self.get_activity,     CS.activity, F.text.in_(self.ACTIVITY_MAP))
        dp.message.register(self.get_goal,         CS.goal,     F.text.in_(self.GOAL_MAP))

        dp.message.register(self._wrong_gender,    CS.gender)
        dp.message.register(self._wrong_activity,  CS.activity)
        dp.message.register(self._wrong_goal,      CS.goal)
        dp.message.register(self._wrong_level_s,   WS.choosing_strength)
        dp.message.register(self._wrong_level_c,   WS.choosing_cardio)

    # хэндлеры
    @log_handler
    async def cmd_start(self, message: Message, state: FSMContext):
        await state.clear()
        await message.answer(
            f"Привет, {message.from_user.first_name}! 👋\n\n"
            "Добро пожаловать в Fitness Bot 💪\n"
            "Выберите нужный раздел:",
            reply_markup=self.main_kb,
        )

    @log_handler
    async def to_main(self, message: Message, state: FSMContext):
        await state.clear()
        await message.answer("Главное меню:", reply_markup=self.main_kb)

    @log_handler
    async def strength_menu(self, message: Message, state: FSMContext):
        await state.set_state(self.WorkoutState.choosing_strength)
        await message.answer("Выберите уровень:", reply_markup=self.level_kb)

    @log_handler
    async def strength_program(self, message: Message, state: FSMContext):
        await state.clear()
        program = self.catalog.get("strength", self.LEVEL_MAP[message.text])
        await message.answer(program.summary(), reply_markup=self.main_kb)

    @log_handler
    async def cardio_menu(self, message: Message, state: FSMContext):
        await state.set_state(self.WorkoutState.choosing_cardio)
        await message.answer("Выберите уровень:", reply_markup=self.level_kb)

    @log_handler
    async def cardio_program(self, message: Message, state: FSMContext):
        await state.clear()
        program = self.catalog.get("cardio", self.LEVEL_MAP[message.text])
        await message.answer(program.summary(), reply_markup=self.main_kb)

    @log_handler
    async def calc_start(self, message: Message, state: FSMContext):
        await state.set_state(self.CalcState.gender)
        await message.answer("Шаг 1/5 — Выберите пол:", reply_markup=self.gender_kb)

    @log_handler
    async def get_gender(self, message: Message, state: FSMContext):
        await state.update_data(gender=message.text)
        await state.set_state(self.CalcState.age)
        await message.answer("Шаг 2/5 — Введите возраст (лет):", reply_markup=ReplyKeyboardRemove())

    @log_handler
    async def get_age(self, message: Message, state: FSMContext):
        if not message.text.isdigit() or not (10 <= int(message.text) <= 100):
            await message.answer("⚠️ Введите корректный возраст (10–100):")
            return
        await state.update_data(age=int(message.text))
        await state.set_state(self.CalcState.weight)
        await message.answer("Шаг 3/5 — Введите вес (кг):")

    @log_handler
    @validate_number(20, 300, "вес (кг)")
    async def get_weight(self, message: Message, state: FSMContext):
        await state.update_data(weight=float(message.text.replace(",", ".")))
        await state.set_state(self.CalcState.height)
        await message.answer("Шаг 4/5 — Введите рост (см):")

    @log_handler
    @validate_number(100, 250, "рост (см)")
    async def get_height(self, message: Message, state: FSMContext):
        await state.update_data(height=float(message.text.replace(",", ".")))
        await state.set_state(self.CalcState.activity)
        await message.answer("Шаг 5/5 — Уровень активности:", reply_markup=self.activity_kb)

    @log_handler
    async def get_activity(self, message: Message, state: FSMContext):
        await state.update_data(activity=message.text)
        await state.set_state(self.CalcState.goal)
        await message.answer("Какова ваша цель?", reply_markup=self.goal_kb)

    @log_handler
    async def get_goal(self, message: Message, state: FSMContext):
        data    = await state.get_data()
        profile = UserProfile(
            gender          = data["gender"],
            age             = data["age"],
            weight          = data["weight"],
            height          = data["height"],
            activity_factor = self.ACTIVITY_MAP[data["activity"]],
            goal_delta      = self.GOAL_MAP[message.text],
        )
        await state.clear()

        protein, fat, carbs = profile.macros()

        # генератор строит отчёт построчно
        macro_lines = list(macro_breakdown_generator(
            profile.target_calories(), protein, fat, carbs
        ))

        # следующий совет из бесконечного генератора
        tip = next(self._tips)

        report = (
            "✅ РЕЗУЛЬТАТЫ\n\n"
            f"📊 BMR (базовый обмен):  {round(profile.bmr())} ккал\n"
            f"⚡ TDEE (с активностью): {round(profile.tdee())} ккал\n"
            f"🎯 Цель «{message.text}»: {round(profile.target_calories())} ккал\n\n"
            "📊 БЖУК:\n"
            + "\n".join(macro_lines)
            + f"\n\n💡 Совет дня:\n{tip}"
        )
        await message.answer(report, reply_markup=self.main_kb)

    # неверный ввод
    async def _wrong_gender(self,   message: Message): await message.answer("⚠️ Выберите пол кнопкой выше.")
    async def _wrong_activity(self, message: Message): await message.answer("⚠️ Выберите активность кнопкой выше.")
    async def _wrong_goal(self,     message: Message): await message.answer("⚠️ Выберите цель кнопкой выше.")
    async def _wrong_level_s(self,  message: Message): await message.answer("⚠️ Выберите уровень кнопкой выше.")
    async def _wrong_level_c(self,  message: Message): await message.answer("⚠️ Выберите уровень кнопкой выше.")

    # запуск
    async def run(self):
        logger.info("✅ Bot started...")
        await self.dp.start_polling(self.bot)

if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("Переменная окружения BOT_TOKEN не задана!")
    asyncio.run(FitnessBot(TOKEN).run())