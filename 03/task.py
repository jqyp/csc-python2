import functools


def trace(f):
    @functools.wraps(f)
    def inner(*args, **kwargs):
        call = ", ".join(
            [str(a) for a in args] + [f"{k}={v}" for k, v in kwargs.items()]
        )
        print(f"{f.__name__}({call}) = ...")
        ret = f(*args, **kwargs)
        print(f"{f.__name__}({call}) = {ret}")
        return ret

    return inner
