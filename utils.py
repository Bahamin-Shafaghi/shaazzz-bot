from consts import *


def english_digits(string):
    return string.translate(DIGITS)


def normalize(string):
    return english_digits(string).strip(" ")


def search_key(string):
    return normalize(string).lower().translate(PERSIAN_LETTERS)


def national_year(number):
    number = normalize(number)
    if number.isdigit() and int(number) < 1000:
        return str(NATIONAL_FIRST_YEAR + int(number))
    return number


def medal_to_index(medal):
    if medal == "gold":
        return 0
    if medal == "silver":
        return 1
    if medal == "bronze":
        return 2
    if medal == "honorable_mention":
        return 3


def get_ioi_name(ioi_name):
    ioi_name = normalize(ioi_name)
    if ioi_name[0] in MEDALS:
        ioi_name = ioi_name[1:]
    return normalize(ioi_name)


def get_ioi_medal(ioi_name):
    ioi_name = normalize(ioi_name)
    for i in range(len(MEDALS)):
        if MEDALS[i] == ioi_name[0]:
            return i
    return len(MEDALS)

def get_flag(country):
    code = COUNTRY_CODES.get(normalize(country))
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in code) if code else "🌍"
