import functools
from collections import Counter, defaultdict, namedtuple, OrderedDict
from itertools import combinations


Factor = namedtuple("Factor", ["elements", "levels"])


def factor(xs):
    elements, levels = [], {}
    for x in xs:
        element = levels.setdefault(x, len(levels))
        elements.append(element)
    return Factor(elements, levels)


def group_by(xs, key):
    result = defaultdict(list)
    for x in xs:
        result[key(x)].append(x)
    return result


def invert(dictionary):
    result = defaultdict(set)
    for key, value in dictionary.items():
        result[value].add(key)
    return result


CacheInfo = namedtuple("CacheInfo", ["hits", "misses", "maxsize", "currsize"])


def lru_cache(func=None, *, maxsize=64):
    if func is None:
        return functools.partial(lru_cache, maxsize=maxsize)

    cache = OrderedDict()
    hits, misses = 0, 0

    @functools.wraps(func)
    def inner(*args, **kwargs):
        key = (args, frozenset(kwargs.items()))
        if key in cache:
            nonlocal hits
            hits += 1
            cache.move_to_end(key)
        else:
            nonlocal misses
            misses += 1
            cache[key] = func(*args, **kwargs)

        result = cache[key]

        if len(cache) > maxsize:
            cache.popitem(last=False)

        return result

    def clear():
        nonlocal hits, misses
        hits, misses = 0, 0
        cache.clear()

    inner.cache_clear = clear
    inner.cache_info = lambda: CacheInfo(hits, misses, maxsize, len(cache))

    return inner


def hamming(seq1, seq2):
    assert len(seq1) == len(seq2), (
        f"Sequences are of unequal lengths: {len(seq1)} != {len(seq2)}"
    )
    return sum(ch1 != ch2 for ch1, ch2 in zip(seq1, seq2))


def build_graph(words, mismatch_percent):
    result = {i: [] for i in range(len(words))}
    for (idx1, word1), (idx2, word2) in combinations(enumerate(words), 2):
        if len(word1) != len(word2):
            continue
        elif hamming(word1, word2) * 100 <= mismatch_percent * len(word1):
            result[idx1].append(idx2)
            result[idx2].append(idx1)
    return result


def export_graph(adj_list, labels):
    graph = ["graph {"]
    for vertex, adj_vertices in adj_list.items():
        graph.append(f'{vertex} [label="{labels[vertex]}"]')
        graph.extend(f"{vertex} -- {v}" for v in adj_vertices if vertex < v)
    graph.append("}")
    return "\n".join(graph)


def find_connected_components(adj_list):
    result = []
    used = set()
    for vertex, adj_vertices in adj_list.items():
        if vertex in used:
            continue
        used.add(vertex)
        connected_component = {vertex}
        queue = list(adj_vertices)
        while queue:
            cur_vertex = queue.pop()
            if cur_vertex not in used:
                used.add(cur_vertex)
                connected_component.add(cur_vertex)
                queue.extend(adj_list[cur_vertex])
        result.append(connected_component)
    return result


def find_consensus(words):
    assert words, "List are empty"
    assert all(len(word) == len(words[0]) for word in words), (
        f"Words are of unequal lengths"
    )
    result = []
    for chars in zip(*words):
        most_common_char, _ = Counter(chars).most_common(1)[0]
        result.append(most_common_char)
    return "".join(result)


def correct_typos(words, mismatch_percent):
    result = [None] * len(words)
    graph = build_graph(words, mismatch_percent)
    connected_components = find_connected_components(graph)
    for component in connected_components:
        consensus = find_consensus([words[i] for i in component])
        for i in component:
            result[i] = consensus
    return result
