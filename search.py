import difflib
from collections import defaultdict

import tools
from consts import *


class personSearch:
    def __init__(self, names):
        self.names = list(names)
        self.search_index = defaultdict(list)
        for person in self.names:
            self.search_index[tools.search_key(person)].append(person)

    def get_exact(self, name):
        name = tools.normalize(name)
        if name in self.search_index.get(tools.search_key(name), []):
            return [name]
        return self.search_index.get(tools.search_key(name), [])

    def has_person(self, name):
        return len(self.get_exact(name)) == 1

    def get_matching(self, name):
        key = tools.search_key(name)
        if not key:
            return []
        return sorted(person for person in self.names if key in tools.search_key(person))[:MATCHING_COUNT]

    def get_similar(self, name):
        keys = difflib.get_close_matches(tools.search_key(name), self.search_index.keys(), n=MATCHING_COUNT, cutoff=MATCHING_THRESHOLD)
        return [person for key in keys for person in self.search_index[key]][:MATCHING_COUNT]
