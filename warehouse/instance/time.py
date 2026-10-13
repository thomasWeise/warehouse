"""Time utilities."""

from datetime import datetime
from typing import Final

from pycommons.types import check_int_range

#: the earliest start time for an event
EARLIEST_START: Final[int] = 1000000000000
#: the latest end time for an event
LATEST_END: Final[int] = 3500000000000


def check_time(time: int) -> int:
    """
    Check a given time stamp.

    :param time: the time stamp
    :return: the time stamp

    >>> check_time(EARLIEST_START)
    1000000000000

    >>> check_time(LATEST_END)
    3500000000000

    >>> check_time(str_to_time('2026-09-14t12:54:55.616+00:00'))
    1789390495616

    >>> check_time(1789361695615)
    1789361695615

    >>> try:
    ...     check_time("x")
    ... except TypeError as err:
    ...     print(err)
    time should be an instance of int but is str, namely 'x'.

    >>> try:
    ...     check_time(12)
    ... except ValueError as err:
    ...     print(err)
    time=12 is invalid, must be in 1000000000000..3500000000000.

    >>> try:
    ...     check_time(EARLIEST_START - 1)
    ... except ValueError as err:
    ...     print(err)
    time=999999999999 is invalid, must be in 1000000000000..3500000000000.

    >>> try:
    ...     check_time(999_999_999_999_999_999_999)
    ... except ValueError as err:
    ...     print(err)
    time=999999999999999999999 is invalid, must be in 1000000000000\
..3500000000000.

    >>> try:
    ...     check_time(LATEST_END + 1)
    ... except ValueError as err:
    ...     print(err)
    time=3500000000001 is invalid, must be in 1000000000000..3500000000000.
    """
    return check_int_range(time, "time", EARLIEST_START, LATEST_END)


def time_to_str(time: int) -> str:
    """
    Convert an event time to a string.

    :param time: the event time
    :return: the string

    >>> time_to_str(1789361695615)
    '2026-09-14 12:54:55.615'
    >>> time_to_str(1789361695616)
    '2026-09-14 12:54:55.616'
    >>> time_to_str(1789361695614)
    '2026-09-14 12:54:55.614'
    >>> time_to_str(1789361695610)
    '2026-09-14 12:54:55.61'
    >>> time_to_str(1789361695600)
    '2026-09-14 12:54:55.6'
    >>> time_to_str(1789361695000)
    '2026-09-14 12:54:55'
    >>> time_to_str(1789361640000)
    '2026-09-14 12:54'
    >>> time_to_str(1789358400000)
    '2026-09-14 12'
    >>> time_to_str(1789315200000)
    '2026-09-14 00'
    >>> time_to_str(EARLIEST_START)
    '2001-09-09 09:46:40'
    >>> time_to_str(LATEST_END)
    '2080-11-28 14:13:20'
    """
    tpart = datetime.isoformat(datetime.fromtimestamp(  # noqa: DTZ006
        check_time(time) / 1000), sep=" ", timespec="milliseconds")
    if "." in tpart:
        tpart = str.rstrip(str.rstrip(tpart, "0"), ".")
    while tpart.endswith(":00"):
        tpart = tpart[:-3]
    return tpart


def str_to_time(string: str) -> int:
    """
    Convert a time string to an event time value.

    :param string: the time string
    :return: the event time value.

    >>> str_to_time('2026-09-14T12:54:55.615')
    1789361695615
    >>> str_to_time('2026-09-14T12:54:55.615+08')
    1789361695615
    >>> str_to_time('2026-09-14T12:54:55.616+08')
    1789361695616
    >>> str_to_time('2026-09-14T12:54:55.614+08')
    1789361695614
    >>> str_to_time('2026-09-14T12:54:55.61+08')
    1789361695610
    >>> str_to_time('2026-09-14 12:54:55.61+08')
    1789361695610
    >>> str_to_time('2026-09-14 12:54:55.61')
    1789361695610
    >>> str_to_time('2026-09-14T12:54:55.6+08')
    1789361695600
    >>> str_to_time('2026-09-14T12:54:55+08')
    1789361695000
    >>> str_to_time('2026-09-14T12:54+08')
    1789361640000
    >>> str_to_time('2026-09-14T12+08')
    1789358400000
    >>> str_to_time('2026-09-14T00+08')
    1789315200000
    >>> str_to_time('2026-09-14 00+08')
    1789315200000
    >>> str_to_time('2026-09-14 00')
    1789315200000

    >>> str_to_time('2026-09-14T12:54:55.615+08:00')
    1789361695615
    >>> str_to_time('2026-09-14T12:54:55.614+08:00')
    1789361695614
    >>> str_to_time('2026-09-14t12:54:55.616+00:00')
    1789390495616
    >>> str_to_time(time_to_str(EARLIEST_START)) == EARLIEST_START
    True
    >>> str_to_time(time_to_str(LATEST_END)) == LATEST_END
    True
    """
    return check_time(round(
        1000 * datetime.fromisoformat(str.strip(string)).timestamp()))
