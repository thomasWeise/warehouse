"""Test the warehouse time system."""


from random import randint
from typing import Final

from warehouse.instance.time import (
    EARLIEST_START,
    LATEST_END,
    check_time,
    str_to_time,
    time_to_str,
)


def test_time() -> None:
    """Check the time functions."""
    check_time(EARLIEST_START)
    check_time(LATEST_END)
    iterations: Final[int] = 100_000
    for lower, upper in ((EARLIEST_START, LATEST_END),
                         (EARLIEST_START // 10, LATEST_END * 10)):
        for src in (True, False):
            for i in range(iterations):
                time = int(randint(lower, upper)) if src else (
                    lower + (i * (upper - lower)) // (iterations - 1))

                is_ok: bool = True
                try:
                    check_time(time)
                except ValueError:
                    is_ok = False

                assert is_ok == (EARLIEST_START <= time <= LATEST_END)

                time_str: str | None = None
                try:
                    time_str = time_to_str(time)
                except ValueError:
                    assert not is_ok
                else:
                    assert is_ok

                if time_str is None:
                    continue

                time_2 = str_to_time(time_str)
                assert time == time_2
