"""Test the warehouse time system."""


from datetime import datetime
from math import floor
from random import randint
from typing import Final

from warehouse.instance.time import (
    EARLIEST_START,
    LATEST_END,
    MAX_TIME_DELTA,
    TZ,
    check_time,
    check_timedelta,
    end_of_job,
    get_workday,
    str_to_time,
    str_to_timedelta,
    time_to_str,
    timedelta_to_str,
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


def test_time_delta() -> None:
    """Check the time delta functions."""
    iterations: Final[int] = 100_000
    for lower, upper in ((0, MAX_TIME_DELTA),
                         (-MAX_TIME_DELTA // 10, MAX_TIME_DELTA * 10)):
        for src in (True, False):
            for i in range(iterations):
                time = int(randint(lower, upper)) if src else (
                    lower + (i * (upper - lower)) // (iterations - 1))

                is_ok: bool = True
                try:
                    check_timedelta(time)
                except ValueError:
                    is_ok = False

                assert is_ok == (0 <= time <= MAX_TIME_DELTA)

                time_str: str | None = None
                try:
                    time_str = timedelta_to_str(time)
                except ValueError:
                    assert not is_ok
                else:
                    assert is_ok

                if time_str is None:
                    continue

                time_2 = str_to_timedelta(time_str)
                assert time == time_2


def test_adjust_time() -> None:
    """Test the time adjustment."""
    for can_wrap in (True, False):
        for _ in range(100_000):
            work_start = randint(1, 23 * 3600)
            work_end = randint(work_start + 1, 24 * 3600 - 1)

            while True:
                start_time = randint(EARLIEST_START,
                                     LATEST_END - work_end + work_start)
                start_stamp = datetime.fromtimestamp(start_time, tz=TZ)
                ordi = get_workday(start_stamp.toordinal())
                if get_workday(ordi) == ordi:
                    break

            total_time = randint(0, (work_end - work_start))
            assert get_workday(datetime.fromtimestamp(
                start_time + total_time, tz=TZ).toordinal()) is not None
            adjusted = end_of_job(
                start_time, total_time, can_wrap, work_start, work_end)

            end_stamp = datetime.fromtimestamp(adjusted, tz=TZ)
            ordi = end_stamp.toordinal()
            assert get_workday(ordi) == ordi
            assert (floor(end_stamp.timestamp() - start_stamp.timestamp())
                    >= total_time)
