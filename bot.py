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
    ApplicationHandlerStop,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

import edit as editor
from records import *

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

records = recordLoader(ROOT / "data")
ADMIN_GROUP_ID = int(os.getenv("TELEGRAM_ADMIN_GROUP_ID", "0"))

SEARCH_WORD = "جستجو"
MAX_SUGGESTION_LISTS = 20
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


def remember(context, kind, value):
    """Store value under a short random id in user_data[kind] (callback_data is limited to 64 bytes)."""
    stored = context.user_data.setdefault(kind, {})
    key = secrets.token_urlsafe(6)
    stored[key] = value
    while len(stored) > MAX_SUGGESTION_LISTS:
        del stored[next(iter(stored))]
    return key


def profile_buttons(context, name):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ ویرایش اطلاعات", callback_data=f"edit:{remember(context, 'profiles', name)}")],
        [InlineKeyboardButton("ℹ️ راهنما", callback_data="help")],
    ])


def edit_buttons():
    fields = [InlineKeyboardButton(label, callback_data=f"field:{field}") for field, label in EXTRA_FIELDS.items()]
    fields.append(InlineKeyboardButton("🎖 مدال جدید", callback_data="field:medal"))
    rows = [fields[i:i + 2] for i in range(0, len(fields), 2)]
    rows.append([
        InlineKeyboardButton("❌ لغو", callback_data="edit_cancel"),
        InlineKeyboardButton("✅ ثبت", callback_data="edit_submit"),
    ])
    return InlineKeyboardMarkup(rows)


def cancel_buttons():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ لغو", callback_data="edit_cancel")]])


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


def medal_line(medal):
    return "سال " + medal[0] + " | " + medal[2] + " | " + MEDAL_TEXTS[medal[1]]


def edit_panel(editing):
    current = records.get_extra(editing["name"])
    ret = RTL + "✏️ ویرایش اطلاعات «" + editing["name"] + "»" + "\n\n"
    for field, label in EXTRA_FIELDS.items():
        if field in editing["changes"]:
            ret += RTL + label + ": " + editing["changes"][field] + " 🆕" + "\n"
        else:
            ret += RTL + label + ": " + (current[field] or "—") + "\n"
    for medal in editing["medals"]:
        ret += RTL + "🎖 مدال جدید: " + medal_line(medal) + " 🆕" + "\n"
    ret += "\n" + RTL + "برای تغییر هر مورد روی دکمهٔ آن بزنید. تغییرات بعد از «ثبت» و تأیید مدیران اعمال می‌شوند." + "\n"
    return ret + "\n" + FOOTER


def waiting_panel(field):
    if field == "medal":
        return (
            RTL + "🎖 مدال جدید را در یک پیام به این شکل بفرستید:" + "\n"
            + RTL + "سال ، عنوان ، شمارهٔ مدال" + "\n"
            + RTL + "مثال: 2024 ، APIO ، 1" + "\n\n"
            + "".join(RTL + str(i) + " = " + text + "\n" for i, text in enumerate(MEDAL_TEXTS))
        )
    return RTL + "✍️ مقدار جدید «" + EXTRA_FIELDS[field] + "» را بفرستید."


def parse_medal(text):
    """'2024 ، APIO ، 1' -> ['2024', 1, 'APIO'] (same order as extra_medals rows) or None."""
    parts = [tools.normalize(part) for part in text.replace("،", ",").split(",")]
    if len(parts) != 3 or not parts[0].isdigit() or not parts[1] or not parts[2].isdigit():
        return None
    index = int(parts[2])
    if index >= len(MEDAL_TEXTS):
        return None
    return [parts[0], index, parts[1]]


def review_panel(user, editing):
    ret = "📝 درخواست ویرایش" + "\n\n"
    ret += RTL + "👤 فرد: " + editing["name"] + "\n"
    ret += RTL + "🆔 کاربر: " + str(user.id) + (" (@" + user.username + ")" if user.username else "") + "\n\n"
    for field, value in editing["changes"].items():
        ret += RTL + EXTRA_FIELDS[field] + ": " + value + "\n"
    for medal in editing["medals"]:
        ret += RTL + "🎖 مدال جدید: " + medal_line(medal) + "\n"
    return ret + "\n" + RTL + "برای تأیید، به این پیام پاسخ دهید: /approve"


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
    if records.search.has_person(name):
        name = records.search.get_exact(name)[0]
        await send(message, records.get_profile(name), profile_buttons(context, name))
        return

    suggestions = records.search.get_matching(name) or records.search.get_similar(name)
    if not suggestions:
        await send(message, RTL + f"برای «{name}» رکوردی پیدا نشد." + "\n\n" + FOOTER, default_buttons())
        return

    request_id = remember(context, "suggestions", suggestions)
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


# ---------- editing ----------

async def disable_panel(context, editing, text=None):
    """Remove the buttons of the current panel; optionally replace its text too."""
    try:
        if text is None:
            await context.bot.edit_message_reply_markup(chat_id=editing["chat_id"], message_id=editing["message_id"], reply_markup=None)
        else:
            await context.bot.edit_message_text(text, chat_id=editing["chat_id"], message_id=editing["message_id"], reply_markup=None, disable_web_page_preview=True)
    except BadRequest:
        pass


async def send_edit_panel(context, editing):
    message = await context.bot.send_message(editing["chat_id"], edit_panel(editing), reply_markup=edit_buttons(), disable_web_page_preview=True)
    editing["message_id"] = message.message_id


async def on_edit_input(update, context):
    """Runs before every other handler: if this user is waiting to type a field value, consume the message."""
    editing = context.user_data.get("editing")
    if not editing or not editing["waiting"] or update.message.chat_id != editing["chat_id"]:
        return
    if not update.message.text:
        await send(update.message, RTL + "لطفاً مقدار را به صورت متن بفرستید.", None)
        raise ApplicationHandlerStop
    if editing["waiting"] == "medal":
        medal = parse_medal(update.message.text)
        if medal is None:
            await send(update.message, RTL + "فرمت درست نیست. مثل این بفرستید: 2024 ، APIO ، 1", None)
            raise ApplicationHandlerStop
        editing["medals"].append(medal)
    else:
        editing["changes"][editing["waiting"]] = tools.normalize(update.message.text)
    editing["waiting"] = None
    await disable_panel(context, editing, RTL + "✅ ارسال شد.")
    await send_edit_panel(context, editing)
    raise ApplicationHandlerStop


async def submit_edit(query, context, editing):
    if not editing["changes"] and not editing["medals"]:
        await query.answer("هنوز تغییری نداده‌اید.", show_alert=True)
        return
    if not ADMIN_GROUP_ID:
        await edit(query, RTL + "امکان ویرایش فعلاً فعال نیست." + "\n\n" + FOOTER, default_buttons())
        return
    review = await context.bot.send_message(ADMIN_GROUP_ID, review_panel(query.from_user, editing), disable_web_page_preview=True)
    context.bot_data.setdefault("pending", {})[review.message_id] = {"name": editing["name"], "changes": editing["changes"], "medals": editing["medals"], "approved": False}
    del context.user_data["editing"]
    await edit(query, RTL + "✅ تغییرات ثبت شد. پس از تأیید مدیران اعمال می‌شود." + "\n\n" + FOOTER, default_buttons())


async def approve(update, context):
    """/approve as a reply to a review message in the admin group; only the first approval of each message counts."""
    replied = update.message.reply_to_message
    if not replied:
        await send(update.message, RTL + "روی پیام درخواست ویرایش ریپلای کنید.", None)
        return
    pending = context.bot_data.get("pending", {}).get(replied.message_id)
    if not pending:
        await send(update.message, RTL + "این پیام درخواست ویرایش معتبری نیست.", None)
        return
    if pending["approved"]:
        return
    pending["approved"] = True
    if pending["changes"]:
        editor.apply_changes(records.data_path, pending["name"], pending["changes"])
    for medal in pending["medals"]:
        editor.add_medal(records.data_path, pending["name"], *medal)
    editor.reload_records(records)
    await send(update.message, RTL + "✅ تأیید شد و اعمال گردید.", None)


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
            name = context.user_data.get("suggestions", {})[request_id][int(index)]
        except (KeyError, IndexError, ValueError):
            await edit(query, RTL + "این پیشنهاد دیگر در دسترس نیست. دوباره نام را جست‌وجو کنید." + "\n\n" + FOOTER, default_buttons())
            return
        await edit(query, records.get_profile(name), profile_buttons(context, name))
    elif data.startswith("edit:"):
        name = context.user_data.get("profiles", {}).get(data[5:])
        if not name:
            await edit(query, RTL + "این دکمه دیگر معتبر نیست. دوباره نام را جست‌وجو کنید." + "\n\n" + FOOTER, default_buttons())
            return
        old = context.user_data.get("editing")
        if old:
            await disable_panel(context, old)
        editing = {"name": name, "changes": {}, "medals": [], "waiting": None, "chat_id": query.message.chat_id, "message_id": query.message.message_id}
        context.user_data["editing"] = editing
        await edit(query, edit_panel(editing), edit_buttons())
    elif data.startswith("field:") or data in ("edit_cancel", "edit_submit"):
        editing = context.user_data.get("editing")
        if not editing or editing["message_id"] != query.message.message_id:
            await edit(query, RTL + "این پنل ویرایش دیگر فعال نیست." + "\n\n" + FOOTER, default_buttons())
            return
        if data == "edit_cancel":
            del context.user_data["editing"]
            await edit(query, RTL + "❌ ویرایش لغو شد." + "\n\n" + FOOTER, default_buttons())
        elif data == "edit_submit":
            await submit_edit(query, context, editing)
        else:
            editing["waiting"] = data[6:]
            await edit(query, waiting_panel(editing["waiting"]), cancel_buttons())


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

    application.add_handler(MessageHandler(filters.ALL, on_edit_input), group=-1)
    application.add_handler(CommandHandler("approve", approve, filters=filters.Chat(ADMIN_GROUP_ID)))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(on_button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    application.add_error_handler(on_error)

    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=False, bootstrap_retries=-1)


if __name__ == "__main__":
    main()
