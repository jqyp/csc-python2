import functools
import io
import itertools
import sys
import time
import traceback
from contextlib import redirect_stdout
from enum import Enum
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


class assert_raises:
    def __init__(self, expected_exc_type):
        self._expected_exc_type = expected_exc_type

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc, exc_tb):
        if exc is None:
            raise AssertionError(
                f"did not raise '{self._expected_exc_type.__name__}'"
            )
        return issubclass(exc_type, self._expected_exc_type)


class closing:
    def __init__(self, closable):
        self._closable = closable

    def __enter__(self):
        return self._closable

    def __exit__(self, *exc_info):
        self._closable.close()
        del self._closable


class print_exceptions:
    def __init__(self, file=sys.stderr):
        self._file = file

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc, exc_tb):
        traceback.print_exception(exc_type, exc, exc_tb, file=self._file)
        return True


def with_context(context_manager):
    def wrapper(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            with context_manager:
                return func(*args, **kwargs)
        return inner
    return wrapper


class Op(Enum):
    NEXT = ("Ook.", "Ook?")
    PREV = ("Ook?", "Ook.")
    INC = ("Ook.", "Ook.")
    DEC = ("Ook!", "Ook!")
    PRINT = ("Ook!", "Ook.")
    INPUT = ("Ook.", "Ook!")
    START_LOOP = ("Ook!", "Ook?")
    END_LOOP = ("Ook?", "Ook!")

    def __str__(self):
        return " ".join(self.value)


class OokException(Exception):
    """ Base class for Ook! errors. """


class OokSyntaxError(OokException):
    """ Invalid syntax. """


class OokIndexError(OokException):
    """ Memory pointer out of range. """


class OokValueError(OokException):
    """ I/O non-ASCII characters """


def ook_tokenize(source):
    it = iter(source.split())
    try:
        return [Op(op) for op in itertools.zip_longest(it, it)]
    except ValueError as err:
        raise OokSyntaxError("invalid syntax") from None


def ook_eval(source, *, memory_limit=2**16):
    def loop_helper(code, cp, direction):
        inner_loop_counter = 1
        while inner_loop_counter != 0:
            cp += direction
            if cp < 0 or cp >= len(code):
                break
            if code[cp] is Op.END_LOOP:
                inner_loop_counter -= direction
            elif code[cp] is Op.START_LOOP:
                inner_loop_counter += direction
        return cp

    code = ook_tokenize(source)
    memory = [0] * memory_limit
    mp = 0  # Memory Pointer
    cp = 0  # Code Pointer
    while cp < len(code):
        if code[cp] is Op.NEXT:
            mp += 1
        elif code[cp] is Op.PREV:
            mp -= 1
        elif code[cp] is Op.INC:
            memory[mp] += 1
        elif code[cp] is Op.DEC:
            memory[mp] -= 1
        elif code[cp] is Op.PRINT:
            if 0 <= memory[mp] <= 255:
                print(chr(memory[mp]), end="")
            else:
                raise OokValueError(f"{memory[mp]} is not ASCII code")
        elif code[cp] is Op.INPUT:
            char = sys.stdin.read(1)
            char_ord = ord(char)
            if 0 <= char_ord <= 255:
                memory[mp] = char_ord
            else:
                raise OokValueError("{char} is not in ASCII table")
        elif code[cp] is Op.START_LOOP:
            if memory[mp] == 0:
                cp = loop_helper(code, cp, 1)
                if cp >= len(code):
                    raise OokSyntaxError(f"missing Ook? Ook!")
        elif code[cp] is Op.END_LOOP:
            if memory[mp] != 0:
                cp = loop_helper(code, cp, -1)
                if cp < 0:
                    raise OokSyntaxError(f"missing Ook! Ook?")
        cp += 1

        if mp < 0 or mp >= memory_limit:
            raise OokIndexError("memory pointer out of range")


class Pipe:
    def __init__(self, server_url):
        self.server_url = server_url

    def _request(self, data=None):
        while True:
            try:
                with urlopen(self.server_url, data) as response:
                    return bytes.decode(response.read())
            except HTTPError as err:
                if err.code // 100 == 4:
                    raise
                elif err.code // 100 == 5:
                    pass
                else:
                    raise RuntimeError from err
            except URLError:
                pass

    def pull(self):
        """Receive a task (Ook! program) from the server."""
        return self._request().split("\n")

    def push(self, token, result):
        """Send the result of evaluating an Ook! program back to server."""
        data = f"{token}\n{result}".encode()
        self._request(data)

    def loop(self, n_iter, interval=15):
        """Repeatedly receive and execute tasks."""
        for _ in range(n_iter):
            start_time = time.perf_counter()

            token, source = self.pull()

            file = io.StringIO()
            with redirect_stdout(file):
                ook_eval(source)
            result = file.getvalue()

            self.push(token, result)

            end_time = time.perf_counter()
            time.sleep(max(0, interval - (end_time - start_time)))


def ook_encode(s):
    result = []
    current_ord = 0
    for char in s:
        while current_ord < ord(char):
            result.append(Op.INC)
            current_ord += 1
        while current_ord > ord(char):
            result.append(Op.DEC)
            current_ord -= 1
        result.append(Op.PRINT)
    return " ".join(str(op) for op in result)
