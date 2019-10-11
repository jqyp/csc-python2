from itertools import chain, count, groupby, islice, repeat, tee


def ilen(iterable):
    if hasattr(iterable, "__len__"):
        return len(iterable)
    return sum(1 for _ in iterable)


def find(iterable, p):
    try:
        return next(filter(p, iterable))
    except StopIteration:
        raise ValueError("not found") from None


def chunked(iterable, n):
    c = count()
    return (g for _, g in groupby(iterable, lambda _: next(c) // n))


def rle(iterable):
    return ((k, ilen(g)) for k, g in groupby(iterable))


def drop(n, iterable):
    return islice(iterable, n, None)


def intersperse(delimiter, iterable):
    return drop(1, chain.from_iterable(zip(repeat(delimiter), iterable)))


class peekable:
    def __init__(self, iterable):
        self._it = iter(iterable)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._it)

    def peek(self):
        self._it, jt = tee(self._it)
        return next(jt)


def take(n, iterable):
    return islice(iterable, n)


def padded(iterable, fillvalue, n):
    return take(n, chain(iterable, repeat(fillvalue)))


def sliding(iterable, n, step):
    return zip(
        *(islice(it, i, None, step) for i, it in enumerate(tee(iterable, n)))
    )
