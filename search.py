import difflib
from collections import defaultdict

import tools
from consts import *


def is_subsequence(short, long):
    it = iter(long)
    return all(char in it for char in short)


def string_score(query, target):
    if query == target:
        return 1.0
    if target.startswith(query):
        return 0.95
    if query in target:
        return 0.85
    if len(query) >= 3 and is_subsequence(query, target):
        return 0.6 + 0.2 * len(query) / len(target)
    matcher = difflib.SequenceMatcher(None, query, target)
    if matcher.real_quick_ratio() < MATCHING_THRESHOLD or matcher.quick_ratio() < MATCHING_THRESHOLD:
        return 0.0
    ratio = matcher.ratio()
    return ratio if ratio >= MATCHING_THRESHOLD else 0.0


class personSearch:
    def __init__(self, names):
        self.names = list(names)
        self.search_index = defaultdict(list)
        self.keys = {}
        self.tokens = {}
        for person in self.names:
            key = tools.search_key(person)
            self.search_index[key].append(person)
            self.keys[person] = key
            self.tokens[person] = [tools.search_key(word) for word in tools.normalize(person).split()]

    def get_exact(self, name):
        name = tools.normalize(name)
        if name in self.search_index.get(tools.search_key(name), []):
            return [name]
        return self.search_index.get(tools.search_key(name), [])

    def has_person(self, name):
        return len(self.get_exact(name)) == 1

    def score(self, query_key, query_tokens, person):
        full = string_score(query_key, self.keys[person])
        token_scores = [max(string_score(query, token) for token in self.tokens[person]) for query in query_tokens]
        tokens = sum(token_scores) / len(token_scores) if all(token_scores) else 0.0
        best = max(full, tokens)
        if best < MATCHING_THRESHOLD:
            return 0.0
        return best - 0.001 * len(self.keys[person])

    def get_matching(self, name):
        query_key = tools.search_key(name)
        query_tokens = [tools.search_key(word) for word in tools.normalize(name).split()]
        if not query_key or not query_tokens:
            return []
        scored = ((self.score(query_key, query_tokens, person), person) for person in self.names)
        ranked = sorted(((score, person) for score, person in scored if score > 0), key=lambda item: (-item[0], item[1]))
        return [person for score, person in ranked[:MATCHING_COUNT]]

    def get_similar(self, name):
        return self.get_matching(name)
