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
from typing import Callable, Final, Sequence
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


def load_day_map(is_workday: Callable[[int], bool] = range(
        6).__contains__) -> Sequence[int]:
    """
    Load the work day map, defining for each ordinal the next work day.

    :param is_workday: check if a day is a work day (monday=0)
    :return: the work day map

    >>> dm = load_day_map()
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
    2001-09-15
    2001-09-17
    2001-09-17
    2001-09-18
    2001-09-19
    2001-09-20
    2001-09-21
    2001-09-22
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
    raw: list[int] = [int(is_workday((i + 6) % 7)) for i in range(
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


def get_workday(day: int, workdays: Sequence[int]) -> int:
    """
    Get the work day from the workday map.

    :param day: the day ordinal to check
    :param workdays: the work day map, as returned by :func:`load_day_map`
    :return: the work day closest to `day`, may be `day` itself
    """
    return workdays[day - __FIRST_ORDINAL]


def __offset(stamp: datetime, days: int, seconds: int) -> int:
    """
    Create a time stamp with date offset by days and time defined by seconds.

    :param stamp: the time stamp
    :param days: the number of days to add to the date of `stamp`
    :param seconds: the number of seconds after midnight on the new day
    :return: the offset time stamp value

    >>> time_to_str(__offset(datetime(2020, 10, 5, 2, 7, 8, tzinfo=TZ),
    ...             3, 3600 * 6))
    '2020-10-08 06:00'
    """
    return round((stamp.replace(hour=0, minute=0, second=0) + timedelta(
        days=days, seconds=seconds % 86400)).timestamp())


def end_of_job(start: int, needed_time: int,
               can_wrap: bool,
               worktime: tuple[tuple[int, int], ...],
               workdays: Sequence[int]) -> int:
    """
    Get the time when a job ends.

    :param start: the time when the job begins; must be a work day
    :param needed_time: the time the job needs
    :param can_wrap: can the job wrap days (`True`) or does it need to be
        completed entirely in a workday (`False`)?
    :param worktime: the work time window tuples, multiple `(start, end)`
        tuples
    :param workdays: an internal sequence of workdays object, as obtained
        via :func:`load_day_map`
    :return: the adjusted time stamp

    >>> _wt = ((8 * 3600, 11 * 3600), (12 * 3600, 19 * 3600))
    >>> _wd = load_day_map(range(0, 6).__contains__)

    >>> time_to_str(end_of_job(str_to_time("2025-10-10 12:00"),
    ...                        3600 * 2, False, _wt, _wd))
    '2025-10-10 14:00'

    >>> time_to_str(end_of_job(str_to_time("2025-10-12 12:00"),
    ...                        3600 * 2, False, _wt, _wd))
    '2025-10-13 10:00'

    >>> time_to_str(end_of_job(str_to_time("2025-10-18 12:00"),
    ...                        3600 * 2, False, _wt, _wd))
    '2025-10-18 14:00'

    >>> time_to_str(end_of_job(str_to_time("2025-10-10 12:00"),
    ...                        3600 * 6, False, _wt, _wd))
    '2025-10-10 18:00'

    >>> time_to_str(end_of_job(str_to_time("2025-10-10 12:00"),
    ...                        3600 * 6 + 1, False, _wt, _wd))
    '2025-10-10 18:00:01'

    >>> time_to_str(end_of_job(str_to_time("2025-10-10 13:00"),
    ...                        3600 * 6 + 1, False, _wt, _wd))
    '2025-10-11 18:00:01'

    >>> time_to_str(end_of_job(str_to_time("2025-10-10 13:00"),
    ...                        3600 * 6 + 1, True, _wt, _wd))
    '2025-10-11 08:00:01'

    >>> time_to_str(end_of_job(str_to_time("2025-10-10 12:00"),
    ...                        3600 * 6, True, _wt, _wd))
    '2025-10-10 18:00'

    >>> time_to_str(end_of_job(str_to_time("2025-10-10 12:00"),
    ...                        3600 * 6 + 1, True, _wt, _wd))
    '2025-10-10 18:00:01'

    >>> time_to_str(end_of_job(str_to_time("2025-10-10 13:00"),
    ...                        3600 * 6 + 1, True, _wt, _wd))
    '2025-10-11 08:00:01'
    """
    # Get the start day and start time.
    start_stamp: datetime = __timestamp(start)
    start_day: Final[int] = start_stamp.toordinal()
    start_time: int = start_stamp.second + 60 * (
        start_stamp.minute + (60 * start_stamp.hour))

    wd_ofs: Final[int] = __FIRST_ORDINAL
    if needed_time >= max(wt_end - wt_start for wt_start, wt_end in worktime):
        # If this is the case, then we *must* wrap the work time.
        can_wrap = True

    end_day: int = workdays[start_day - wd_ofs]
    if end_day > start_day:
        start_time = 0
    end_time: int = start_time

    loop: bool = needed_time > 0
    while loop:
        for wt_start, wt_end in worktime:
            if wt_start > start_time:
                start_time = wt_start
            elif start_time > wt_end:
                continue
            if ((start_time + needed_time) > wt_end) and (not can_wrap):
                continue
            end_time = min(start_time + needed_time, wt_end)
            needed_time -= end_time - start_time
            if needed_time <= 0:
                loop = False
                break
            start_time = end_time
        if not loop:
            break
        start_time = 0
        end_day = workdays[end_day + 1 - wd_ofs]

    return __offset(start_stamp, end_day - start_day, end_time)


def next_multiple_of(now: int, multiple_in_s: int,
                     worktime: tuple[tuple[int, int], ...],
                     workdays: Sequence[int]) -> int:
    """
    Get the next time when a multiple of a certain amount of seconds elapses.

    :param now: the current time
    :param multiple_in_s: the multiple that needs to elapse
    :param worktime: the work time window tuples, multiple `(start, end)`
        tuples
    :param workdays: an internal sequence of workdays object, as obtained
        via :func:`load_day_map`
    :return: the adjusted time stamp

    >>> _wt = ((8 * 3600, 11 * 3600), (12 * 3600, 19 * 3600))
    >>> _wd = load_day_map(range(0, 6).__contains__)

    >>> time_to_str(next_multiple_of(str_to_time("2025-10-10 12:00"), 3600,
    ...             _wt, _wd))
    '2025-10-10 12:00'

    >>> time_to_str(next_multiple_of(str_to_time("2025-10-10 12:00"), 3,
    ...             _wt, _wd))
    '2025-10-10 12:00'

    >>> time_to_str(next_multiple_of(str_to_time("2025-10-10 12:00"), 7,
    ...             _wt, _wd))
    '2025-10-10 12:00:04'

    >>> time_to_str(next_multiple_of(str_to_time("2025-10-10 17:59:58"), 7,
    ...             _wt, _wd))
    '2025-10-10 17:59:59'

    >>> time_to_str(next_multiple_of(str_to_time("2025-10-10 17:59:58"), 37,
    ...             _wt, _wd))
    '2025-10-10 18:00:24'

    >>> time_to_str(next_multiple_of(str_to_time("2025-10-10 18:59:58"), 37,
    ...             _wt, _wd))
    '2025-10-11 08:00:23'
    """
    # Get the start day and start time.
    start_stamp: datetime = __timestamp(now)
    start_day: Final[int] = start_stamp.toordinal()
    wd_ofs: Final[int] = __FIRST_ORDINAL

    end_day: int = workdays[start_day - wd_ofs]
    end_time = 0 if end_day > start_day else (start_stamp.second + 60 * (
        start_stamp.minute + (60 * start_stamp.hour)))

    while True:
        for wt_start, wt_end in worktime:
            if wt_start > end_time:
                end_time = wt_start
            elif end_time > wt_end:
                continue

            d, m = divmod(end_time, multiple_in_s)
            end_time = multiple_in_s * ((d + 1) if m > 0 else d)
            if end_time < wt_end:
                return __offset(start_stamp, end_day - start_day, end_time)
        end_time = 0
        end_day = workdays[end_day - wd_ofs + 1]
