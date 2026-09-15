"""Loading and searching the Olympiad CSV archives."""

from __future__ import annotations

import csv
import difflib
import re
from dataclasses import dataclass
from pathlib import Path


MEDALS = {
    "gold": "🥇 طلا",
    "silver": "🥈 نقره",
    "bronze": "🥉 برنز",
    "honorable_mention": "🎖️ دیپلم افتخار",
}
MEDAL_PREFIX = re.compile(r"^[🥇🥈🥉]\s*")
RTL = "\u200f"
# Keep both competition labels free of padding: the result-line formatter
# supplies one ordinary space on either side of each separator.
IOI_PERSON_LABEL = f"{RTL}IOI بین المللی"
NATIONAL_PERSON_LABEL = f"{RTL}INOI ملی"


def normalize(value: str) -> str:
    """Make Persian/Arabic spelling and whitespace comparable for a search."""
    value = value.strip().lower().translate(str.maketrans({"ي": "ی", "ى": "ی", "ك": "ک"}))
    return " ".join(value.split())


def clean_name(value: str) -> str:
    return MEDAL_PREFIX.sub("", value).strip()


def medal_from_ioi(value: str) -> str:
    return {"🥇": "🥇 طلا", "🥈": "🥈 نقره", "🥉": "🥉 برنز"}.get(value.strip()[:1], "عضو تیم")


@dataclass(frozen=True)
class Result:
    year: str
    competition: str
    category: str


class Archive:
    def __init__(
        self,
        ioi_path: str | Path,
        national_path: str | Path,
        ioi_history_path: str | Path | None = None,
        person_notes_path: str | Path | None = None,
    ):
        self.ioi_path = Path(ioi_path)
        self.national_path = Path(national_path)
        self.ioi_history_path = Path(ioi_history_path) if ioi_history_path else None
        self.person_notes_path = Path(person_notes_path) if person_notes_path else None
        self.ioi = self._load_ioi()
        self.ioi_history = self._load_ioi_history()
        self.national = self._load_national()
        self.person_notes = self._load_person_notes()

    @staticmethod
    def _rows(path: Path) -> list[dict[str, str]]:
        if not path.exists():
            return []
        with path.open(encoding="utf-8-sig", newline="") as file:
            return list(csv.DictReader(file))

    def _load_ioi(self) -> dict[str, list[tuple[str, str]]]:
        records: dict[str, list[tuple[str, str]]] = {}
        for row in self._rows(self.ioi_path):
            year = (row.get("year") or "").strip()
            members = []
            for key, value in row.items():
                if key.startswith("team_member") and value and value.strip():
                    members.append((clean_name(value), medal_from_ioi(value)))
            if year:
                records[year] = members
        return records

    def _load_ioi_history(self) -> dict[str, dict[str, str]]:
        if self.ioi_history_path is None:
            return {}
        records: dict[str, dict[str, str]] = {}
        for row in self._rows(self.ioi_history_path):
            year = (row.get("Year") or row.get("year") or "").strip()
            if year:
                records[year] = {
                    key: value.strip()
                    for key, value in row.items()
                    if key and value and value.strip()
                }
        return records

    def _load_national(self) -> dict[str, list[tuple[str, str]]]:
        records: dict[str, list[tuple[str, str]]] = {}
        for row in self._rows(self.national_path):
            year = (row.get("year") or "").strip()
            name = (row.get("name") or "").strip()
            category = (row.get("category") or "").strip().lower()
            if year and name:
                records.setdefault(year, []).append((name, MEDALS.get(category, category)))
        return records

    def _load_person_notes(self) -> dict[str, str]:
        """Load optional editable notes, indexed by normalized person name."""
        if self.person_notes_path is None:
            return {}
        notes: dict[str, str] = {}
        for row in self._rows(self.person_notes_path):
            name = (row.get("name") or "").strip()
            note = (row.get("note") or "").strip()
            if name and note:
                notes[normalize(name)] = note
        return notes

    def years(self, competition: str) -> list[str]:
        if competition == "ioi":
            years = self.ioi.keys() | self.ioi_history.keys()
        else:
            years = self.national
        return sorted(years, key=lambda y: int(y) if y.isdigit() else 0, reverse=True)

    def year_record(self, competition: str, year: str) -> list[tuple[str, str]]:
        return (self.ioi if competition == "ioi" else self.national).get(year, [])

    def ioi_history_record(self, year: str) -> dict[str, str]:
        return self.ioi_history.get(year, {})

    def has_year_record(self, competition: str, year: str) -> bool:
        if competition == "ioi":
            return year in self.ioi or year in self.ioi_history
        return year in self.national

    def person_note(self, name: str) -> str | None:
        """Return the optional note for a person, if one was supplied."""
        return self.person_notes.get(normalize(name))

    def person_history(self, query: str) -> dict[str, list[Result]]:
        needle = normalize(query)
        matches: dict[str, list[Result]] = {}
        # The RTL marker prevents Persian text following a Latin acronym from
        # flipping the direction of a result line in Telegram.
        for competition, records in ((IOI_PERSON_LABEL, self.ioi), (NATIONAL_PERSON_LABEL, self.national)):
            for year, people in records.items():
                for name, category in people:
                    if needle == normalize(name):
                        matches.setdefault(name, []).append(Result(year, competition, category))
        for results in matches.values():
            results.sort(key=lambda r: int(r.year) if r.year.isdigit() else 0, reverse=True)
        return matches

    def matching_people(self, query: str) -> list[str]:
        """Return names containing a query, for choosing the intended person."""
        needle = normalize(query)
        if not needle:
            return []
        return sorted({
            name
            for records in (self.ioi, self.national)
            for people in records.values()
            for name, _ in people
            if needle in normalize(name)
        })

    def similar_people(self, query: str, limit: int = 5) -> list[str]:
        """Return likely intended names when a name search has no matches."""
        needle = normalize(query)
        if len(needle) < 2:
            return []

        names = {
            name
            for records in (self.ioi, self.national)
            for people in records.values()
            for name, _ in people
        }
        normalized_names = {normalize(name): name for name in names}
        close_matches = difflib.get_close_matches(
            needle, normalized_names, n=limit, cutoff=0.55
        )
        return [normalized_names[name] for name in close_matches]
