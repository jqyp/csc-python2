import functools
import random
import sut
import sys
from collections.abc import Iterator
from hypothesis import given, strategies as st
from itertools import chain, tee


@given(st.text(), st.text(), st.lists(st.text()))
def test_common_prefix(s1, s2, rest):
    strings = [s1, s2, *rest]
    prefix = sut.common_prefix(*strings)
    assert all(s.startswith(prefix) for s in strings)
    if s1 > prefix:
        non_prefix = s1[:len(prefix) + 1]
        assert not all(s.startswith(non_prefix) for s in strings)


@given(st.lists(st.integers()))
def test_factor(xs):
    elements, levels = sut.factor(xs)

    assert set(xs) == set(levels)
    assert all(element == levels[x] for element, x in zip(elements, xs))

    ordered_unique_elements = []
    for x in xs:
        if x not in ordered_unique_elements:
            ordered_unique_elements.append(x)

    assert not elements or elements[0] == 0

    assert all(
        levels[xi] + 1 == levels[xj] for xi, xj in zip(
            ordered_unique_elements, ordered_unique_elements[1:]
        )
    )


def ilen(iterable):
    if hasattr(iterable, "__len__"):
        return len(iterable)
    return sum(1 for _ in iterable)


def try_next(iterator):
    try:
        next(iterator)
    except StopIteration:
        return False
    return True


@given(st.iterables(st.integers()), st.integers(min_value=1))
def test_chunk(iterable, n):
    it1, it2, it3 = tee(iterable, 3)

    gen1 = chain.from_iterable(sut.chunked(it1, n))
    assert all(x == y for x, y in zip(it2, gen1))
    assert not try_next(it2) and not try_next(gen1)

    gen2 = sut.chunked(it3, n)
    for chunk in gen2:
        chunk_len = ilen(chunk)
        assert chunk_len == n or not try_next(gen2)


class Strategy(Iterator):
    def __or__(self, other):
        return OneOfStrategy(self, other)

    def example(self):
        return next(self)


class OneOfStrategy(Strategy):
    def __init__(self, *strategies):
        self.strategies = strategies

    def __next__(self):
        return random.choice(self.strategies).example()


class ConstStrategy(Strategy):
    def __init__(self, value):
        self.value = value

    def __next__(self):
        return self.value


class UniformFloatStrategy(Strategy):
    def __next__(self):
        return random.uniform(0, 1)


class GaussianFloatStrategy(Strategy):
    def __next__(self):
        return random.gauss(0, 1)


class BoundedFloatStrategy(Strategy):
    def __next__(self, min=sys.float_info.min, max=sys.float_info.max):
        res = random.uniform(min, max)
        while not (min < res < max):
            res = random.uniform(min, max)
        return res


class NastyFloatStrategy(Strategy):
    def __next__(self):
        return random.choice([float("inf"), -float("inf"),
                              float("nan"), +0.0, -0.0,
                              sys.float_info.min, sys.float_info.max])


def floats():
    return (UniformFloatStrategy() | GaussianFloatStrategy() |
            BoundedFloatStrategy() | NastyFloatStrategy())


def with_arguments(deco):
    @functools.wraps(deco)
    def wrapper(*dargs, **dkwargs):
        def decorator(func):
            result = deco(func, *dargs, **dkwargs)
            functools.update_wrapper(result, func)
            return result
        return decorator
    delattr(wrapper, "__wrapped__")
    return wrapper


@with_arguments
def given(func, *strategies, n_trials):
    def inner():
        for _ in range(n_trials):
            args = [strategy.example() for strategy in strategies]
            try:
                func(*args)
            except AssertionError:
                counterarguments = ', '.join(f"{arg}" for arg in args)
                print(f"Counterexample: {func.__name__}({counterarguments})",
                      file=sys.stderr)
                raise

    return inner


@given(floats(), n_trials=1024)
def test_add(x):
    assert x + 41 == 42
