"""Telegram UI for Iran's Computer Olympiad archive."""

from __future__ import annotations

import logging
import os
import secrets
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover - the bot is deployed on Unix hosts.
    fcntl = None

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions, Update
from telegram.error import BadRequest
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.request import HTTPXRequest
from dotenv import load_dotenv

from records import Archive

ROOT = Path(__file__).parent
LOCK_FILE = ROOT / ".bot.lock"
load_dotenv(ROOT / ".env")
archive = Archive(
    os.getenv("IOI_CSV", ROOT / "data/ioi_records.csv"),
    os.getenv("NATIONAL_CSV", ROOT / "data/national_records.csv"),
    os.getenv("IOI_HISTORY_CSV", ROOT / "data/ioi_history.csv"),
    os.getenv("PERSON_NOTES_CSV", ROOT / "data/person_notes.csv"),
)
logger = logging.getLogger(__name__)
YEARS_PER_ROW = 4
# Keep the base direction RTL even when the label includes the Latin acronym.
# Without this marker, Telegram can render the whole line left-to-right on
# some clients.
NATIONAL_LABEL = "\u200fنتایج INOI ملی"
IOI_LABEL = "نتایج IOI بین‌المللی"
FOOTER = "📣 https://t.me/shaazzz\n🌐 https://shaazzz.ir"

# IOI's host names are kept in English in the source CSV.  Keeping the ISO
# codes here lets the display stay pleasant without adding another dependency
# just to render a flag.
HOST_COUNTRY_CODES = {
    "Argentina": "AR", "Australia": "AU", "Azerbaijan": "AZ", "Bolivia": "BO",
    "Bulgaria": "BG", "Canada": "CA", "China": "CN", "Croatia": "HR",
    "Egypt": "EG", "Finland": "FI", "Germany": "DE", "Greece": "GR",
    "Hungary": "HU", "Indonesia": "ID", "Iran": "IR", "Italy": "IT",
    "Japan": "JP", "Kazakhstan": "KZ", "Mexico": "MX", "Netherlands": "NL",
    "Poland": "PL", "Portugal": "PT", "Russia": "RU", "Singapore": "SG",
    "South Africa": "ZA", "South Korea": "KR", "Sweden": "SE", "Taiwan": "TW",
    "Thailand": "TH", "Turkey": "TR", "United States": "US",
}


def with_footer(text: str) -> str:
    """Add unobtrusive Shaazzz links to every bot message."""
    return f"{text}\n\n{FOOTER}"


async def reply_text(message, text: str, **kwargs) -> None:
    """Send a bot reply with its standard footer and no link previews."""
    await message.reply_text(
        with_footer(text),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
        **kwargs,
    )


def menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔎 جست‌وجوی شخص", callback_data="person")],
        [
            InlineKeyboardButton(f"🏅 {NATIONAL_LABEL}", callback_data="years:national"),
            InlineKeyboardButton(f"🌍 {IOI_LABEL}", callback_data="years:ioi"),
        ],
        [InlineKeyboardButton("ℹ️ راهنما", callback_data="help")],
    ])


def back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 منوی اصلی", callback_data="home")]])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = "🇮🇷 آرشیو المپیاد کامپیوتر ایران\n\nنام یک نفر را جست‌وجو کنید یا نتایج یک سال را ببینید."
    if update.message:
        await reply_text(update.message, text, reply_markup=menu())
    else:
        await edit_message(update.callback_query, text, menu())


async def edit_message(query, text: str, reply_markup: InlineKeyboardMarkup) -> None:
    """Edit an inline-menu message without failing on a duplicate button tap."""
    try:
        await query.edit_message_text(
            with_footer(text),
            reply_markup=reply_markup,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
    except BadRequest as error:
        # Telegram rejects an edit when a user taps the button that already
        # represents the current screen.  That is not a bot failure.
        if "Message is not modified" not in str(error):
            raise


async def show_years(query, competition: str) -> None:
    years = archive.years(competition)
    title = f"🌍 سال {IOI_LABEL}" if competition == "ioi" else f"🏅 سال {NATIONAL_LABEL}"
    if not years:
        await edit_message(query, f"{title}\n\nهنوز داده‌ای ثبت نشده است.", back())
        return
    buttons = [
        [
            InlineKeyboardButton(year, callback_data=f"year:{competition}:{year}")
            for year in years[index:index + YEARS_PER_ROW]
        ]
        for index in range(0, len(years), YEARS_PER_ROW)
    ]
    buttons.append([InlineKeyboardButton("🏠 منوی اصلی", callback_data="home")])
    await edit_message(query, title, InlineKeyboardMarkup(buttons))


async def show_record(query, competition: str, year: str) -> None:
    people = archive.year_record(competition, year)
    title = f"🌍 {IOI_LABEL} {year}" if competition == "ioi" else f"🏅 {NATIONAL_LABEL} {year}"
    lines = [title, ""] + [f"{category} — {name}" for name, category in people]
    if competition == "ioi":
        lines.extend(ioi_history_lines(archive.ioi_history_record(year)))
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("‹ بازگشت به سال‌ها", callback_data=f"years:{competition}")], [InlineKeyboardButton("🏠 منوی اصلی", callback_data="home")]])
    await edit_message(query, "\n".join(lines), keyboard)


def ioi_history_lines(record: dict[str, str]) -> list[str]:
    """Format optional country-level IOI facts beneath the team results."""
    if not record:
        return []

    def number(value: str) -> str:
        """Drop CSV's cosmetic .0 while leaving non-numeric values intact."""
        try:
            parsed = Decimal(value)
        except (InvalidOperation, ValueError):
            return value
        return str(int(parsed)) if parsed == parsed.to_integral_value() else format(parsed, "f")

    def host(value: str) -> str:
        code = HOST_COUNTRY_CODES.get(value)
        flag = "".join(chr(127397 + ord(letter)) for letter in code) if code else "🌍"
        return f"{value} {flag}"

    fields: list[str] = []
    if value := record.get("Host"):
        fields.append(f"🌍 میزبان: {host(value)}")
    if value := record.get("Countries"):
        fields.append(f"👥 کشورها: {number(value)}")

    medals = [
        f"{emoji} {number(record[key])}"
        for key, emoji in (("Gold", "🥇"), ("Silver", "🥈"), ("Bronze", "🥉"))
        if record.get(key)
    ]
    if medals:
        fields.append(f"🏅 مدال‌ها: {'  |  '.join(medals)}")

    ranks = [
        f"{label}: {number(record[key])}"
        for key, label in (("Medal Rank", "رتبهٔ مدال"), ("Score Rank", "رتبهٔ امتیاز"))
        if record.get(key)
    ]
    if ranks:
        fields.append(f"📈 {'  |  '.join(ranks)}")
    if value := record.get("Notes"):
        fields.append(f"📝 یادداشت: {value}")
    # Separate the individual facts so the history section remains easy to
    # scan in Telegram, particularly on narrow mobile screens.
    return ["", *interleave_blank_lines(fields)] if fields else []


def interleave_blank_lines(lines: list[str]) -> list[str]:
    """Insert a blank line between display rows."""
    return [line for index, line in enumerate(lines) for line in (line, "")][:-1]


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "home":
        context.user_data.pop("awaiting_person", None)
        context.user_data.pop("person_suggestions", None)
        await start(update, context)
    elif data == "person":
        context.user_data["awaiting_person"] = True
        await edit_message(query, "🔎 نام فرد را بفرستید. جست‌وجو با بخشی از نام هم کار می‌کند.", back())
    elif data == "help":
        await edit_message(query, "از دکمه‌ها استفاده کنید، یا دستورهای زیر را بفرستید:\n/person نام\n/year ioi 2025\n/year national 1370", back())
    elif data.startswith("suggest:"):
        try:
            _, request_id, suggestion_index = data.split(":", 2)
            suggestion_sets = context.user_data.get("person_suggestions", {})
            suggestions = suggestion_sets.pop(request_id, [])
            name = suggestions[int(suggestion_index)]
        except (IndexError, ValueError):
            await edit_message(query, "این پیشنهاد دیگر در دسترس نیست. دوباره نام را جست‌وجو کنید.", menu())
            return
        await edit_message(query, person_results_text(name, archive.person_history(name)), menu())
    elif data.startswith("years:"):
        await show_years(query, data.split(":", 1)[1])
    elif data.startswith("year:"):
        _, competition, year = data.split(":", 2)
        await show_record(query, competition, year)


def person_results_text(name: str, matches) -> str:
    # Set each line's base direction explicitly: result rows contain Latin
    # acronyms and years, which otherwise make Telegram render them LTR.
    rtl = "\u200f"
    lines = [f"{rtl}🔎 نتیجهٔ جست‌وجو برای «{name}»", ""]
    for person, results in matches.items():
        lines.append(f"{rtl}👤 {person}")
        lines.extend(
            f"{rtl}• سال {r.year} | {r.competition} | {r.category}"
            for r in results
        )
        if note := archive.person_note(person):
            lines.extend(["", f"{rtl}📝 یادداشت: {note}"])
    return "\n".join(lines)


async def person_result(update: Update, context: ContextTypes.DEFAULT_TYPE, name: str) -> None:
    exact_matches = archive.person_history(name)
    if exact_matches:
        await reply_text(
            update.effective_message,
            person_results_text(name, exact_matches), reply_markup=menu()
        )
        return

    suggestions = archive.matching_people(name) or archive.similar_people(name)
    if not suggestions:
        await reply_text(
            update.effective_message,
            f"برای «{name}» رکوردی پیدا نشد.", reply_markup=menu()
        )
        return

    request_id = secrets.token_urlsafe(6)
    suggestion_sets = context.user_data.setdefault("person_suggestions", {})
    suggestion_sets[request_id] = suggestions
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(person, callback_data=f"suggest:{request_id}:{index}")]
        for index, person in enumerate(suggestions)
    ] + [[InlineKeyboardButton("🏠 منوی اصلی", callback_data="home")]])
    await reply_text(
        update.effective_message,
        f"منظورتان از «{name}» کدام فرد است؟",
        reply_markup=keyboard,
    )


async def text_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # A text message used to be ignored unless the user had first pressed the
    # search button. Searching by default makes the bot useful in both private
    # chats and groups, and avoids the appearance that it received no update.
    context.user_data.pop("awaiting_person", None)
    await person_result(update, context, update.message.text)


async def person_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await reply_text(update.message, "نمونه: /person امیرعلی عسگری", reply_markup=menu())
        return
    await person_result(update, context, " ".join(context.args))


async def year_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 2 or context.args[0] not in {"ioi", "national"}:
        await reply_text(
            update.message,
            "نمونه: /year ioi 2025 یا /year national 1370", reply_markup=menu()
        )
        return
    competition, year = context.args
    people = archive.year_record(competition, year)
    if not archive.has_year_record(competition, year):
        await reply_text(update.message, "برای این سال رکوردی پیدا نشد.", reply_markup=menu())
        return
    title = f"🌍 {IOI_LABEL} {year}" if competition == "ioi" else f"🏅 {NATIONAL_LABEL} {year}"
    lines = [title, ""] + [f"{category} — {name}" for name, category in people]
    if competition == "ioi":
        lines.extend(ioi_history_lines(archive.ioi_history_record(year)))
    await reply_text(
        update.message,
        "\n".join(lines),
        reply_markup=menu(),
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Keep polling and leave a useful traceback in the terminal on errors."""
    logger.exception("Unhandled error while processing update %r", update, exc_info=context.error)


class AlreadyRunningError(RuntimeError):
    """Raised when another copy of this bot holds the process lock."""


def acquire_instance_lock():
    """Acquire an advisory lock held until this process exits.

    ``flock`` is released automatically if the process crashes, so a stale
    lock file never prevents a later restart.
    """
    if fcntl is None:
        raise RuntimeError("Single-instance locking requires a Unix-like host.")
    lock_file = LOCK_FILE.open("w")
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock_file.close()
        raise AlreadyRunningError("Another bot instance is already running.") from None
    lock_file.write(str(os.getpid()))
    lock_file.flush()
    return lock_file


def run_bot() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN in your environment or .env loader.")
    proxy_url = os.getenv("TELEGRAM_PROXY_URL")
    # Telegram is not directly reachable from every hosting network. A proxy
    # can be supplied as, for example, http://host:port or socks5://host:port.
    request_options = dict(
        proxy=proxy_url,
        connect_timeout=20.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=10.0,
    )
    # PTB uses a separate client for the long-polling getUpdates request.
    # Give both clients the same proxy and timeout configuration.
    request = HTTPXRequest(connection_pool_size=8, **request_options)
    get_updates_request = HTTPXRequest(connection_pool_size=1, **request_options)
    app = (
        Application.builder()
        .token(token)
        .request(request)
        .get_updates_request(get_updates_request)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("person", person_command))
    app.add_handler(CommandHandler("year", year_command))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_search))
    app.add_error_handler(error_handler)
    logger.info(
        "Starting Telegram polling%s.",
        " through the configured proxy" if proxy_url else "",
    )
    # Retain updates sent while the process was restarting and keep retrying
    # transient Telegram/network failures instead of silently exiting.
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=False,
        bootstrap_retries=-1,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        lock_file = acquire_instance_lock()
    except AlreadyRunningError as error:
        logger.error("%s", error)
        sys.exit(1)
    with lock_file:
        run_bot()
