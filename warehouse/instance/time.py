"""
Time utilities.

In our simulation, the time is represented as integer values `int`
representing dates and times in second resolution, i.e., a time unit of `1`
corresponds to one second.
However, we store and retrieve times as ISO timestamps, where we clamp
off zero components that are not used.
Furthermore, as time zone, we by default use `Asia/Shanghai` time.
This means that a date/time without UTC offset, i.e., without something
like `"+08:00"` or `"-10:00"`, is treated as Shanghai time.
Of course, you still provide time stamps in UTC time by using suffix
`"+00:00"`.
"""

from datetime import date, datetime, timedelta
from importlib.resources import open_text
from math import floor
from typing import Callable, Final
from zoneinfo import ZoneInfo

from pycommons.io.path import UTF8
from pycommons.types import check_int_range

#: the earliest start time for an event
EARLIEST_START: Final[int] = 1000000000
#: the latest end time for an event
LATEST_END: Final[int] = 3500000000


#: the CSV column for delays
COLUMN_DELAY: Final[str] = "delay"

#: the CSV column for delays of the effect of rules.
COLUMN_EFFECT_DELAY: Final[str] = f"effect_{COLUMN_DELAY}"

#: the internal time zone information record
TZ: Final[ZoneInfo] = ZoneInfo("Asia/Shanghai")


def check_time(time: int) -> int:
    """
    Check a given time stamp.

    :param time: the time stamp
    :return: the time stamp

    >>> check_time(EARLIEST_START)
    1000000000

    >>> check_time(LATEST_END)
    3500000000

    >>> check_time(str_to_time('2026-09-14t12:54:55.616+00:00'))
    1789390496

    >>> check_time(1789361695)
    1789361695

    >>> try:
    ...     check_time("x")
    ... except TypeError as err:
    ...     print(err)
    time should be an instance of int but is str, namely 'x'.

    >>> try:
    ...     check_time(12)
    ... except ValueError as err:
    ...     print(err)
    time=12 is invalid, must be in 1000000000..3500000000.

    >>> try:
    ...     check_time(EARLIEST_START - 1)
    ... except ValueError as err:
    ...     print(err)
    time=999999999 is invalid, must be in 1000000000..3500000000.

    >>> try:
    ...     check_time(999_999_999_999_999_999_999)
    ... except ValueError as err:
    ...     print(err)
    time=999999999999999999999 is invalid, must be in 1000000000\
..3500000000.

    >>> try:
    ...     check_time(LATEST_END + 1)
    ... except ValueError as err:
    ...     print(err)
    time=3500000001 is invalid, must be in 1000000000..3500000000.
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


def __timestamp(time: int) -> datetime:
    """
    Create a timestamp.

    :param time: the time
    :return: the timestamp

    >>> __timestamp(EARLIEST_START)
    datetime.datetime(2001, 9, 9, 9, 46, 40, tzinfo=zoneinfo.ZoneInfo(\
key='Asia/Shanghai'))

    >>> __timestamp(LATEST_END)
    datetime.datetime(2080, 11, 28, 14, 13, 20, tzinfo=zoneinfo.ZoneInfo(\
key='Asia/Shanghai'))
    """
    return datetime.fromtimestamp(time, tz=TZ)


def time_to_str(time: int) -> str:
    """
    Convert an event time to a string.

    :param time: the event time
    :return: the string

    >>> time_to_str(1789361695)
    '2026-09-14 12:54:55'
    >>> time_to_str(1789361640)
    '2026-09-14 12:54'
    >>> time_to_str(1789358400)
    '2026-09-14 12:00'
    >>> time_to_str(1789315200)
    '2026-09-14 00:00'
    >>> time_to_str(EARLIEST_START)
    '2001-09-09 09:46:40'
    >>> time_to_str(LATEST_END)
    '2080-11-28 14:13:20'
    """
    return __trim(datetime.isoformat(__timestamp(check_time(
        time)).replace(tzinfo=None), sep=" ", timespec="seconds"))


def str_to_time(string: str) -> int:
    """
    Convert a time string to an event time value.

    :param string: the time string
    :return: the event time value.

    >>> str_to_time('2026-09-14T12:54:55')
    1789361695
    >>> str_to_time('2026-09-14T12:54:55+08')
    1789361695
    >>> str_to_time('2026-09-14T12:54+08')
    1789361640
    >>> str_to_time('2026-09-14T12+08')
    1789358400
    >>> str_to_time('2026-09-14T00+08')
    1789315200
    >>> str_to_time('2026-09-14 00+08')
    1789315200
    >>> str_to_time('2026-09-14 00')
    1789315200

    >>> str_to_time('2026-09-14T12:54:55+08:00')
    1789361695
    >>> str_to_time(time_to_str(EARLIEST_START)) == EARLIEST_START
    True
    >>> str_to_time(time_to_str(LATEST_END)) == LATEST_END
    True
    """
    stamp: datetime = datetime.fromisoformat(str.strip(string))
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=TZ)
    return check_time(round(stamp.timestamp()))


#: the maximum permitted time delta
MAX_TIME_DELTA: Final[int] = min(LATEST_END - EARLIEST_START, floor(
    timedelta.max.total_seconds()))


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
    delta=-1 is invalid, must be in 0..2500000000.
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
    '0:00:01'

    >>> timedelta_to_str(10)
    '0:00:10'

    >>> timedelta_to_str(60)
    '0:01'

    >>> timedelta_to_str(10 * 60)
    '0:10'

    >>> timedelta_to_str(60 * 60)
    '1:00'

    >>> timedelta_to_str(10 * 60 * 60)
    '10:00'

    >>> timedelta_to_str(24 * 60 * 60)
    '1 day'

    >>> timedelta_to_str(10 * 24 * 60 * 60)
    '10 days'

    >>> timedelta_to_str(10 * 24 * 60 * 60 + 1)
    '10 days, 0:00:01'
    """
    return str.removesuffix(__trim(str(timedelta(
        seconds=check_timedelta(delta)))), ", 0:00")


def str_to_timedelta(text: str) -> int:
    """
    Convert a time delta string to a time delta value.

    :param text: the string
    :return: the time delta

    >>> str_to_timedelta('0:00')
    0

    >>> str_to_timedelta('0')
    0

    >>> str_to_timedelta('0:00:01')
    1

    >>> str_to_timedelta('0:00:10')
    10

    >>> str_to_timedelta('0:01')
    60

    >>> str_to_timedelta('0:10')
    600

    >>> str_to_timedelta('0:10:00.1')
    600

    >>> str_to_timedelta('1:00')
    3600

    >>> str_to_timedelta('10:00')
    36000

    >>> str_to_timedelta('1 day')
    86400

    >>> str_to_timedelta('10 days')
    864000

    >>> str_to_timedelta('10 days, 0:00:01')
    864001

    >>> str_to_timedelta('150:00')
    540000

    >>> str_to_timedelta('00:150')
    9000

    >>> str_to_timedelta('2:30:00')
    9000
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

    return check_timedelta(round(timedelta(
        days=days, hours=h, minutes=m, seconds=s,
        microseconds=ms).total_seconds()))


#: a time delta of a single day
__DD: Final[timedelta] = timedelta(days=1)

#: the ordinal of the first supported day
__FIRST_ORDINAL: Final[int] = __timestamp(EARLIEST_START).toordinal()


def __is_monday_to_friday(ordinal: int) -> bool:
    """
    Check if a date ordinal is a work day, i.e., Monday...Friday.

    :param ordinal: the date ordinal
    :return: if it is a work day
    """
    return ((ordinal + 6) % 7) < 5


def __load_day_map() -> tuple[int, ...]:
    """
    Load the work day map, defining for each ordinal the next work day.

    :return: the work day map

    >>> dm = __load_day_map()
    >>> __timestamp(LATEST_END)
    datetime.datetime(2080, 11, 28, 14, 13, 20, \
tzinfo=zoneinfo.ZoneInfo(key='Asia/Shanghai'))

    >>> date.fromordinal(dm[-1])
    datetime.date(2080, 11, 29)

    >>> __timestamp(EARLIEST_START)
    datetime.datetime(2001, 9, 9, 9, 46, 40, \
tzinfo=zoneinfo.ZoneInfo(key='Asia/Shanghai'))

    >>> for i in range(20):
    ...     print(date.fromordinal(dm[i]))
    2001-09-10
    2001-09-10
    2001-09-11
    2001-09-12
    2001-09-13
    2001-09-14
    2001-09-17
    2001-09-17
    2001-09-17
    2001-09-18
    2001-09-19
    2001-09-20
    2001-09-21
    2001-09-24
    2001-09-24
    2001-09-24
    2001-09-25
    2001-09-26
    2001-09-27
    2001-09-28

    >>> date.fromordinal(dm[date(2016, 1, 1).toordinal() - __FIRST_ORDINAL])
    datetime.date(2016, 1, 4)

    >>> date.fromordinal(dm[date(2016, 2, 5).toordinal() - __FIRST_ORDINAL])
    datetime.date(2016, 2, 5)

    >>> date.fromordinal(dm[date(2016, 2, 6).toordinal() - __FIRST_ORDINAL])
    datetime.date(2016, 2, 6)

    >>> date.fromordinal(dm[date(2016, 2, 7).toordinal() - __FIRST_ORDINAL])
    datetime.date(2016, 2, 14)
    """
    first: Final[int] = __FIRST_ORDINAL
    last: int = __timestamp(LATEST_END).toordinal()
    raw: list[int] = [__is_monday_to_friday(i) for i in range(
        first, last + 1)]

    with open_text(str(__package__), "special_days.txt", encoding=UTF8) as sc:
        for oline in sc:
            line = str.strip(oline)
            idx: int = str.find(line, "#")
            if idx >= 0:
                line = str.strip(line[:idx])
            if str.__len__(line) <= 0:
                continue
            dte, tp = str.split(line, ";")
            raw[date(*map(int, str.split(dte, "-"))).toordinal() - first] = (
                str.upper(tp) == "T")

    raw[-1] = True  # Force that last day in our supported range is a workday
    raw.append(True)
    for i in range(list.__len__(raw) - 1, -1, -1):
        if raw[i]:
            last = i + first
        raw[i] = last

    return tuple(raw)


def get_workday(day: int, dm=__load_day_map().__getitem__) -> int:
    """
    Get the next work day for the given day.

    :param day: the day
    :param dm: the next work day
    :return: the next work day
    """
    return dm(day - __FIRST_ORDINAL)


def end_of_job(start: int, worktime: int,
               can_wrap: bool = False,
               work_start_in_s: int = 7 * 3600,
               work_end_in_s: int = 18 * 3600,
               workday: Callable[[int], int] = get_workday) -> int:
    """
    Get the time when a job ends.

    :param start: the time when the job begins; must be a work day
    :param worktime: the time the job needs
    :param can_wrap: can the job wrap days (`True`) or does it need to be
        completed entirely in a workday (`False`)?
    :param work_start_in_s: the start time of the work, in seconds from
        midnight
    :param work_end_in_s: the end time of the work, in seconds from midnight
    :param workday: a callable that receives a date ordinal and that returns
        the earliest work day with an ordinal >= workday.
    :return: the adjusted time stamp

    >>> time_to_str(end_of_job(str_to_time("2025-10-10 12:00"), 3600 * 2))
    '2025-10-10 14:00'

    >>> time_to_str(end_of_job(str_to_time("2025-10-12 12:00"), 3600 * 2))
    '2025-10-13 09:00'

    >>> time_to_str(end_of_job(str_to_time("2025-10-18 12:00"), 3600 * 2))
    '2025-10-20 09:00'

    >>> time_to_str(end_of_job(str_to_time("2025-10-10 12:00"), 3600 * 6))
    '2025-10-10 18:00'

    >>> time_to_str(end_of_job(str_to_time("2025-10-10 12:00"), 3600 * 6 + 1))
    '2025-10-11 13:00:01'

    >>> time_to_str(end_of_job(str_to_time("2025-10-10 12:00"), 3600 * 6,
    ...                        can_wrap=True))
    '2025-10-10 18:00'

    >>> time_to_str(end_of_job(str_to_time("2025-10-10 12:00"), 3600 * 6 + 1,
    ...                        can_wrap=True))
    '2025-10-11 07:00:01'
    """
    if worktime >= (work_end_in_s - work_start_in_s):
        # If this is the case, then we *must* wrap the work time.
        can_wrap = True

    # Get the start day and start time.
    start_stamp: datetime = __timestamp(start)
    start_day: Final[int] = start_stamp.toordinal()
    start_time: int = start_stamp.second + 60 * (
        start_stamp.minute + (60 * start_stamp.hour))

    if start_time > work_end_in_s:
        # Start time is outside working hours.
        # So we start on the next day.
        start_time = work_start_in_s
        end_day = workday(start_day + 1)
    else:  # Start time is within working hours.
        end_day = workday(start_day)

    # If everything goes well, this is the end time.
    end_time: int = max(work_start_in_s, start_time) + worktime

    if can_wrap:
        # The work can be done partially on different days.
        # So we step-by-step gobble it up until it is done.
        while end_time > work_end_in_s:
            end_time = (end_time - work_end_in_s) + work_start_in_s
            end_day = workday(end_day + 1)
    elif end_day > start_day:
        # If we *cannot* wrap and we start on next day, then we can
        # begin at the work start time and finish the work.
        end_time = work_start_in_s + worktime
    elif end_time > work_end_in_s:
        # I we *cannot* wrap and the work extends into the next day,
        # we simply start at the next morning.
        end_time = work_start_in_s + worktime
        end_day = workday(end_day + 1)

    end_time %= 86400
    hours, end_time = divmod(end_time, 3600)
    minutes, seconds = divmod(end_time, 60)
    return round((start_stamp.replace(hour=0, minute=0, second=0) + timedelta(
        days=end_day - start_day, hours=hours, minutes=minutes,
        seconds=seconds)).timestamp())
