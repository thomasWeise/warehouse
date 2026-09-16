"""
The different events that may occur during a simulation.

>>> with context():
...     m1 = Material(None, "Shoe")
...     m2 = Material(1, "Hat")
...     m3 = Material(2, "Skirt")
...     m4 = Material(None, "T-Shirt")
...     b1 = Bin(None, "shelf", m1)
...     b2 = Bin(1, "cupboard")
...     b3 = Bin(None, "wardrobe", 3)
...     b4 = Bin(None, "drawer", "Skirt")
...     b5 = Bin(4, "shed", None)
...     ev0 = StartEvent(1789361500000)
...     ev1 = WarehouseIn(1789361600000, "Hat", 12)
...     ev2 = WarehouseOut(1889361600000, "Hat", 8)
...     ev3 = OverstockIn(1899361600000, "Skirt", 4)
...     ev4 = OverstockOut(1999361600000, "Skirt", 3)
...     ev5 = BinIn(2099361600000, "Hat", "cupboard")
...     ev6 = BinOut(2109361600000, "Hat", "cupboard")
...     ev7 = EndEvent(2110000000000)
...
...     text = list(Event.to_csv((ev0, ev1, ev2, ev3, ev4, ev5, ev6, ev7)))
...     for srow in text:
...         if not str.startswith(srow, '#'):
...             print(srow)
...
...     print("------")
...
...     events = list(Event.from_csv(text))
...     for event in events:
...         print(repr(event))
...
...     print("------")
...
...     text = list(Event.to_csv(events))
...     for srow in text:
...         if not str.startswith(srow, '#'):
...             print(srow)
time;type;material;amount;bin
2026-09-14T12:51:40+08:00;start
2026-09-14T12:53:20+08:00;warehouse_in;Hat;12
2029-11-14T22:40:00+08:00;warehouse_out;Hat;8
2030-03-10T16:26:40+08:00;overstock_in;Skirt;4
2033-05-11T02:13:20+08:00;overstock_out;Skirt;3
2036-07-11T12:00:00+08:00;bin_in;Hat;1;cupboard
2036-11-04T05:46:40+08:00;bin_out;Hat;1;cupboard
2036-11-11T15:06:40+08:00;end
------
StartEvent(time=1789361500000)
WarehouseIn(time=1789361600000, material=Material(key=1, name='Hat'), \
amount=12)
WarehouseOut(time=1889361600000, material=Material(key=1, name='Hat'), \
amount=8)
OverstockIn(time=1899361600000, material=Material(key=2, name='Skirt'), \
amount=4)
OverstockOut(time=1999361600000, material=Material(key=2, name='Skirt'), \
amount=3)
BinIn(time=2099361600000, material=Material(key=1, name='Hat'), where=Bin(\
key=1, name='cupboard', material=None))
BinOut(time=2109361600000, material=Material(key=1, name='Hat'), where=Bin(\
key=1, name='cupboard', material=None))
EndEvent(time=2110000000000)
------
time;type;material;amount;bin
2026-09-14T12:51:40+08:00;start
2026-09-14T12:53:20+08:00;warehouse_in;Hat;12
2029-11-14T22:40:00+08:00;warehouse_out;Hat;8
2030-03-10T16:26:40+08:00;overstock_in;Skirt;4
2033-05-11T02:13:20+08:00;overstock_out;Skirt;3
2036-07-11T12:00:00+08:00;bin_in;Hat;1;cupboard
2036-11-04T05:46:40+08:00;bin_out;Hat;1;cupboard
2036-11-11T15:06:40+08:00;end
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar, Final, Iterable, Self
from zoneinfo import ZoneInfo

from pycommons.io.csv import CsvReader as CsvReaderBase
from pycommons.io.csv import CsvWriter as CsvWriterBase
from pycommons.io.csv import (
    csv_column,
    csv_column_or_none,
    csv_scope,
)
from pycommons.types import check_int_range, type_error

from warehouse.instance.bin import COLUMN_MATERIAL, Bin
from warehouse.instance.element import context
from warehouse.instance.material import Material

#: the event time column
COLUMN_TIME: Final[str] = "time"
#: the event type column
COLUMN_TYPE: Final[str] = "type"
#: the bin column
COLUMN_BIN: Final[str] = "bin"
#: the amount column
COLUMN_AMOUNT: Final[str] = "amount"

#: the standard time zone to use to write dates and times
TIME_ZONE: Final[ZoneInfo] = ZoneInfo("Asia/Shanghai")


#: the earliest start time for an event
EARLIEST_START: Final[int] = 1000000000000
#: the latest end time for an event
LATEST_END: Final[int] = 3500000000000


def time_to_str(time: int) -> str:
    """
    Convert an event time to a string.

    :param time: the event time
    :return: the string

    >>> time_to_str(1789361695615)
    '2026-09-14T12:54:55.615+08:00'
    >>> time_to_str(1789361695616)
    '2026-09-14T12:54:55.616+08:00'
    >>> time_to_str(1789361695614)
    '2026-09-14T12:54:55.614+08:00'
    >>> time_to_str(EARLIEST_START)
    '2001-09-09T09:46:40+08:00'
    >>> time_to_str(LATEST_END)
    '2080-11-28T14:13:20+08:00'
    """
    return str.replace(datetime.fromtimestamp(
        time / 1000, tz=TIME_ZONE).isoformat(), "000+", "+")


def str_to_time(string: str) -> int:
    """
    Convert a time string to an event time value.

    :param string: the time string
    :return: the event time value.

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
    return round(
        1000 * datetime.fromisoformat(str.strip(string)).timestamp())


@dataclass(frozen=True, init=False, order=False, eq=False)
class Event:
    """The base class for events."""

    #: all subclasses
    _subclasses: ClassVar[dict[str, type["Event"]]] = {}

    #: the time associated with the event
    time: int = field(init=False, repr=True, hash=False, compare=False)

    def __init_subclass__(cls, **kwargs) -> None:
        """
        Initialize a new subclass of :class:`Event`.

        :param kwargs: some arguments
        """
        super().__init_subclass__(**kwargs)
        if cls.__name__ in {"BinEvent", "StorageEvent"}:
            return
        Event._subclasses[str.lower(cls._get_csv_type())] = cls

    @classmethod
    def _get_csv_columns(cls) -> tuple[str, ...]:
        """
        Get the CSV columns used by this event class.

        :return: the CSV columns used by this event class
        """
        return ()

    @classmethod
    def _get_csv_type(cls) -> str:
        """
        Get the CSV type of this class.

        :return: the csv type
        """
        return str.lower(cls.__name__)

    @classmethod
    def _get_event_desc(cls) -> str | None:
        """
        Get the event description.

        :return: the event description, if any
        """
        return None

    @classmethod
    def _get_col_desc(
            cls, col: str) -> str | None:  # noqa  # pylint: disable=W0613
        """
        Get the column description.

        :param col: the column
        :return: the event description, if any
        """
        return None

    @classmethod
    def _create(
            cls, time: int, cols: dict[  # noqa  # pylint: disable=W0613
                str, int | None],
            data: list[str]) -> "Event":  # noqa  # pylint: disable=W0613
        """
        Create the event from the columns.

        :param time: the event time
        :param cols: the columns
        :param data: the data
        :return: the event
        """
        return cls(time)

    def __init__(self, time: int) -> None:
        """
        Create an event object.

        :param time: the event time
        """
        object.__setattr__(self, "time", check_int_range(
            time, "time", EARLIEST_START, LATEST_END))

    def copy(self) -> Self:
        """
        Create a copy of this event.

        :return: an independent copy of this event
        """
        return self.__class__(self.time)

    def __hash__(self) -> int:
        """
        Get the hash code of this event.

        :return: the hash code.
        """
        return hash((self.time, self.__class__))

    def _get_csv_value(
            self, column: str) -> str:  # noqa  # pylint: disable=W0613
        """
        Get a specific csv value.

        :param column: the csv column
        :return: the value
        """
        return ""

    def __lt__(self, other) -> bool:
        """
        Compare this event with another event object for "less".

        :param other: the other event
        :return: `True` if this event is less than the other event,
            `False` otherwise

        >>> Event(10 ** 12) < Event(2 * (10 ** 12))
        True
        >>> Event(2 * (10 ** 12)) < Event(2 * (10 ** 12))
        False
        >>> Event(2 * (10 ** 12)) < Event(10 ** 12)
        False
        """
        return self.time < other.time

    def __le__(self, other) -> bool:
        """
        Compare this event with another event object for "less or equal".

        :param other: the other event
        :return: `True` if this event is less or equal than the other event,
            `False` otherwise

        >>> Event(10 ** 12) <= Event(2 * (10 ** 12))
        True
        >>> Event(2 * (10 ** 12)) <= Event(2 * (10 ** 12))
        True
        >>> Event(2 * (10 ** 12)) <= Event(10 ** 12)
        False
        """
        return self.time <= other.time

    def __eq__(self, other) -> bool:
        """
        Compare this event with another event object for "equality".

        :param other: the other event
        :return: `True` if this event is equal to the other event,
            `False` otherwise

        >>> Event(10 ** 12) == Event(2 * (10 ** 12))
        False
        >>> Event(2 * (10 ** 12)) == Event(2 * (10 ** 12))
        True
        >>> Event(2 * (10 ** 12)) == Event(10 ** 12)
        False
        """
        return self.time == other.time

    def __ge__(self, other) -> bool:
        """
        Compare this event with another event object for "greater or equal".

        :param other: the other event
        :return: `True` if this event is greater or equal than the other
            event, `False` otherwise

        >>> Event(10 ** 12) >= Event(2 * (10 ** 12))
        False
        >>> Event(2 * (10 ** 12)) >= Event(2 * (10 ** 12))
        True
        >>> Event(2 * (10 ** 12)) >= Event(10 ** 12)
        True
        """
        return self.time >= other.time

    def __gt__(self, other) -> bool:
        """
        Compare this event with another event object for "greater".

        :param other: the other event
        :return: `True` if this event is greater than the other event,
            `False` otherwise

        >>> Event(10 ** 12) > Event(2 * (10 ** 12))
        False
        >>> Event(2 * (10 ** 12)) > Event(2 * (10 ** 12))
        False
        >>> Event(2 * (10 ** 12)) > Event(10 ** 12)
        True
        """
        return self.time > other.time

    def __ne__(self, other) -> bool:
        """
        Compare this event with another event object for "inequality".

        :param other: the other event
        :return: `True` if this event is not equal than the other event,
            `False` otherwise

        >>> Event(10 ** 12) != Event(2 * (10 ** 12))
        True
        >>> Event(2 * (10 ** 12)) != Event(2 * (10 ** 12))
        False
        >>> Event(2 * (10 ** 12)) != Event(10 ** 12)
        True
        """
        return self.time != other.time

    @classmethod
    def to_csv(cls, data: Iterable["Event"]) -> Iterable[str]:
        """
        Convert an iterable of the object to a CSV stream.

        :param data: the data
        :return: the stream
        """
        return CsvWriter.write(data)

    @classmethod
    def from_csv(cls, rows: Iterable[str]) -> Iterable["Event"]:
        """
        Get the data from CSV.

        :param rows: the rows
        :return: the sequence of objects
        """
        with context():
            yield from CsvReader.read(rows=rows)   # type: ignore


class CsvReader(CsvReaderBase[Event]):
    """A CsvReader that reads named objects from a CSV file."""

    def __init__(self, columns: dict[str, int]):
        """
        Initialize.

        :param columns: the named object columns
        """
        super().__init__(columns)

        cols: Final[dict[str, int | None]] = {}
        cols[COLUMN_TIME] = csv_column(columns, COLUMN_TIME, True)
        cols[COLUMN_TYPE] = csv_column(columns, COLUMN_TYPE, True)
        for cls in Event._subclasses.values():
            cls_cols = cls._get_csv_columns()
            for col in cls_cols:
                if col in cols:
                    continue
                cols[col] = csv_column_or_none(columns, col, True)

        #: the internal column list
        self.__cols: Final[dict[str, int | None]] = cols

    def parse_row(self, data: list[str]) -> Event:
        """
        Parse a data row.

        :param data: the data row
        :return: the instance
        """
        cols: Final[dict[str, int | None]] = self.__cols
        cls: Final[type[Event]] = Event._subclasses[
            str.lower(data[cols[COLUMN_TYPE]])]
        ret = cls._create(str_to_time(data[cols[
            COLUMN_TIME]]), cols, data)
        if not isinstance(ret, Event):
            raise type_error(ret, "parse_row result", Event)
        return ret


class CsvWriter(CsvWriterBase[Event]):
    """Write the event data to a csv file."""

    def __init__(self, data: Iterable[Event],
                 scope: str | None = None) -> None:
        """
        Initialize the CSV writer.

        :param data: the data
        :param scope: the scope
        """
        super().__init__(data, scope)

        #: the time column
        self.__col_time: Final[str] = csv_scope(scope, COLUMN_TIME)
        #: the type column
        self.__col_type: Final[str] = csv_scope(scope, COLUMN_TYPE)

        cols: Final[dict[str, str]] = {}
        for cls in Event._subclasses.values():
            for col in cls._get_csv_columns():
                if col not in cols:
                    cols[col] = csv_scope(scope, col)
        #: the columns
        self.__cols: Final[dict[str, str]] = cols

    def get_column_titles(self) -> Iterable[str]:
        """
        Get the column titles.

        :returns: the column titles
        """
        yield self.__col_time
        yield self.__col_type
        yield from self.__cols.values()

    def get_row(self, data: Event) -> Iterable[str]:
        """
        Render a single element  CSV row.

        :param data: the element
        :returns: the row iterator
        """
        yield time_to_str(data.time)
        yield data.__class__._get_csv_type()
        for col in self.__cols:
            yield data._get_csv_value(col)

    def get_footer_comments(self) -> Iterable[str]:
        """
        Get the footer comments.

        :return: the footer comments
        """
        yield "The following columns exist in this file:"
        yield (f"{self.__col_time}: The time at which the event takes place, "
               "as an ISO timestamp with millisecond precision")
        yield (f"{self.__col_type}: The type of the event. Each event type "
               "has a specific meaning. See below for a list of event types.")
        cols: Final[dict[str, str]] = dict(self.__cols)
        for cls in Event._subclasses.values():
            for col in cls._get_csv_columns():
                if col in cols:
                    desc = cls._get_col_desc(col)
                    if desc:
                        yield f"{cols[col]}: {desc}"
                        del cols[col]
        yield ""
        yield f"Event types (column {self.__col_type}):"
        for name, cls in Event._subclasses.items():
            desc = cls._get_event_desc()
            if desc:
                yield f"  - {name}: {desc}"


class StartEvent(Event):
    """The simulation begins."""

    @classmethod
    def _get_csv_type(cls) -> str:
        """
        Get the csv type of the event.

        :return: the csv type
        """
        return "start"

    @classmethod
    def _get_event_desc(cls) -> str | None:
        """
        Get the event description.

        :return: the event description, if any
        """
        return "the time when the simulation begins"


class EndEvent(Event):
    """The simulation ends."""

    @classmethod
    def _get_csv_type(cls) -> str:
        """
        Get the csv type of the event.

        :return: the csv type
        """
        return "end"

    @classmethod
    def _get_event_desc(cls) -> str | None:
        """
        Get the event description.

        :return: the event description, if any
        """
        return "the time when the simulation ends"


@dataclass(frozen=True, init=False, order=False, eq=False)
class StorageEvent(Event):
    """Store or retrieve an amount of a given material in the warehouse."""

    #: the material to be stored in or retrieved from the warehouse
    material: Material = field(init=False, repr=True, hash=False,
                               compare=False)

    #: the amount of the material to be stored in or retrieved from the
    #: warehouse
    amount: int = field(init=False, repr=True, hash=False, compare=False)

    def __init__(self, time: int, material: Material | int | str,
                 amount: int) -> None:
        """
        Create the storage event.

        :param time: the time when we want to store material in the warehouse
        :param material: the material that we want to store/retrieve
        :param amount: the amount of material to store/retrieve
        """
        super().__init__(time)
        if isinstance(material, int | str):
            with context() as ctx:
                material = ctx.resolve(Material, material)
        if not isinstance(material, Material):
            raise type_error(material, "material", (Material, int, str))
        object.__setattr__(self, "material", material)
        object.__setattr__(self, "amount", check_int_range(
            amount, "amount", 1, 1_000_000))

    def copy(self) -> Self:
        """
        Create a copy of this event.

        :return: an independent copy of this event
        """
        return self.__class__(self.time, self.material, self.amount)

    @classmethod
    def _get_col_desc(cls, col: str) -> str | None:
        """
        Get the column description.

        :param col: the column
        :return: the event description, if any
        """
        if col == COLUMN_MATERIAL:
            return "the type of material associated with the event"
        if col == COLUMN_AMOUNT:
            return "the amount of material stored or retrieved"
        return None

    def _get_csv_value(self, column: str) -> str:
        """
        Get a specific csv value.

        :param column: the csv column
        :return: the value
        """
        if column == COLUMN_MATERIAL:
            return self.material.name
        if column == COLUMN_AMOUNT:
            return str(self.amount)
        return ""

    @classmethod
    def _get_csv_columns(cls) -> tuple[str, ...]:
        """
        Get the CSV columns of the event.

        :return: the csv columns
        """
        return COLUMN_MATERIAL, COLUMN_AMOUNT

    @classmethod
    def _create(cls, time: int, cols: dict[
            str, int | None], data: list[str]) -> Event:
        """
        Create the storage event.

        :param time: the time
        :param cols: the csv columns
        :param data: the csv data
        :return: the event
        """
        return cls(time, data[cols[COLUMN_MATERIAL]], int(
            data[cols[COLUMN_AMOUNT]]))


class WarehouseIn(StorageEvent):
    """Store material in the warehouse."""

    @classmethod
    def _get_csv_type(cls) -> str:
        """
        Get the csv type of the event.

        :return: the csv type
        """
        return "warehouse_in"

    @classmethod
    def _get_event_desc(cls) -> str | None:
        """
        Get the event description.

        :return: the event description, if any
        """
        return ("a certain amount of a material has arrived at the warehouse "
                "and needs to be stored; it then needs to be decided where to"
                " put it.")


class WarehouseOut(StorageEvent):
    """Retrieve material from the warehouse."""

    @classmethod
    def _get_csv_type(cls) -> str:
        """
        Get the csv type of the event.

        :return: the csv type
        """
        return "warehouse_out"

    @classmethod
    def _get_event_desc(cls) -> str | None:
        """
        Get the event description.

        :return: the event description, if any
        """
        return ("a certain amount of a material is requested from the "
                "warehouse and needs to be taken out of the stored amount of "
                "this material; it then needs to be decided from which bin to"
                " take it or, if there is overstock, maybe it can be taken "
                "from there.")


class OverstockIn(StorageEvent):
    """Store material in the overstock."""

    @classmethod
    def _get_csv_type(cls) -> str:
        """
        Get the csv type of the event.

        :return: the csv type
        """
        return "overstock_in"

    @classmethod
    def _get_event_desc(cls) -> str | None:
        """
        Get the event description.

        :return: the event description, if any
        """
        return ("a certain amount of a material has arrived in the warehouse,"
                " but it could not be put into any bin, because all bins are "
                "full; the material was placed into the 'overstock', meaning "
                "that it is just laying around somewhere.")


class OverstockOut(StorageEvent):
    """Retrieve material from the overstock."""

    @classmethod
    def _get_csv_type(cls) -> str:
        """
        Get the csv type of the event.

        :return: the csv type
        """
        return "overstock_out"

    @classmethod
    def _get_event_desc(cls) -> str | None:
        """
        Get the event description.

        :return: the event description, if any
        """
        return ("a certain amount of a material was taken from the overstock:"
                " this material was not in any bin, because all bins were "
                "occupied; so it was just laying around.")


@dataclass(frozen=True, init=False, order=False, eq=False)
class BinEvent(Event):
    """Store or retrieve material in/from a bin."""

    #: the material to be stored in or retrieved from the bin
    material: Material = field(init=False, repr=True, hash=False,
                               compare=False)

    #: the bin
    where: Bin = field(init=False, repr=True, hash=False, compare=False)

    def __init__(self, time: int, material: Material | int | str,
                 where: Bin | int | str) -> None:
        """
        Create the storage event.

        :param time: the time when we want to store material in the warehouse
        :param material: the material that we want to store/retrieve
        :param where: the bin to use
        """
        super().__init__(time)
        needs_mat = isinstance(material, int | str)
        needs_bin = isinstance(where, int | str)
        if needs_mat | needs_bin:
            with context() as ctx:
                if needs_mat:
                    material = ctx.resolve(Material, material)  # type: ignore
                if needs_bin:
                    where = ctx.resolve(Bin, where)  # type: ignore
        if not isinstance(material, Material):
            raise type_error(material, "material", (Material, int, str))
        if not isinstance(where, Bin):
            raise type_error(where, "where", (Bin, int, str))
        object.__setattr__(self, "material", material)
        object.__setattr__(self, "where", where)

    def copy(self) -> Self:
        """
        Create a copy of this event.

        :return: an independent copy of this event
        """
        return self.__class__(self.time, self.material, self.where)

    def _get_csv_value(self, column: str) -> str:
        """
        Get a specific csv value.

        :param column: the csv column
        :return: the value
        """
        if column == COLUMN_MATERIAL:
            return self.material.name
        if column == COLUMN_BIN:
            return str(self.where.name)
        if column == COLUMN_AMOUNT:
            return "1"
        return ""

    @classmethod
    def _get_csv_columns(cls) -> tuple[str, ...]:
        """
        Get the CSV columns of the event.

        :return: the csv columns
        """
        return COLUMN_MATERIAL, COLUMN_BIN

    @classmethod
    def _create(cls, time: int, cols: dict[
            str, int | None], data: list[str]) -> Event:
        """
        Create the storage event.

        :param time: the time
        :param cols: the csv columns
        :param data: the csv data
        :return: the event
        """
        return cls(time, data[cols[COLUMN_MATERIAL]], data[cols[COLUMN_BIN]])

    @classmethod
    def _get_col_desc(cls, col: str) -> str | None:
        """
        Get the column description.

        :param col: the column
        :return: the event description, if any
        """
        if col == COLUMN_MATERIAL:
            return "the type of material associated with the event"
        if col == COLUMN_BIN:
            return "the bin into which material was stored or taken out of"
        return None


class BinIn(BinEvent):
    """Put some material in a bin."""

    @classmethod
    def _get_csv_type(cls) -> str:
        """
        Get the csv type of the event.

        :return: the csv type
        """
        return "bin_in"

    @classmethod
    def _get_event_desc(cls) -> str | None:
        """
        Get the event description.

        :return: the event description, if any
        """
        return ("one unit of a material was stored into one bin, thus "
                "fully occupying this bin.")


class BinOut(BinEvent):
    """Take some material from a bin."""

    @classmethod
    def _get_csv_type(cls) -> str:
        """
        Get the csv type of the event.

        :return: the csv type
        """
        return "bin_out"

    @classmethod
    def _get_event_desc(cls) -> str | None:
        """
        Get the event description.

        :return: the event description, if any
        """
        return ("one unit of a material was taken out of one bin, making "
                "the bin empty.")
