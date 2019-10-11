from itertools import count, groupby
from typing import NamedTuple, List, Mapping


def common_prefix(s1, s2, *rest):
    strings = (s1, s2, *rest)
    for idx, chars in enumerate(zip(*strings)):
        if not all(char == chars[0] for char in chars):
            return strings[0][:idx]
    return min(strings)


class Factor(NamedTuple):
    elements: List
    levels: Mapping


def factor(xs):
    elements, levels = [], {}
    for x in xs:
        element = levels.setdefault(x, len(levels))
        elements.append(element)
    return Factor(elements, levels)


def chunked(iterable, n):
    c = count()
    return (g for _, g in groupby(iterable, lambda _: next(c) // n))
