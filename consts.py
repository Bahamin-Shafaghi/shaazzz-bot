YEARS_PER_ROW = 4
NATIONAL_FIRST_YEAR = 1369  # year of دوره 0; دوره N was held in NATIONAL_FIRST_YEAR + N
FOOTER = "📣 https://t.me/shaazzz\n🌐 https://shaazzz.ir"
MEDALS = ["🥇", "🥈", "🥉", "🎖"]
MEDAL_TEXTS = ["🥇 طلا", "🥈 نقره", "🥉 برنز", "🎖 دیپلم افتخار", "عضو تیم"]
IOI_HISTORY_FILE = "ioi_history.csv"
IOI_RECORDS_FILE = "ioi_records.csv"
NATIONAL_RECORDS_FILE = "national_records.csv"
PERSON_EXTRA_FILE = "person_extra.csv"
EXTRA_MEDALS_FILE = "extra_medals.csv"
FIRST_SORTED_YEAR = 1386
MATCHING_THRESHOLD = 0.6
MATCHING_COUNT = 5
EXTRA_FIELDS = {
    "highschool": "🏫 دبیرستان",
    "university": "🎓 دانشگاه",
    "codeforces": "💻 هندل کدفورسز",
    "linkedin": "🔗 لینکدین",
    "note": "📝 یادداشت",
}
LTR = "\u200e"
RTL = "\u200f"
COUNTRY_CODES = {
    "Argentina": "AR", "Australia": "AU", "Azerbaijan": "AZ", "Bolivia": "BO",
    "Bulgaria": "BG", "Canada": "CA", "China": "CN", "Croatia": "HR",
    "Egypt": "EG", "Finland": "FI", "Germany": "DE", "Greece": "GR",
    "Hungary": "HU", "Indonesia": "ID", "Iran": "IR", "Italy": "IT",
    "Japan": "JP", "Kazakhstan": "KZ", "Mexico": "MX", "Netherlands": "NL",
    "Poland": "PL", "Portugal": "PT", "Russia": "RU", "Singapore": "SG",
    "South Africa": "ZA", "South Korea": "KR", "Sweden": "SE", "Taiwan": "TW",
    "Thailand": "TH", "Turkey": "TR", "United States": "US", "Uzbekistan": "UZ",
}

SEARCH_WORD = "جستجو"
IOI_WORD = "جهانی"
NATIONAL_WORD = "ملی"

REVIEW_TITLE = "📝 درخواست ویرایش"
NAME_PREFIX = "👤 فرد: "
USER_PREFIX = "🆔 کاربر: "
MEDAL_PREFIX = "🎖 مدال جدید: "
APPROVE_HINT = "برای تأیید، به این پیام پاسخ دهید: /approve"
APPROVED_MARK = "✅ تأیید شد"

DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹" "٠١٢٣٤٥٦٧٨٩", "0123456789" * 2)
PERSIAN_LETTERS = str.maketrans("ئيىكأإآؤة", "یییکاااوه", "\u0621\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0670\u200c\u200d\u200e\u200f ")