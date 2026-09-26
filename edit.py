from consts import *


def medal_line(medal):
    """[year, medal_index, title] -> 'سال 2024 | APIO | 🥈 نقره'."""
    return "سال " + str(medal[0]) + " | " + medal[2] + " | " + MEDAL_TEXTS[medal[1]]


def review_text(user, name, changes, medals):
    """Build the message posted to the admin group. parse_review must be able to read it back."""
    ret = REVIEW_TITLE + "\n\n"
    ret += RTL + NAME_PREFIX + name + "\n"
    ret += RTL + USER_PREFIX + str(user.id) + (" (@" + user.username + ")" if user.username else "") + "\n\n"
    for field, value in changes.items():
        ret += RTL + EXTRA_FIELDS[field] + ": " + value + "\n"
    for medal in medals:
        ret += RTL + MEDAL_PREFIX + medal_line(medal) + "\n"
    return ret + "\n" + RTL + APPROVE_HINT


def parse_review(text):
    """Inverse of review_text: message text -> (name, {field: value}, [[year, medal_index, title], ...]).

    Returns None if the text is not a review message.
    """
    if not text or not text.startswith(REVIEW_TITLE):
        return None
    name, changes, medals = None, {}, []
    labels = {label + ": ": field for field, label in EXTRA_FIELDS.items()}
    for line in text.split("\n"):
        line = line.replace(RTL, "").strip()
        if line.startswith(NAME_PREFIX):
            name = line[len(NAME_PREFIX):]
        elif line.startswith(MEDAL_PREFIX):
            year, title, medal_text = line[len(MEDAL_PREFIX):].split(" | ", 2)
            medals.append([year.replace("سال ", ""), MEDAL_TEXTS.index(medal_text), title])
        else:
            for prefix, field in labels.items():
                if line.startswith(prefix):
                    changes[field] = line[len(prefix):]
    if name is None:
        return None
    return name, changes, medals


def apply_changes(data_path, name, changes):
    """Write approved edits into data/person_extra.csv.

    name:    the person's stored name (exactly as it appears in the CSVs)
    changes: {field: new_value} where field is a key of EXTRA_FIELDS
             (highschool, university, codeforces, linkedin, note)

    Should update the person's row if it exists, or add a new row otherwise,
    leaving untouched fields as they are.
    """
    pass


def add_medal(data_path, name, year, medal_index, title):
    """Append a row `name,year,medal_index,title` to data/extra_medals.csv.

    medal_index is an int indexing MEDAL_TEXTS (0 gold, 1 silver, 2 bronze, 3 honorable mention, 4 team member).
    """
    pass


def reload_records(records):
    """Refresh the in-memory recordLoader after apply_changes so the bot shows
    the new values without a restart.
    """
    pass
