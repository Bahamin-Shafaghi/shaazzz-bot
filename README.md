# Iran Computer Olympiad Archive Bot

A Persian Telegram bot for browsing Iranian National Computer Olympiad results and Iran's IOI teams.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN='token-from-BotFather'
python bot.py
```

If the host cannot reach Telegram directly (the terminal will show timeouts
while starting), configure a proxy before starting it:

```bash
export TELEGRAM_PROXY_URL='http://proxy-host:8080'
python bot.py
```

`socks5://proxy-host:1080` is also supported after installing the requirements.
Put these values in `.env` if you want them to persist. The bot uses long polling, clears an old webhook on
startup, and retains any pending updates during a restart.

Only one copy of the bot may run from this project directory at a time. A
second `python bot.py` exits with an error instead of competing for Telegram
updates. The lock uses only Python's standard library and is released
automatically when the running process stops or crashes.

The bot uses `data/ioi_records.csv`, `data/ioi_history.csv`, `data/national_records.csv`, and `data/person_notes.csv`. Replace the sample data with your complete files. Keep the headers exactly as shown:

```csv
# ioi_records.csv
year,team_member_1,team_member_2,team_member_3,team_member_4
2025,🥇 Name,🥈 Name,🥈 Name,🥉 Name
```

```csv
# ioi_history.csv
Year,Host,Countries,Gold,Silver,Bronze,Medal Rank,Score Rank,Notes
2025,Bolivia,84,1,2,1,8,8,
```

The optional IOI history row is shown below that year's team results. Set `IOI_HISTORY_CSV` to use a file at another path.

```csv
# national_records.csv
year,category,name
1370,gold,Name
```

```csv
# person_notes.csv
name,note
Name,متن یادداشت این شخص
```

`person_notes.csv` controls the optional `📝 یادداشت` section shown in each person's search history. Add one row per person; people without a non-empty `note` are shown without this section. Restart the bot after editing this file. Set `PERSON_NOTES_CSV` to use a file at another path. If a note contains commas or line breaks, wrap it in CSV double quotes.

National categories `gold`, `silver`, `bronze`, and `honorable_mention` are displayed as Persian medal labels (including `🎖️ دیپلم افتخار`). The bot also accepts custom category text. National results are labelled `نتایج INOI ملی` in the interface. Every bot message ends with emoji-only links to the Shaazzz Telegram channel and website, with link previews disabled. When a search does not find an exact or partial name match, the bot offers selectable similar names.

Commands: `/start`, `/person نام`, `/year ioi 2025`, and `/year national 1370`.
Sending a plain name also searches the archive.
