# Fitness Bot

A Telegram bot for fitness — workout programs and a calorie calculator. Built with Python and aiogram 3.

---

## Features

- **Strength Training** — three difficulty levels (easy, medium, hard)
- **Cardio Training** — three difficulty levels
- **Calorie Calculator** — calculates BMR, TDEE, and macros using the Mifflin–St Jeor formula

---

## Tech Stack

| Technology | Description |
|---|---|
| Python 3.12+ | Core language |
| aiogram 3 | Telegram Bot API library |
| FSM (MemoryStorage) | Conversation state management |

---

## Code Principles

The code demonstrates four key Python concepts:

**OOP** — five classes: `FitnessBot`, `WorkoutCatalog`, `WorkoutProgram`, `Exercise`, `UserProfile`

**Decorators** — `@log_handler` logs every incoming message, `@validate_number` validates numeric user input

**Iterator** — `WorkoutIterator` implements `__iter__` and `__next__` to iterate over exercises

**Generators** — `nutrition_tips_generator()` yields tips infinitely in a loop, `macro_breakdown_generator()` builds the macro report line by line

---

## Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/fitness-bot.git
cd fitness-bot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set your token

Get a token from [@BotFather](https://t.me/BotFather) and set the environment variable:

```bash
# Windows
set BOT_TOKEN=your_token_here

# Linux / macOS
export BOT_TOKEN=your_token_here
```

### 4. Run the bot

```bash
python bot.py
```

---

## Project Structure

```
fitness-bot/
├── bot.py           # All bot logic
├── requirements.txt # Dependencies
└── README.md        # This file
```

---

## Code Structure

```
FitnessBot                  ← main class
├── WorkoutCatalog          ← stores all workout programs
│   ├── WorkoutProgram      ← a single program
│   │   └── Exercise        ← a single exercise (dataclass)
│   └── WorkoutIterator     ← exercise iterator
├── UserProfile             ← user data (dataclass)
│   ├── bmr()               ← basal metabolic rate
│   ├── tdee()              ← total daily energy expenditure
│   └── macros()            ← proteins, fats, carbs
├── WorkoutState (FSM)      ← workout conversation states
├── CalcState (FSM)         ← calculator conversation states
└── Decorators
    ├── @log_handler        ← handler logging
    └── @validate_number    ← numeric input validation
```

---

## Deployment (Railway)

1. Push your code to [GitHub](https://github.com)
2. Sign up at [railway.app](https://railway.app) with GitHub
3. Click **New Project → Deploy from GitHub repo** → select your repository
4. Click on the service card → open the **Variables** tab
5. Add `BOT_TOKEN` = your token
6. Railway will deploy the bot automatically

Whenever you push changes with `git push`, Railway redeploys automatically.

---

## Author

Built with Python + aiogram 3
