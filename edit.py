import csv
import html

import utils
from consts import *
from search import personSearch


def medal_line(medal):
    return "سال " + str(medal[0]) + " | " + medal[2] + " | " + MEDAL_TEXTS[medal[1]]


def review_text(user, name, changes, medals):
    ret = REVIEW_TITLE + "\n\n"
    ret += RTL + NAME_PREFIX + html.escape(name) + "\n"
    ret += RTL + USER_PREFIX + str(user.id) + (" (@" + html.escape(user.username) + ")" if user.username else "") + "\n\n"
    for field, value in changes.items():
        rendered = utils.codeforces_links(value) if field == "codeforces" else html.escape(value)
        ret += RTL + EXTRA_FIELDS[field] + ": " + rendered + "\n"
    for medal in medals:
        ret += RTL + MEDAL_PREFIX + html.escape(medal_line(medal)) + "\n"
    return ret + "\n" + RTL + APPROVE_HINT


def parse_review(text):
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
                    value = line[len(prefix):]
                    changes[field] = utils.split_handles(value) if field == "codeforces" else value
    if name is None:
        return None
    return name, changes, medals


def apply_changes(records, name, changes):
    for field, value in changes.items():
        records.person_data[name][field] = value


def add_medal(records, name, year, medal_index, title):
    records.person_data[name]["extra_medals"].append([str(year), int(medal_index), title])


def reload_records(records):
    with open(records.data_path / PERSON_EXTRA_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name"] + list(EXTRA_FIELDS))
        for name, person in records.person_data.items():
            values = [" ".join(person.get(field, [])) if field == "codeforces" else person.get(field, "") for field in EXTRA_FIELDS]
            if any(values):
                writer.writerow([name] + values)
    with open(records.data_path / EXTRA_MEDALS_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "year", "medal_index", "title"])
        for name, person in records.person_data.items():
            for year, medal_index, title in person.get("extra_medals", []):
                writer.writerow([name, year, medal_index, title])
    records.search = personSearch(records.person_data)
