import csv

from consts import *
from search import personSearch


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


def apply_changes(records, name, changes):
    """Apply approved edits to the in-memory records (nothing is written to disk here).

    changes: {field: new_value} where field is a key of EXTRA_FIELDS.
    Each extra field is stored as a single-element list [[value]], the same shape the loader builds.
    """
    for field, value in changes.items():
        records.person_data[name][field] = [[value]]


def add_medal(records, name, year, medal_index, title):
    """Add a medal [year, medal_index, title] to the person's in-memory extra_medals."""
    records.person_data[name]["extra_medals"].append([str(year), int(medal_index), title])


def reload_records(records):
    """Write the editable data back from `records` into the CSV files and rebuild the search index.

    Only person_extra.csv and extra_medals.csv are regenerated (the competition files never change).
    A person gets a row in person_extra.csv only if at least one extra field is non-empty.
    """
    with open(records.data_path / PERSON_EXTRA_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name"] + list(EXTRA_FIELDS))
        for name, person in records.person_data.items():
            values = [person[field][0][0] if field in person else "" for field in EXTRA_FIELDS]
            if any(values):
                writer.writerow([name] + values)
    with open(records.data_path / EXTRA_MEDALS_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "year", "medal_index", "title"])
        for name, person in records.person_data.items():
            for year, medal_index, title in person.get("extra_medals", []):
                writer.writerow([name, year, medal_index, title])
    records.search = personSearch(records.person_data)
