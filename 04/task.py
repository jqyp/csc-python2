import bz2
import gzip
from collections import defaultdict
from itertools import islice, tee
from random import choice, choices


def capwords(s, sep=None):
    return (sep or " ").join(x.capitalize() for x in s.split(sep))


def cut_suffix(s, suffix):
    if suffix and s.endswith(suffix):
        return s[:-len(suffix)]
    return s


def boxed(s, fill, pad):
    width = len(s) + 2 * pad + 2
    line = fill * width
    s = f" {s} ".center(width, fill)
    return "\n".join([line, s, line])


def find_all(s, sub):
    return [i for i in range(len(s)) if s[i:].startswith(sub)]


def common_prefix(s1, s2, *rest):
    strings = (s1, s2, *rest)
    for idx, chars in enumerate(zip(*strings)):
        if not all(char == chars[0] for char in chars):
            return strings[0][:idx]
    return min(strings)


def reader(filename, **kwargs):
    if filename.endswith(".bz2"):
        return bz2.open(filename, **kwargs)
    if filename.endswith(".gz"):
        return gzip.open(filename, **kwargs)
    return open(filename, **kwargs)


def parse_shebang(filename):
    with open(filename, "rb") as file:
        return file.readline().partition(b"#!")[2].strip().decode() or None


def words(handle):
    return [word for line in handle for word in line.split(" ")]


def sliding(iterable, n, step):
    return zip(
        *(islice(it, i, None, step) for i, it in enumerate(tee(iterable, n)))
    )


def transition_matrix(language):
    result = defaultdict(list)
    for u, v, w in sliding(language, 3, 1):
        result[(u, v)].append(w)
    return result


def markov_chain(language, matrix, n):
    result = choices(language, k=2)
    while len(result) < n:
        penult_word, last_word = result[-2:]
        result.append(choice(matrix.get((penult_word, last_word), language)))
    return " ".join(result)


def snoop_says(filename, n):
    with open(filename) as file:
        language = words(file)
        return markov_chain(language, transition_matrix(language), n)
