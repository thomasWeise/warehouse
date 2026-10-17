"""
Time utilities.

In our simulation, the time is represented as integer values `int`
representing dates and times in millisecond resolution, i.e., a time
unit of `1` corresponds to one millisecond.
However, we store and retrieve times as ISO timestamps, where we clamp
off zero components that are not used.
Furthermore, as time zone, we by default use `Asia/Shanghai` time.
This means that a date/time without UTC offset, i.e., without something
like `"+08:00"` or `"-10:00"`, is treated as Shanghai time.
Of course, you still provide time stamps in UTC time by using suffix
`"+00:00"`.
"""

from datetime import datetime, timedelta
from math import floor
from typing import Final
from zoneinfo import ZoneInfo

from pycommons.types import check_int_range

#: the earliest start time for an event
EARLIEST_START: Final[int] = 1000000000000
#: the latest end time for an event
LATEST_END: Final[int] = 3500000000000

#: the internal time zone information record
__TZ: Final[ZoneInfo] = ZoneInfo("Asia/Shanghai")


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


def __trim(text: str) -> str:
    """
    Trim a time or time delta string.

    :param text: the text
    :return: the trimmed text
    """
    return str.removesuffix(str.rstrip(str.rstrip(
        text, "0"), ".") if "." in text else text, ":00")


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
    '2026-09-14 12:00'
    >>> time_to_str(1789315200000)
    '2026-09-14 00:00'
    >>> time_to_str(EARLIEST_START)
    '2001-09-09 09:46:40'
    >>> time_to_str(LATEST_END)
    '2080-11-28 14:13:20'
    """
    return __trim(datetime.isoformat(datetime.fromtimestamp(check_time(
        time) / 1000, tz=__TZ).replace(tzinfo=None),
        sep=" ", timespec="milliseconds"))


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
    stamp: datetime = datetime.fromisoformat(str.strip(string))
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=__TZ)
    return check_time(round(1000 * stamp.timestamp()))


#: the maximum permitted time delta
MAX_TIME_DELTA: Final[int] = min(LATEST_END - EARLIEST_START,
                                 floor(timedelta.max.total_seconds() * 1000))


def check_timedelta(delta: int) -> int:
    """
    Check a time delta.

    :param delta: the timte delta.
    :return: the `delta`, if it is O
    :raises ValueError: for invalid time deltas

    >>> check_timedelta(0)
    0

    >>> try:
    ...     check_timedelta(-1)
    ... except ValueError as ve:
    ...     print(ve)
    delta=-1 is invalid, must be in 0..2500000000000.
    """
    return check_int_range(delta, "delta", 0, MAX_TIME_DELTA)


def timedelta_to_str(delta: int) -> str:
    """
    Convert a time delta to a string.

    :param delta: the delta
    :return: the string representation of the delta

    >>> timedelta_to_str(0)
    '0:00'

    >>> timedelta_to_str(1)
    '0:00:00.001'

    >>> timedelta_to_str(70)
    '0:00:00.07'

    >>> timedelta_to_str(71)
    '0:00:00.071'

    >>> timedelta_to_str(1000)
    '0:00:01'

    >>> timedelta_to_str(10 * 1000)
    '0:00:10'

    >>> timedelta_to_str(60 * 1000)
    '0:01'

    >>> timedelta_to_str(10 * 60 * 1000)
    '0:10'

    >>> timedelta_to_str(60 * 60 * 1000)
    '1:00'

    >>> timedelta_to_str(10 * 60 * 60 * 1000)
    '10:00'

    >>> timedelta_to_str(24 * 60 * 60 * 1000)
    '1 day'

    >>> timedelta_to_str(10 * 24 * 60 * 60 * 1000)
    '10 days'

    >>> timedelta_to_str(10 * 24 * 60 * 60 * 1000 + 1)
    '10 days, 0:00:00.001'
    """
    return str.removesuffix(__trim(str(timedelta(
        milliseconds=check_timedelta(delta)))), ", 0:00")


def str_to_timedelta(text: str) -> int:
    """
    Convert a time delta string to a time delta value.

    :param text: the string
    :return: the time delta

    >>> str_to_timedelta('0:00')
    0

    >>> str_to_timedelta('0')
    0

    >>> str_to_timedelta('0:00:00.001')
    1

    >>> str_to_timedelta('0:00:00.07')
    70

    >>> str_to_timedelta('0:00:00.071')
    71

    >>> str_to_timedelta('0:00:01')
    1000

    >>> str_to_timedelta('0:00:10')
    10000

    >>> str_to_timedelta('0:01')
    60000

    >>> str_to_timedelta('0:10')
    600000

    >>> str_to_timedelta('1:00')
    3600000

    >>> str_to_timedelta('10:00')
    36000000

    >>> str_to_timedelta('1 day')
    86400000

    >>> str_to_timedelta('10 days')
    864000000

    >>> str_to_timedelta('10 days, 0:00:00.001')
    864000001

    >>> str_to_timedelta('150:00')
    540000000

    >>> str_to_timedelta('00:150')
    9000000

    >>> str_to_timedelta('2:30:00')
    9000000
    """
    text = str.lower(str.strip(text))
    slen: Final[int] = str.__len__(text)
    i: int = str.find(text, "day")
    if i <= 0:
        i = days = 0
    else:
        days = int(text[:i])
        i += 3
        while (i < slen) and (text[i] in "days,"):
            i += 1

    h = m = s = ms = 0
    if slen > i:
        j = str.find(text, ":", i)
        if j <= i:
            h = int(text[i:])
        else:
            h = int(text[i:j])
            i = j + 1
            j = str.find(text, ":", i)
            if j <= i:
                m = int(text[i:])
            else:
                m = int(text[i:j])
                i = j + 1
                j = str.find(text, ".", i)
                if j <= i:
                    s = int(text[i:])
                else:
                    s = int(text[i:j])
                    ms = round(1_000_000 * float(text[j:]))

    return check_timedelta(round(1000 * timedelta(
        days=days, hours=h, minutes=m, seconds=s,
        microseconds=ms).total_seconds()))
