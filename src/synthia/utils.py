import datetime
import random
import sys
import time
from functools import wraps
from time import sleep
from typing import Any, Callable, Literal, ParamSpec, TypeVar

T = TypeVar("T")
T1 = TypeVar("T1")
T2 = TypeVar("T2")

P = ParamSpec("P")
R = TypeVar("R")


def timeit(func: Callable[P, R]):
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        log(f"Execution time of {func.__name__}: {execution_time:.6f} seconds")
        return result
    return wrapper


def iso_timestamp_now() -> str:
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    iso_now = now.isoformat()
    return iso_now


def log(
        msg: str,
        *values: object,
        sep: str | None = " ",
        end: str | None = "\n",
        file: Any | None = None,
        flush: Literal[False] = False
    ):
    print(f"[{iso_timestamp_now()}] " + msg, *values, sep=sep, end=end, file=file, flush=flush)


def retry(max_retries: int | None, retry_exceptions: list[type]):
    assert max_retries is None or max_retries > 0

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        def wrapper(*args: P.args, **kwargs: P.kwargs):
            max_retries__ = max_retries or sys.maxsize  # TODO: fix this ugly thing
            for tries in range(max_retries__ + 1):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    if any(isinstance(e, exception_t) for exception_t in retry_exceptions):
                        func_name = func.__name__
                        log(f"An exception occurred in '{func_name} on try {tries}': {e}, but we'll retry.")
                        if tries < max_retries__:
                            delay = (1.4 ** tries) + random.uniform(0, 1)
                            sleep(delay)
                            continue
                    raise e
            raise Exception("Unreachable")
        return wrapper
    return decorator