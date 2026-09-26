from consts import *


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
