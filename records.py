import csv
import html
from collections import defaultdict

import utils
from consts import *
from search import personSearch


class recordLoader:
    def __init__(self, data_path):
        self.data_path = data_path
        
        self.person_data = defaultdict(lambda: defaultdict(list))
        self.national_year_count = defaultdict(int)
        with open(self.data_path / NATIONAL_RECORDS_FILE, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                self.national_year_count[utils.normalize(row["year"])] += 1
                self.person_data[utils.normalize(row["name"])]["national"].append([utils.normalize(row["year"]), utils.medal_to_index(row["category"]), self.national_year_count[utils.normalize(row["year"])]])
        with open(self.data_path / IOI_RECORDS_FILE, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                for i in range(1, 5):
                    self.person_data[utils.get_ioi_name(row["team_member_" + str(i)])]["ioi"].append([utils.normalize(row["year"]), utils.get_ioi_medal(row["team_member_" + str(i)])])
        with open(self.data_path / EXTRA_MEDALS_FILE, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                self.person_data[utils.normalize(row["name"])]["extra_medals"].append([utils.normalize(row["year"]), int(row["medal_index"]), row["title"]])
        with open(self.data_path / PERSON_EXTRA_FILE, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                self.person_data[utils.normalize(row["name"])]["note"] = utils.normalize(row["note"])
                self.person_data[utils.normalize(row["name"])]["highschool"] = utils.normalize(row["highschool"])
                self.person_data[utils.normalize(row["name"])]["linkedin"] = utils.normalize(row["linkedin"])
                self.person_data[utils.normalize(row["name"])]["codeforces"] = utils.normalize(row["codeforces"])
                self.person_data[utils.normalize(row["name"])]["university"] = utils.normalize(row["university"])
        
        self.national_data = defaultdict(lambda: defaultdict(list))
        with open(self.data_path / NATIONAL_RECORDS_FILE, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                self.national_data[utils.normalize(row["year"])]["people"].append([utils.normalize(row["name"]), utils.medal_to_index(row["category"])])
                if not self.national_data[utils.normalize(row["year"])][row["category"] + "_count"]:
                    self.national_data[utils.normalize(row["year"])][row["category"] + "_count"].append(1)
                else:
                    self.national_data[utils.normalize(row["year"])][row["category"] + "_count"][0] += 1
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
                    self.ioi_data[utils.normalize(row["year"])]["people"].append([utils.get_ioi_name(row["team_member_" + str(i)]), utils.get_ioi_medal(row["team_member_" + str(i)])])
        with open(self.data_path / IOI_HISTORY_FILE, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if row["Gold"]:
                    self.ioi_data[utils.normalize(row["Year"])]["host"].append(row["Host"])
                    self.ioi_data[utils.normalize(row["Year"])]["count"].append(int(float(row["Countries"])))
                    self.ioi_data[utils.normalize(row["Year"])]["gold_count"].append(int(float(row["Gold"])))
                    self.ioi_data[utils.normalize(row["Year"])]["silver_count"].append(int(float(row["Silver"])))
                    self.ioi_data[utils.normalize(row["Year"])]["bronze_count"].append(int(float(row["Bronze"])))
                    self.ioi_data[utils.normalize(row["Year"])]["medal_rank"].append(int(float(row["Medal Rank"])))
                    self.ioi_data[utils.normalize(row["Year"])]["score_rank"].append(int(float(row["Score Rank"])))
                    self.ioi_data[utils.normalize(row["Year"])]["notes"].append(utils.normalize(row["Notes"]))
                else: 
                    self.ioi_data[utils.normalize(row["Year"])]["host"].append(row["Host"])
                    self.ioi_data[utils.normalize(row["Year"])]["count"].append(int(float(row["Countries"])))
                    self.ioi_data[utils.normalize(row["Year"])]["gold_count"].append(0)
                    self.ioi_data[utils.normalize(row["Year"])]["silver_count"].append(0)
                    self.ioi_data[utils.normalize(row["Year"])]["bronze_count"].append(0)
                    self.ioi_data[utils.normalize(row["Year"])]["medal_rank"].append(0)
                    self.ioi_data[utils.normalize(row["Year"])]["score_rank"].append(0)
                    self.ioi_data[utils.normalize(row["Year"])]["notes"].append(utils.normalize(row["Notes"]))
    
        self.search = personSearch(self.person_data)

    def get_years(self, competition):
        data = self.ioi_data if competition == "ioi" else self.national_data
        return sorted(data.keys(), reverse=True)

    def get_profile(self, name):
        exact = self.search.get_exact(name)
        name = exact[0] if len(exact) == 1 else utils.normalize(name)
        if name not in self.person_data:
            return RTL + "این فرد در دیتابیس موجود نیست" + "\n\n" + FOOTER
        ret = RTL + "🔎 نتیجهٔ جست‌وجو برای «" + html.escape(name) + "»" + "\n\n" + RTL + "👤 " + html.escape(name) + "\n"
        for medal in self.person_data[name]["national"]:
            if int(medal[0]) >= FIRST_SORTED_YEAR:
                ret += RTL + "• سال " + str(medal[0]) + " | " + "INOI" + " | " + MEDAL_TEXTS[medal[1]] + " "
                if medal[1] == 0:
                    ret += str(medal[2]) + "\n"
                elif medal[1] == 1:
                    ret += str(medal[2] - self.national_data[medal[0]]["gold_count"][0]) + "\n"
                elif medal[1] == 2:
                    ret += str(medal[2] - self.national_data[medal[0]]["gold_count"][0] -
                                          self.national_data[medal[0]]["silver_count"][0]) + "\n"
                else:
                    ret += str(medal[2] - self.national_data[medal[0]]["gold_count"][0] -
                                          self.national_data[medal[0]]["silver_count"][0] -
                                          self.national_data[medal[0]]["bronze_count"][0]) + "\n"
            else:
                ret += RTL + "• سال " + str(medal[0]) + " | " + "INOI" + " | " + MEDAL_TEXTS[medal[1]] + "\n"
        for medal in self.person_data[name]["ioi"]:
            ret += RTL + "• سال " + str(medal[0]) + " | " + "IOI" + " | " + MEDAL_TEXTS[medal[1]] + "\n"
        for medal in self.person_data[name]["extra_medals"]:
            ret += RTL + "• سال " + str(medal[0]) + " | " + html.escape(medal[2]) + " | " + MEDAL_TEXTS[medal[1]] + "\n"
        if self.person_data[name].get("highschool", ""):
            ret += RTL + "\n" + "🏫 دبیرستان: " + html.escape(self.person_data[name]["highschool"]) + "\n"
        if self.person_data[name].get("university", ""):
            ret += RTL + "\n" + "🎓 دانشگاه: " + html.escape(self.person_data[name]["university"]) + "\n"
        if self.person_data[name].get("codeforces", ""):
            ret += RTL + "\n" + "💻 هندل کدفورسز: " + utils.codeforces_link(self.person_data[name]["codeforces"]) + "\n"
        if self.person_data[name].get("linkedin", ""):
            ret += RTL + "\n" + "🔗 لینکدین: " + html.escape(self.person_data[name]["linkedin"]) + "\n"
        if self.person_data[name].get("note", ""):
            ret += RTL + "\n" + "📝 یادداشت: " + html.escape(self.person_data[name]["note"]) + "\n"
        return ret + "\n" + FOOTER

    def get_extra(self, name):
        name = utils.normalize(name)
        return {field: self.person_data[name].get(field, "") for field in EXTRA_FIELDS}

    def get_ioi(self, year):
        year = utils.normalize(year)
        if year not in self.ioi_data:
            return RTL + "این سال در دیتابیس موجود نیست" + "\n\n" + FOOTER
        ret = RTL + "🌍 نتایج IOI بین‌المللی " + str(year) + "\n\n"
        for medal in self.ioi_data[year]["people"]:
            ret += RTL + MEDAL_TEXTS[medal[1]] + " — " + medal[0] + "\n"
        ret += "\n" + RTL + "🌍 میزبان: " + self.ioi_data[year]["host"][0] + " " + utils.get_flag(self.ioi_data[year]["host"][0]) + "\n"
        ret += "\n" + RTL + "👥 کشورها: " + str(self.ioi_data[year]["count"][0]) + "\n"
        if self.ioi_data[year]["medal_rank"][0] > 0: 
            ret += "\n" + RTL + "🏅 مدال‌ها: " + MEDALS[0] + " " + str(self.ioi_data[year]["gold_count"][0]) + " | " + \
                                      MEDALS[1] + " " + str(self.ioi_data[year]["silver_count"][0]) + " | " + \
                                      MEDALS[2] + " " + str(self.ioi_data[year]["bronze_count"][0]) + "\n"
            ret += "\n" + RTL + "📈 رتبهٔ مدال: " + str(self.ioi_data[year]["medal_rank"][0]) + " | " + "رتبهٔ امتیاز: " + str(self.ioi_data[year]["score_rank"][0]) + "\n"
        if self.ioi_data[year]["notes"][0]: 
            ret += "\n" + RTL + "📝 یادداشت: " + self.ioi_data[year]["notes"][0] + "\n"
        return ret + "\n" + FOOTER

    def get_national(self, year):
        year = utils.national_year(year)
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
        