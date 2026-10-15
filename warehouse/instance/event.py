"""
Events provide information about things that happen in a simulation.

They both drive the simulation *and* are its output.
They are a part of a simulation scenario
(:mod:`~warehouse.instance.instance`).
In this function, they tell the simulation what outside events happen, e.g.,
that some parts have arrived and should be stored in the warehouse.
As the output of the :meth:`~warehouse.simulation.simulation.Simulation.run`
method, they tell us what happened and when it happened.
The concrete event classes are implemented in package :mod:`~warehouse.event`.

**Note** regarding the comparison functions: `<`, `<=`, `>`, and `>=` *only*
use the :attr:`~Event.time` attribute.
This if for performance *and* consistency reasons.
Inside the simulation, events enter a priority queue.
There, only the original sequence of events as well as their time stamps
should matter.
Sorting and priority-queueing usually only use `<` comparisons and each
element with a different key must also have a different name anyway.

However, `==` and `!=` may *also* use other attributes.
This may be useful for comparing data across instances.
"""

from dataclasses import dataclass, field
from operator import itemgetter
from typing import ClassVar, Final, Iterable

from pycommons.io.csv import CsvReader as CsvReaderBase
from pycommons.io.csv import CsvWriter as CsvWriterBase
from pycommons.io.csv import (
    csv_column,
    csv_column_or_none,
    csv_scope,
    csv_str_or_none,
)
from pycommons.types import type_error

from warehouse.instance.element import context
from warehouse.instance.time import check_time, str_to_time, time_to_str

#: the event time column
COLUMN_TIME: Final[str] = "time"
#: the event type column
COLUMN_TYPE: Final[str] = "type"


@dataclass(frozen=True, init=True, order=False, eq=False, unsafe_hash=True)
class Event:  # noqa: PLW1641
    """The base class for events."""

    #: the internal subclasses
    __subclasses: ClassVar[dict[str, type["Event"]]] = {}

    #: the subclass items
    __subclasses_items: ClassVar[tuple[tuple[
        str, type["Event"]], ...] | None] = None

    #: the subclasses
    __subclasses_classes: ClassVar[tuple[type["Event"], ...] | None] = None

    #: the time when the event takes place
    time: int = field(hash=True)

    def __init_subclass__(cls, **kwargs) -> None:
        """
        Initialize a new subclass of :class:`Event`.

        :param kwargs: some arguments
        """
        if not issubclass(cls, Event):
            raise type_error(cls, "cls", Event.__class__)
        super().__init_subclass__(**kwargs)
        if cls.eventclass_needs_register():
            key: Final[str] = cls.eventclass_get_csv_type()
            sc: Final[dict[str, type[Event]]] = Event.__subclasses
            if key in sc:
                raise ValueError(f"Event type {key!r} is already registered.")
            sc[key] = cls
            Event.__subclasses_items = None
            Event.__subclasses_classes = None

    @classmethod
    def eventclass_from_name(cls, name: str) -> type["Event"]:
        """
        Get an event class of the given name.

        :param name: the name
        :return: the class
        """
        return Event.__subclasses[name]

    @classmethod
    def eventclass_classes(cls) -> tuple[type["Event"], ...]:
        """
        Get an iterable of the event classes.

        :return: the event classes
        """
        res = Event.__subclasses_classes
        if res is None:
            Event.__subclasses_classes = res = tuple(map(
                itemgetter(1), Event.eventclass_types()))
        return res

    @classmethod
    def eventclass_types(cls) -> Iterable[tuple[str, type["Event"]]]:
        """
        Get an iterable of the event types and corresponding classes.

        :return: the event types and classes
        """
        res = Event.__subclasses_items
        if res is None:
            Event.__subclasses_items = res = tuple(sorted(
                Event.__subclasses.items()))
        return res

    @classmethod
    def eventclass_needs_register(cls) -> bool:
        """
        Check whether the class should be registered.

        :returns: `True` if it should be registered as a possible event type,
            `False` otherwise; in this case: `True` if class is not `Event`.
        """
        return cls is not Event

    @classmethod
    def eventclass_get_csv_columns(cls) -> tuple[str, ...]:
        """
        Get the CSV columns used by this event class.

        :return: the CSV columns used by this event class, except for event
            time and event type
        """
        return ()

    @classmethod
    def eventclass_get_csv_type(cls) -> str:
        """
        Get the CSV type of this class.

        :return: the csv type
        """
        return str.lower(cls.__name__)

    @classmethod
    def eventclass_get_event_desc(cls) -> str | None:
        """
        Get the event description.

        :return: the event description, if any
        """
        return None

    @classmethod
    def eventclass_get_col_desc(
            cls, col: str) -> str | None:  # noqa  # pylint: disable=W0613
        """
        Get the column description.

        :param col: the column
        :return: the event description, if any
        """
        return None

    @classmethod
    def create(cls, time: int, **_) -> "Event":  # noqa  # pylint: disable=W0613
        """
        Create the event from the columns.

        :param time: the event time
        :return: the event
        """
        return cls(check_time(time))

    def event_get_csv_value(
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
        return (self.__class__ is other.__class__) and (
            self.time == other.time)

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
        return (self.__class__ is not other.__class__) or (
            self.time != other.time)

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

        _load_event_types()

        cols: Final[dict[str, int | None]] = {}
        cols[COLUMN_TIME] = csv_column(columns, COLUMN_TIME, True)
        cols[COLUMN_TYPE] = csv_column(columns, COLUMN_TYPE, True)
        for cls in Event.eventclass_classes():
            cls_cols = cls.eventclass_get_csv_columns()
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
        cls: Final[type[Event]] = Event.eventclass_from_name(
            data[cols[COLUMN_TYPE]])
        col_names = cls.eventclass_get_csv_columns()
        ret = cls.create(time=str_to_time(data[cols[
            COLUMN_TIME]]), **{c: csv_str_or_none(
                data, cols[c]) for c in col_names})
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
        for cls in Event.eventclass_classes():
            for col in cls.eventclass_get_csv_columns():
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
        yield data.__class__.eventclass_get_csv_type()
        for col in self.__cols:
            yield data.event_get_csv_value(col)

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
        for cls in Event.eventclass_classes():
            for col in cls.eventclass_get_csv_columns():
                if col in cols:
                    desc = cls.eventclass_get_col_desc(col)
                    if desc:
                        yield f"{cols[col]}: {desc}"
                        del cols[col]
        yield ""
        yield f"Event types (column {self.__col_type}):"
        for name, cls in Event.eventclass_types():
            desc = cls.eventclass_get_event_desc()
            if desc:
                yield f"  - {name}: {desc}"


def _load_event_types() -> None:
    """Load all event types."""
    from importlib import (  # noqa  # pylint: disable=C0415
        import_module)  # noqa  # type: ignore  # pylint: disable=C0415
    for name in ("warehouse.event.time",
                 "warehouse.event.storage",
                 "warehouse.event.bins"):
        import_module(name)  # noqa  # type: ignore  # pylint: disable=C0415
