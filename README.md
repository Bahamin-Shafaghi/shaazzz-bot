# Shaazzz Bot

A Persian Telegram bot for browsing Iranian National Computer Olympiad (INOI) results and Iran's IOI teams.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python bot.py
```

Create a `.env` file next to `bot.py`:

```env
TELEGRAM_BOT_TOKEN=token-from-BotFather
# optional, if the host cannot reach Telegram directly:
TELEGRAM_PROXY_URL=socks5://127.0.0.1:1080
# group where edit requests are sent and approved with /approve (bot must be a member):
TELEGRAM_ADMIN_GROUP_ID=-1001234567890
```

`TELEGRAM_PROXY_URL` accepts `http://host:port` or `socks5://[user:pass@]host:port` and is used for both API calls and `getUpdates`. MTProto (`t.me/proxy?...`) links are not supported; the Bot API needs an HTTP/SOCKS5 proxy. Requires Python 3.10+ (python-telegram-bot 22 also works on 3.14). Only one instance of the bot may poll at a time.

## Commands

| Command | Description |
| --- | --- |
| `/start` | Main menu (with the ℹ️ راهنما button) |
| `/help` | Help text |
| `جستجو نام` | Search a person and show their profile; without a name the bot asks for one |
| `جهانی` | IOI year grid; `جهانی 2025` shows that year's team directly |
| `ملی` | INOI year grid; `ملی 1404` shows that year, `ملی 35` is interpreted as دوره 35 (= 1369 + 35) |

Persian/Arabic digits are accepted everywhere; the bot always writes English digits. Plain text that is not one of these commands is ignored. Link previews are disabled on every message and each message ends with the channel/site footer.

## Search

Search lives in `search.py` (`personSearch`). Names are compared through `tools.search_key`, which unifies Persian spelling variants (ئ/ي/ى→ی, ك→ک, أ/إ/آ→ا, ؤ→و, ة→ه, drops hamza, tashkeel, ZWNJ and spaces, lowercases Latin), so `عطایی` finds `عطائی` and `محمدحسین` finds `محمد حسین`.

An exact match opens the profile directly. Otherwise every name is scored and the top `MATCHING_COUNT` are offered as buttons:

1. exact key match
2. prefix match
3. substring match
4. subsequence match (missing letters, e.g. `محدحسین`)
5. `difflib` similarity ratio ≥ `MATCHING_THRESHOLD`

The query is also matched word by word against the name's words in any order (`باطنی محمد` finds `محمد حسین باطنی`); shorter names win ties. Suggestion buttons from the last 20 searches per user stay usable until the bot restarts. `MATCHING_COUNT` and `MATCHING_THRESHOLD` are in `consts.py`.

## Editing profiles

Every profile has a `✏️ ویرایش اطلاعات` button. It opens an editing panel listing the five extra fields (current values, `—` when empty) with one button per field, a `🎖 مدال جدید` button, plus `❌ لغو` / `✅ ثبت`. Tapping a field replaces the panel with just a prompt and a cancel button; the next message the user sends (any text, even a command) becomes the new value. A new medal is entered in one message as `سال ، عنوان ، شمارهٔ مدال` (e.g. `2024 ، APIO ، 1`, index into `MEDAL_TEXTS`). The old panel is then replaced by "✅ ارسال شد." with no buttons and a fresh panel is sent showing the pending values marked `🆕`. Fields can be changed as many times as wanted; nothing is written until approval.

`✅ ثبت` posts the request (user id, person, changed fields) to the group in `TELEGRAM_ADMIN_GROUP_ID` and tells the user it awaits admin approval. An admin approves by replying `/approve` to that message; `/approve` only works in that group, only as a reply to a pending request, and only the first approval of a request has any effect. On approval `edit.apply_changes(data_path, name, changes)`, `edit.add_medal(data_path, name, year, medal_index, title)` and `edit.reload_records(records)` in `edit.py` are called (currently stubs to be implemented). Pending requests, in-progress edits and suggestion lists are persisted to `bot_state.pickle` (git-ignored), so requests can be approved any time later, even after restarts; there is no limit on how many can be pending.

## Code layout

| File | Role |
| --- | --- |
| `bot.py` | Telegram handlers, keyboards, command parsing |
| `records.py` | `recordLoader`: loads the CSVs, builds year/profile texts |
| `search.py` | `personSearch`: exact/ranked fuzzy name search |
| `edit.py` | applying approved profile edits to the CSV (stubs) |
| `tools.py` | digit normalisation, search key, دوره→year, flags |
| `consts.py` | file names, medal labels, search constants, country codes |

## Data

All files are in `data/`, UTF-8 (a BOM is tolerated), with these headers:

```csv
# national_records.csv  (sorted by year descending; rows of one year keep gold→silver→bronze→honorable_mention order)
year,category,name
1404,gold,Name
```

`category` is `gold`, `silver`, `bronze` or `honorable_mention`. The per-medal rank shown in a profile (e.g. `🥇 طلا 3`) is the row position inside that medal group and is shown from `FIRST_SORTED_YEAR` (1386) on.

```csv
# ioi_records.csv
year,team_member_1,team_member_2,team_member_3,team_member_4
2025,🥇 Name,🥈 Name,🥈 Name,🥉 Name
```

Each member is prefixed with the medal emoji (🥇 🥈 🥉 🎖) or nothing for no medal.

```csv
# ioi_history.csv
Year,Host,Countries,Gold,Silver,Bronze,Medal Rank,Score Rank,Notes
2025,Bolivia,84,1,2,1,8,8,
```

Shown under the team of that year: host with flag (from `COUNTRY_CODES`), number of countries, medal counts, ranks and the note. Empty cells are skipped.

```csv
# extra_medals.csv
name,year,medal_index,title
```

Additional medals (e.g. other olympiads) listed in a profile; `medal_index` is 0–3 for 🥇 🥈 🥉 🎖.

```csv
# person_extra.csv
name,note,highschool,linkedin,codeforces,university
```

Optional profile fields, shown only when non-empty: 🏫 دبیرستان, 🎓 دانشگاه, 💻 هندل کدفورسز, 🔗 لینکدین, 📝 یادداشت. Wrap values containing commas in double quotes. Restart the bot after editing any data file.
