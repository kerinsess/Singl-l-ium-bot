"""
Telegram-бот для расчёта прироста ресурсов (пузыри, карточки, сундуки)
Установка: pip install pyTelegramBotAPI
Запуск: python bubble_bot.py
"""

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "ВАШ_ТОКЕН_ЗДЕСЬ"  # <-- вставьте токен от @BotFather

bot = telebot.TeleBot(BOT_TOKEN)

# ───────────────────────────────────────────────
# Хранилище данных пользователя (в памяти)
# ───────────────────────────────────────────────
user_data: dict[int, dict] = {}

DEFAULT_STATE = {
    "min_res": None,
    "max_res": None,
    "blue_min_per": 180,
    "blue_count": 0,
    "purple_min_per": 720,
    "purple_count": 0,
    "gold_min_per": 2880,
    "gold_count": 0,
    "premium_min_per": 11520,
    "premium_count": 0,
    "regular_min_min_per": 5,
    "regular_max_min_per": 60,
    "regular_count": 0,
    "step": None,   # текущий шаг ввода
}

def get_user(uid: int) -> dict:
    if uid not in user_data:
        user_data[uid] = DEFAULT_STATE.copy()
    return user_data[uid]

# ───────────────────────────────────────────────
# Расчёты
# ───────────────────────────────────────────────
def calc(data: dict) -> dict | None:
    min_r = data["min_res"]
    max_r = data["max_res"]
    if min_r is None or max_r is None:
        return None

    results = {}

    # Голубые карточки
    bc = data["blue_count"]
    bm = data["blue_min_per"]
    results["blue"] = {
        "min": bc * bm * min_r,
        "max": bc * bm * max_r,
        "avg": bc * bm * (min_r + max_r) // 2,
    }

    # Фиолетовые карточки
    pc = data["purple_count"]
    pm = data["purple_min_per"]
    results["purple"] = {
        "min": pc * pm * min_r,
        "max": pc * pm * max_r,
        "avg": pc * pm * (min_r + max_r) // 2,
    }

    # Золотые карточки
    gc = data["gold_count"]
    gm = data["gold_min_per"]
    results["gold"] = {
        "min": gc * gm * min_r,
        "max": gc * gm * max_r,
        "avg": gc * gm * (min_r + max_r) // 2,
    }

    # Премиум сундук
    prc = data["premium_count"]
    prm = data["premium_min_per"]
    results["premium"] = {
        "min": prc * prm * min_r,
        "max": prc * prm * max_r,
        "avg": prc * prm * (min_r + max_r) // 2,
    }

    # Обычный сундук (диапазон минут)
    rc = data["regular_count"]
    rmin = data["regular_min_min_per"]
    rmax = data["regular_max_min_per"]
    results["regular"] = {
        "min": rc * rmin * min_r,
        "max": rc * rmax * max_r,
        "avg": rc * (rmin + rmax) // 2 * (min_r + max_r) // 2,
    }

    # Итого
    results["total"] = {
        "min": sum(v["min"] for v in results.values()),
        "max": sum(v["max"] for v in results.values()),
        "avg": sum(v["avg"] for v in results.values()),
    }

    return results

def fmt(n: int) -> str:
    return f"{n:,}".replace(",", " ")

def build_report(data: dict) -> str:
    r = calc(data)
    if r is None:
        return "⚠️ Сначала укажите мин. и макс. ресурс в минуту."

    lines = [
        "📊 *Результаты расчёта*\n",
        f"⚙️ Ресурс/мин: {data['min_res']} – {data['max_res']}\n",
    ]

    sections = [
        ("🔵 Голубые карточки", "blue",    f"{data['blue_count']} шт × {data['blue_min_per']} мин"),
        ("🟣 Фиолетовые карточки", "purple", f"{data['purple_count']} шт × {data['purple_min_per']} мин"),
        ("🟡 Золотые карточки", "gold",    f"{data['gold_count']} шт × {data['gold_min_per']} мин"),
        ("💎 Премиум сундук", "premium",   f"{data['premium_count']} шт × {data['premium_min_per']} мин"),
        ("📦 Обычный сундук", "regular",   f"{data['regular_count']} шт × {data['regular_min_min_per']}–{data['regular_max_min_per']} мин"),
    ]

    for label, key, info in sections:
        v = r[key]
        if data.get(key.replace("regular","regular_count").replace("blue","blue_count")
                      .replace("purple","purple_count").replace("gold","gold_count")
                      .replace("premium","premium_count"), 1) == 0 and key != "regular":
            pass  # показываем всё равно
        lines.append(
            f"*{label}* ({info})\n"
            f"  мин: `{fmt(v['min'])}`\n"
            f"  макс: `{fmt(v['max'])}`\n"
            f"  ср: `{fmt(v['avg'])}`\n"
        )

    t = r["total"]
    lines.append(
        f"━━━━━━━━━━━━━━━━━\n"
        f"*ИТОГО*\n"
        f"  Общий мин. прирост: `{fmt(t['min'])}`\n"
        f"  Общий макс. прирост: `{fmt(t['max'])}`\n"
        f"  Общий ср. прирост: `{fmt(t['avg'])}`"
    )

    return "\n".join(lines)

# ───────────────────────────────────────────────
# Клавиатура главного меню
# ───────────────────────────────────────────────
def main_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("⚙️ Ресурс в мин", callback_data="set_res"),
        InlineKeyboardButton("🔵 Голубые карточки", callback_data="set_blue"),
    )
    kb.add(
        InlineKeyboardButton("🟣 Фиолетовые", callback_data="set_purple"),
        InlineKeyboardButton("🟡 Золотые", callback_data="set_gold"),
    )
    kb.add(
        InlineKeyboardButton("💎 Премиум сундук", callback_data="set_premium"),
        InlineKeyboardButton("📦 Обычный сундук", callback_data="set_regular"),
    )
    kb.add(InlineKeyboardButton("📊 Рассчитать", callback_data="calc"))
    kb.add(InlineKeyboardButton("🔄 Сбросить всё", callback_data="reset"))
    return kb

# ───────────────────────────────────────────────
# Команды
# ───────────────────────────────────────────────
@bot.message_handler(commands=["start", "help"])
def cmd_start(msg):
    uid = msg.from_user.id
    get_user(uid)
    bot.send_message(
        uid,
        "👋 *Калькулятор прироста ресурсов*\n\n"
        "Выберите параметр для настройки или нажмите *Рассчитать*:",
        parse_mode="Markdown",
        reply_markup=main_keyboard(),
    )

# ───────────────────────────────────────────────
# Обработка кнопок
# ───────────────────────────────────────────────
STEP_PROMPTS = {
    "res":     "Введите *мин. ресурс в минуту* и *макс. ресурс в минуту* через пробел\nПример: `1000 1500`",
    "blue":    "Введите *количество голубых карточек*\n(минут за карточку = 180, фиксировано)\nПример: `10`",
    "purple":  "Введите *количество фиолетовых карточек*\n(минут за карточку = 720)\nПример: `5`",
    "gold":    "Введите *количество золотых карточек*\n(минут за карточку = 2880)\nПример: `2`",
    "premium": "Введите *количество Премиум сундуков*\n(минут за штуку = 11520)\nПример: `2`",
    "regular": "Введите через пробел: *кол-во* *мин_минут* *макс_минут*\nПример: `10 5 60`",
}

@bot.callback_query_handler(func=lambda c: True)
def on_button(call):
    uid = call.from_user.id
    data = get_user(uid)
    cd = call.data

    if cd == "calc":
        bot.answer_callback_query(call.id)
        bot.send_message(uid, build_report(data), parse_mode="Markdown", reply_markup=main_keyboard())
        return

    if cd == "reset":
        user_data[uid] = DEFAULT_STATE.copy()
        bot.answer_callback_query(call.id, "Данные сброшены")
        bot.send_message(uid, "✅ Всё сброшено. Начните заново:", reply_markup=main_keyboard())
        return

    step_map = {
        "set_res": "res",
        "set_blue": "blue",
        "set_purple": "purple",
        "set_gold": "gold",
        "set_premium": "premium",
        "set_regular": "regular",
    }
    if cd in step_map:
        step = step_map[cd]
        data["step"] = step
        bot.answer_callback_query(call.id)
        bot.send_message(uid, STEP_PROMPTS[step], parse_mode="Markdown")

# ───────────────────────────────────────────────
# Обработка текстового ввода
# ───────────────────────────────────────────────
@bot.message_handler(func=lambda m: True)
def on_text(msg):
    uid = msg.from_user.id
    data = get_user(uid)
    step = data.get("step")
    text = msg.text.strip()

    if step is None:
        bot.send_message(uid, "Используйте меню ниже:", reply_markup=main_keyboard())
        return

    try:
        parts = list(map(int, text.split()))

        if step == "res":
            if len(parts) != 2:
                raise ValueError
            data["min_res"], data["max_res"] = sorted(parts)
            reply = f"✅ Ресурс в мин: {data['min_res']} – {data['max_res']}"

        elif step == "blue":
            data["blue_count"] = parts[0]
            reply = f"✅ Голубых карточек: {parts[0]} × 180 мин"

        elif step == "purple":
            data["purple_count"] = parts[0]
            reply = f"✅ Фиолетовых карточек: {parts[0]} × 720 мин"

        elif step == "gold":
            data["gold_count"] = parts[0]
            reply = f"✅ Золотых карточек: {parts[0]} × 2880 мин"

        elif step == "premium":
            data["premium_count"] = parts[0]
            reply = f"✅ Премиум сундуков: {parts[0]} × 11520 мин"

        elif step == "regular":
            if len(parts) == 1:
                data["regular_count"] = parts[0]
            elif len(parts) == 3:
                data["regular_count"] = parts[0]
                data["regular_min_min_per"] = parts[1]
                data["regular_max_min_per"] = parts[2]
            else:
                raise ValueError
            reply = (f"✅ Обычных сундуков: {data['regular_count']} × "
                     f"{data['regular_min_min_per']}–{data['regular_max_min_per']} мин")

        data["step"] = None
        bot.send_message(uid, reply, reply_markup=main_keyboard())

    except (ValueError, IndexError):
        bot.send_message(uid, "❌ Неверный формат. Попробуйте ещё раз:")

# ───────────────────────────────────────────────
if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()
