import logging
import os
import secrets
from html import escape
from pathlib import Path

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from records import *

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

records = recordLoader(ROOT / "data")

SEARCH_WORD = "جستجو"
IOI_WORD = "جهانی"
NATIONAL_WORD = "ملی"


# ---------- keyboards ----------

def default_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("ℹ️ راهنما", callback_data="help")],
    ])


def home_button():
    return [InlineKeyboardButton("🏠 منوی اصلی", callback_data="home")]


def back_buttons():
    return InlineKeyboardMarkup([home_button()])


def years_buttons(competition):
    years = records.get_years(competition)
    rows = [
        [InlineKeyboardButton(year, callback_data=f"year:{competition}:{year}")
         for year in years[i:i + YEARS_PER_ROW]]
        for i in range(0, len(years), YEARS_PER_ROW)
    ]
    rows.append(home_button())
    return InlineKeyboardMarkup(rows)


def record_buttons(competition):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("‹ بازگشت به سال‌ها", callback_data=competition)],
        home_button(),
    ])


# ---------- texts ----------

def code(text):
    return f"<code>{escape(text)}</code>"


def start_panel():
    return (
        RTL + "<b>🇮🇷 آرشیو المپیاد کامپیوتر ایران</b>" + "\n\n"
        + RTL + "🔎 جست‌وجوی شخص: " + code(f"{SEARCH_WORD} نام") + "\n"
        + RTL + "🌍 نتایج جهانی: " + code(f"{IOI_WORD} سال") + "\n"
        + RTL + "🏅 نتایج ملی: " + code(f"{NATIONAL_WORD} سال") + " یا " + code(f"{NATIONAL_WORD} دوره") + "\n\n"
        + FOOTER
    )


def help_panel():
    return (
        RTL + "<b>ℹ️ راهنما</b>" + "\n\n"
        + RTL + "🔎 جست‌وجوی شخص (با بخشی از نام هم کار می‌کند)" + "\n"
        + RTL + code(f"{SEARCH_WORD} امیرعلی عسگری") + "\n\n"
        + RTL + "🌍 نتایج جهانی یک سال (بدون سال: فهرست سال‌ها)" + "\n"
        + RTL + code(f"{IOI_WORD} 2025") + "\n\n"
        + RTL + "🏅 نتایج ملی یک سال یا یک دوره (بدون عدد: فهرست سال‌ها)" + "\n"
        + RTL + code(f"{NATIONAL_WORD} 1404") + " یا " + code(f"{NATIONAL_WORD} 35") + "\n\n"
        + FOOTER
    )


def search_panel():
    return (
        RTL + "🔎 نام را بعد از «" + SEARCH_WORD + "» بنویسید:" + "\n"
        + RTL + code(f"{SEARCH_WORD} امیرعلی عسگری") + "\n\n"
        + FOOTER
    )


def years_panel(competition):
    title = "🌍 سال IOI" if competition == "ioi" else "🏅 سال INOI"
    return RTL + title + "\n\n" + FOOTER


def year_panel(competition, year):
    return records.get_ioi(year) if competition == "ioi" else records.get_national(year)


# ---------- sending helpers ----------

async def send(message, text, keyboard, parse_mode=None):
    await message.reply_text(text, reply_markup=keyboard, parse_mode=parse_mode, disable_web_page_preview=True)


async def edit(query, text, keyboard, parse_mode=None):
    try:
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode=parse_mode, disable_web_page_preview=True)
    except BadRequest as error:
        if "Message is not modified" not in str(error):
            raise


# ---------- person search ----------

async def person_result(message, context, name):
    name = tools.normalize(name)
    if records.has_person(name):
        await send(message, records.get_profile(name), default_buttons())
        return

    suggestions = records.get_matching(name) or records.get_similar(name)
    if not suggestions:
        await send(message, RTL + f"برای «{name}» رکوردی پیدا نشد." + "\n\n" + FOOTER, default_buttons())
        return

    request_id = secrets.token_urlsafe(6)
    context.user_data.setdefault("suggestions", {})[request_id] = suggestions
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(person, callback_data=f"suggest:{request_id}:{i}")]
         for i, person in enumerate(suggestions)] + [home_button()]
    )
    await send(message, RTL + f"منظورتان از «{name}» کدام فرد است؟" + "\n\n" + FOOTER, keyboard)


# ---------- commands ----------

async def start(update, context):
    await send(update.message, start_panel(), default_buttons(), parse_mode=ParseMode.HTML)


async def help_command(update, context):
    await send(update.message, help_panel(), default_buttons(), parse_mode=ParseMode.HTML)


def split_command(text):
    """'جستجو علی رضا' -> ('جستجو', 'علی رضا'); 'ملی' -> ('ملی', '')."""
    word, _, rest = tools.normalize(text).partition(" ")
    return word, tools.normalize(rest)


async def on_text(update, context):
    word, argument = split_command(update.message.text)

    if word == SEARCH_WORD:
        if not argument:
            await send(update.message, search_panel(), default_buttons(), parse_mode=ParseMode.HTML)
            return
        await person_result(update.message, context, argument)
    elif word in (IOI_WORD, NATIONAL_WORD):
        competition = "ioi" if word == IOI_WORD else "national"
        if not argument:
            await send(update.message, years_panel(competition), years_buttons(competition))
            return
        await send(update.message, year_panel(competition, argument), record_buttons(competition))


# ---------- buttons ----------

async def on_button(update, context):
    query = update.callback_query
    try:
        await query.answer()
    except BadRequest as error:
        if "too old" not in str(error) and "query id is invalid" not in str(error):
            raise
    data = query.data

    if data == "home":
        context.user_data.pop("suggestions", None)
        await edit(query, start_panel(), default_buttons(), parse_mode=ParseMode.HTML)
    elif data == "help":
        await edit(query, help_panel(), back_buttons(), parse_mode=ParseMode.HTML)
    elif data in ("ioi", "national"):
        await edit(query, years_panel(data), years_buttons(data))
    elif data.startswith("year:"):
        _, competition, year = data.split(":", 2)
        await edit(query, year_panel(competition, year), record_buttons(competition))
    elif data.startswith("suggest:"):
        try:
            _, request_id, index = data.split(":", 2)
            name = context.user_data.get("suggestions", {}).pop(request_id)[int(index)]
        except (KeyError, IndexError, ValueError):
            await edit(query, RTL + "این پیشنهاد دیگر در دسترس نیست. دوباره نام را جست‌وجو کنید." + "\n\n" + FOOTER, default_buttons())
            return
        await edit(query, records.get_profile(name), default_buttons())


async def on_error(update, context):
    logger.exception("Unhandled error while processing update %r", update, exc_info=context.error)


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN in .env")
    builder = Application.builder().token(token)
    proxy = os.getenv("TELEGRAM_PROXY_URL")
    if proxy:
        builder = builder.proxy(proxy).get_updates_proxy(proxy)
        logger.info("Using proxy %s", proxy.split("@")[-1])
    application = builder.build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(on_button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    application.add_error_handler(on_error)

    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=False, bootstrap_retries=-1)


if __name__ == "__main__":
    main()
