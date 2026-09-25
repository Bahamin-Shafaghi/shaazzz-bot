import csv
import difflib
from collections import defaultdict

import tools
from consts import *


class recordLoader:
    def __init__(self, data_path):
        self.data_path = data_path
        
        self.person_data = defaultdict(lambda: defaultdict(list))
        self.national_year_count = defaultdict(int)
        with open(self.data_path / NATIONAL_RECORDS_FILE, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                self.national_year_count[tools.normalize(row["year"])] += 1
                self.person_data[tools.normalize(row["name"])]["national"].append([tools.normalize(row["year"]), tools.medal_to_index(row["category"]), self.national_year_count[tools.normalize(row["year"])]])
        with open(self.data_path / IOI_RECORDS_FILE, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                for i in range(1, 5):
                    self.person_data[tools.get_ioi_name(row["team_member_" + str(i)])]["ioi"].append([tools.normalize(row["year"]), tools.get_ioi_medal(row["team_member_" + str(i)])])
        with open(self.data_path / EXTRA_MEDALS_FILE, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                self.person_data[tools.normalize(row["name"])]["extra_medals"].append([tools.normalize(row["year"]), row["medal_index"], row["title"]])
        with open(self.data_path / PERSON_EXTRA_FILE, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                self.person_data[tools.normalize(row["name"])]["note"].append([tools.normalize(row["note"])])
                self.person_data[tools.normalize(row["name"])]["highschool"].append([tools.normalize(row["highschool"])])
                self.person_data[tools.normalize(row["name"])]["linkedin"].append([tools.normalize(row["linkedin"])])
                self.person_data[tools.normalize(row["name"])]["codeforces"].append([tools.normalize(row["codeforces"])])
                self.person_data[tools.normalize(row["name"])]["university"].append([tools.normalize(row["university"])])
        
        self.national_data = defaultdict(lambda: defaultdict(list))
        with open(self.data_path / NATIONAL_RECORDS_FILE, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                self.national_data[tools.normalize(row["year"])]["people"].append([tools.normalize(row["name"]), tools.medal_to_index(row["category"])])
                if len(self.national_data[tools.normalize(row["year"])][row["category"] + "_count"]) == 0:
                    self.national_data[tools.normalize(row["year"])][row["category"] + "_count"].append(1)
                else:
                    self.national_data[tools.normalize(row["year"])][row["category"] + "_count"][0] += 1
        for year in self.national_data:
            if not self.national_data[year]["gold_count"]:
                self.national_data[year]["gold_count"].append(0)
            if not self.national_data[year]["silver_count"]:
                self.national_data[year]["silver_count"].append(0)
            if not self.national_data[year]["bronze_count"]:
                self.national_data[year]["bronze_count"].append(0)
            if not self.national_data[year]["honorable_mention_count"]:
                self.national_data[year]["honorable_mention_count"].append(0)

        self.ioi_data = defaultdict(lambda: defaultdict(list))
        with open(self.data_path / IOI_RECORDS_FILE, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                for i in range(1, 5):
                    self.ioi_data[tools.normalize(row["year"])]["people"].append([tools.get_ioi_name(row["team_member_" + str(i)]), tools.get_ioi_medal(row["team_member_" + str(i)])])
        with open(self.data_path / IOI_HISTORY_FILE, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if len(row["Gold"]) > 0: 
                    self.ioi_data[tools.normalize(row["Year"])]["host"].append(row["Host"])
                    self.ioi_data[tools.normalize(row["Year"])]["count"].append(int(float(row["Countries"])))
                    self.ioi_data[tools.normalize(row["Year"])]["gold_count"].append(int(float(row["Gold"])))
                    self.ioi_data[tools.normalize(row["Year"])]["silver_count"].append(int(float(row["Silver"])))
                    self.ioi_data[tools.normalize(row["Year"])]["bronze_count"].append(int(float(row["Bronze"])))
                    self.ioi_data[tools.normalize(row["Year"])]["medal_rank"].append(int(float(row["Medal Rank"])))
                    self.ioi_data[tools.normalize(row["Year"])]["score_rank"].append(int(float(row["Score Rank"])))
                    self.ioi_data[tools.normalize(row["Year"])]["notes"].append(tools.normalize(row["Notes"]))
                else: 
                    self.ioi_data[tools.normalize(row["Year"])]["host"].append(row["Host"])
                    self.ioi_data[tools.normalize(row["Year"])]["count"].append(int(float(row["Countries"])))
                    self.ioi_data[tools.normalize(row["Year"])]["gold_count"].append(0)
                    self.ioi_data[tools.normalize(row["Year"])]["silver_count"].append(0)
                    self.ioi_data[tools.normalize(row["Year"])]["bronze_count"].append(0)
                    self.ioi_data[tools.normalize(row["Year"])]["medal_rank"].append(0)
                    self.ioi_data[tools.normalize(row["Year"])]["score_rank"].append(0)
                    self.ioi_data[tools.normalize(row["Year"])]["notes"].append(tools.normalize(row["Notes"]))
    
        self.search_index = defaultdict(list)
        for person in self.person_data:
            self.search_index[tools.search_key(person)].append(person)

    def get_exact(self, name):
        name = tools.normalize(name)
        if name in self.person_data:
            return [name]
        return self.search_index.get(tools.search_key(name), [])

    def has_person(self, name):
        return len(self.get_exact(name)) == 1

    def get_matching(self, name):
        key = tools.search_key(name)
        if not key:
            return []
        return sorted(person for person in self.person_data if key in tools.search_key(person))

    def get_similar(self, name):
        keys = difflib.get_close_matches(tools.search_key(name), self.search_index.keys(), n=MATCHING_COUNT, cutoff=MATCHING_THRESHOLD)
        return [person for key in keys for person in self.search_index[key]][:MATCHING_COUNT]

    def get_years(self, competition):
        data = self.ioi_data if competition == "ioi" else self.national_data
        return sorted(data.keys(), reverse=True)

    def get_profile(self, name):
        exact = self.get_exact(name)
        name = exact[0] if len(exact) == 1 else tools.normalize(name)
        if name not in self.person_data:
            return RTL + "این فرد در دیتابیس موجود نیست" + "\n\n" + FOOTER
        ret = RTL + "🔎 نتیجهٔ جست‌وجو برای «" + name + "»" + "\n\n" + RTL + "👤 " + name + "\n"
        for medal in self.person_data[name]["national"]:
            if int(medal[0]) >= FIRST_SORTED_YEAR:
                if medal[1] == 0:
                    ret += RTL + "• سال " + str(medal[0]) + " | " + "INOI" + " | " + MEDALS[
                        medal[1]] + " طلا " + str(medal[2]) + "\n"
                elif medal[1] == 1:
                    ret += RTL + "• سال " + str(medal[0]) + " | " + "INOI" + " | " + MEDALS[
                        medal[1]] + " نقره " + str(medal[2] - self.national_data[medal[0]]["gold_count"][0]) + "\n"
                elif medal[1] == 2:
                    ret += RTL + "• سال " + str(medal[0]) + " | " + "INOI" + " | " + MEDALS[
                        medal[1]] + " برنز " + str(medal[2] - self.national_data[medal[0]]["gold_count"][0] -
                                                    self.national_data[medal[0]]["silver_count"][0]) + "\n"
                else:
                    ret += RTL + "• سال " + str(medal[0]) + " | " + "INOI" + " | " + MEDALS[
                        medal[1]] + " دیپلم " + str(medal[2] - self.national_data[medal[0]]["gold_count"][0] -
                                                    self.national_data[medal[0]]["silver_count"][0] -
                                                    self.national_data[medal[0]]["bronze_count"][0]) + "\n"
            else:
                ret += RTL + "• سال " + str(medal[0]) + " | " + "INOI" + " | " + MEDAL_TEXTS[medal[1]] + "\n"
        for medal in self.person_data[name]["ioi"]:
            ret += RTL + "• سال " + str(medal[0]) + " | " + "IOI" + " | " + MEDAL_TEXTS[medal[1]] + "\n"
        for medal in self.person_data[name]["extra_medals"]:
            ret += RTL + "• سال " + str(medal[0]) + " | " + medal[2] + " | " + MEDAL_TEXTS[medal[1]] + "\n"
        if "highschool" in self.person_data[name] and self.person_data[name]["highschool"][0][0]:
            ret += RTL + "\n" + "🏫 دبیرستان: " + self.person_data[name]["highschool"][0][0] + "\n"
        if "university" in self.person_data[name] and self.person_data[name]["university"][0][0]:
            ret += RTL + "\n" + "🎓 دانشگاه: " + self.person_data[name]["university"][0][0] + "\n"
        if "codeforces" in self.person_data[name] and self.person_data[name]["codeforces"][0][0]:
            ret += RTL + "\n" + "💻 هندل کدفورسز: " + self.person_data[name]["codeforces"][0][0] + "\n"
        if "linkedin" in self.person_data[name] and self.person_data[name]["linkedin"][0][0]:
            ret += RTL + "\n" + "🔗 لینکدین: " + self.person_data[name]["linkedin"][0][0] + "\n"
        if "note" in self.person_data[name] and self.person_data[name]["note"][0][0]:
            ret += RTL + "\n" + "📝 یادداشت: " + self.person_data[name]["note"][0][0] + "\n"
        return ret + "\n" + FOOTER

    def get_ioi(self, year):
        year = tools.normalize(year)
        if year not in self.ioi_data:
            return RTL + "این سال در دیتابیس موجود نیست" + "\n\n" + FOOTER
        ret = RTL + "🌍 نتایج IOI بین‌المللی " + str(year) + "\n\n"
        for medal in self.ioi_data[year]["people"]:
            ret += RTL + MEDAL_TEXTS[medal[1]] + " — " + medal[0] + "\n"
        ret += "\n" + RTL + "🌍 میزبان: " + self.ioi_data[year]["host"][0] + " " + tools.get_flag(self.ioi_data[year]["host"][0]) + "\n"
        ret += "\n" + RTL + "👥 کشورها: " + str(self.ioi_data[year]["count"][0]) + "\n"
        if self.ioi_data[year]["medal_rank"][0] > 0: 
            ret += "\n" + RTL + "🏅 مدال‌ها: " + MEDALS[0] + " " + str(self.ioi_data[year]["gold_count"][0]) + " | " + \
                                      MEDALS[1] + " " + str(self.ioi_data[year]["silver_count"][0]) + " | " + \
                                      MEDALS[2] + " " + str(self.ioi_data[year]["bronze_count"][0]) + "\n"
            ret += "\n" + RTL + "📈 رتبهٔ مدال: " + str(self.ioi_data[year]["medal_rank"][0]) + " | " + "رتبهٔ امتیاز: " + str(self.ioi_data[year]["score_rank"][0]) + "\n"
        if len(self.ioi_data[year]["notes"][0]) > 0: 
            ret += "\n" + RTL + "📝 یادداشت: " + self.ioi_data[year]["notes"][0] + "\n"
        return ret + "\n" + FOOTER

    def get_national(self, year):
        year = tools.national_year(year)
        if year not in self.national_data:
            return RTL + "این سال در دیتابیس موجود نیست" + "\n\n" + FOOTER
        ret = RTL + "🏅 نتایج INOI ملی " + str(year) + " (دورهٔ " + str(int(year) - NATIONAL_FIRST_YEAR) + ")" + "\n"
        ret += "\n" + RTL + "🏅 مدال‌ها: " + MEDALS[0] + " " + str(self.national_data[year]["gold_count"][0]) + " | " + \
                                     MEDALS[1] + " " + str(self.national_data[year]["silver_count"][0]) + " | " + \
                                     MEDALS[2] + " " + str(self.national_data[year]["bronze_count"][0]) + " | " + \
                                     MEDALS[3] + " " + str(self.national_data[year]["honorable_mention_count"][0]) + "\n\n"
        for medal in self.national_data[year]["people"]:
            ret += RTL + MEDAL_TEXTS[medal[1]] + " — " + medal[0] + "\n"
        return ret + "\n" + FOOTER
        