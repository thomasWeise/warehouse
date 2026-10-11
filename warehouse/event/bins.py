"""
Events regarding the storage and retrieval of material to and from bins.

>>> from warehouse.instance.bin_type import BinType
>>> with context():
...     BinType(None, "random_small", 1000)
...     BinType(None, "random_large", 500)
...     BinType(None, "hat_bins", 30)
...     Material(None, "hat", "hat_bins")
...     Material(None, "shoe", "random_small")
...     Material(None, "trousers", "random_large")
...     ev01 = BinIn(1500000000000, "hat", 10, "hat_bins")
...     ev02 = BinIn(1700000000000, "shoe", 15, "random_small")
...     ev03 = BinIn(1800000000000, "trousers", 7, "random_large")
...     ev04 = BinOut(1900000000000, "hat", 9, "hat_bins")
...     ev05 = BinOut(2000000000000, "shoe", 8, "random_small")
...     ev06 = BinOut(2100000000000, "trousers", 3, "random_large")
...
...     events_1 = (ev01, ev02, ev03, ev04, ev05, ev06)
...
...     for ev in events_1:
...         print(ev)
...
...     print()
...     print("===================")
...     print()
...
...     csv = list(Event.to_csv(events_1))
...     for row in csv:
...         if not str.startswith(row, "#"):
...             print(row)
...
...     print()
...     print("===================")
...     print()
...
...     events_2 = tuple(Event.from_csv(csv))
...     for ev in events_2:
...         print(ev)
BinType(key=0, name='random_small', amount=1000)
BinType(key=1, name='random_large', amount=500)
BinType(key=2, name='hat_bins', amount=30)
Material(key=0, name='hat', bin_type=BinType(key=2, name='hat_bins', \
amount=30))
Material(key=1, name='shoe', bin_type=BinType(key=0, name='random_small', \
amount=1000))
Material(key=2, name='trousers', bin_type=BinType(key=1, \
name='random_large', amount=500))
BinIn(amount=10, bin_type=BinType(key=2, name='hat_bins', amount=30), \
material=Material(key=0, name='hat', bin_type=BinType(key=2, \
name='hat_bins', amount=30)), time=1500000000000)
BinIn(amount=15, bin_type=BinType(key=0, name='random_small', amount=1000), \
material=Material(key=1, name='shoe', bin_type=BinType(key=0, \
name='random_small', amount=1000)), time=1700000000000)
BinIn(amount=7, bin_type=BinType(key=1, name='random_large', amount=500), \
material=Material(key=2, name='trousers', bin_type=BinType(key=1, \
name='random_large', amount=500)), time=1800000000000)
BinOut(amount=9, bin_type=BinType(key=2, name='hat_bins', amount=30), \
material=Material(key=0, name='hat', bin_type=BinType(key=2, \
name='hat_bins', amount=30)), time=1900000000000)
BinOut(amount=8, bin_type=BinType(key=0, name='random_small', \
amount=1000), material=Material(key=1, name='shoe', bin_type=BinType(key=0, \
name='random_small', amount=1000)), time=2000000000000)
BinOut(amount=3, bin_type=BinType(key=1, name='random_large', amount=500), \
material=Material(key=2, name='trousers', bin_type=BinType(key=1, \
name='random_large', amount=500)), time=2100000000000)
<BLANKLINE>
===================
<BLANKLINE>
time;type;material;amount;binType
2017-07-14T10:40+08;bin_in;hat;10;hat_bins
2023-11-15T06:13:20+08;bin_in;shoe;15;random_small
2027-01-15T16+08;bin_in;trousers;7;random_large
2030-03-18T01:46:40+08;bin_out;hat;9;hat_bins
2033-05-18T11:33:20+08;bin_out;shoe;8;random_small
2036-07-18T21:20+08;bin_out;trousers;3;random_large
<BLANKLINE>
===================
<BLANKLINE>
BinIn(amount=10, bin_type=BinType(key=2, name='hat_bins', amount=30), \
material=Material(key=0, name='hat', bin_type=BinType(key=2, \
name='hat_bins', amount=30)), time=1500000000000)
BinIn(amount=15, bin_type=BinType(key=0, name='random_small', amount=1000), \
material=Material(key=1, name='shoe', bin_type=BinType(key=0, \
name='random_small', amount=1000)), time=1700000000000)
BinIn(amount=7, bin_type=BinType(key=1, name='random_large', amount=500), \
material=Material(key=2, name='trousers', bin_type=BinType(key=1, \
name='random_large', amount=500)), time=1800000000000)
BinOut(amount=9, bin_type=BinType(key=2, name='hat_bins', amount=30), \
material=Material(key=0, name='hat', bin_type=BinType(key=2, \
name='hat_bins', amount=30)), time=1900000000000)
BinOut(amount=8, bin_type=BinType(key=0, name='random_small', \
amount=1000), material=Material(key=1, name='shoe', bin_type=BinType(key=0, \
name='random_small', amount=1000)), time=2000000000000)
BinOut(amount=3, bin_type=BinType(key=1, name='random_large', amount=500), \
material=Material(key=2, name='trousers', bin_type=BinType(key=1, \
name='random_large', amount=500)), time=2100000000000)
"""

from typing import Self

from warehouse.event.storage import (
    COLUMN_AMOUNT,
    COLUMN_MATERIAL,
    StorageEvent,
)
from warehouse.instance.bin_type import BinType
from warehouse.instance.element import context
from warehouse.instance.event import Event
from warehouse.instance.material import COLUMN_BIN_TYPE, Material


class BinEvent(StorageEvent):
    """An amount of material has changed places."""

    @classmethod
    def eventclass_needs_register(cls) -> bool:
        """
        Check whether the class should be registered.

        :returns: `True` if it should be registered as a possible event type,
            `False` otherwise; in this class, if it is neither `Event`,
            `StorageEvent`, nor `BinEvent`.
        """
        return super().eventclass_needs_register() and (
            cls.__name__ != "BinEvent")

    def __init__(self, time: int, material: Material | int | str,
                 amount: int, bin_type: BinType | int | str) -> None:
        """
        Create the bin event.

        :param time: the time when we want to store material in the warehouse
        :param material: the material that we want to store/retrieve
        :param amount: the amount of material to store/retrieve
        """
        need_bin: bool = bin_type.__class__ is not BinType
        if (material.__class__ is not Material) or need_bin:
            with context() as ctx:
                super().__init__(time, material, amount)
                if need_bin:
                    bin_type = ctx.resolve(BinType, bin_type)  # type: ignore
        else:
            super().__init__(time, material, amount)

        #: the bin type into or out of which the material is being transferred
        self.bin_type: BinType = bin_type  # type: ignore

    def copy(self) -> Self:
        """
        Create a copy of this event.

        :return: an independent copy of this event
        """
        return self.__class__(
            self.time, self.material, self.amount, self.bin_type)

    def __eq__(self, other) -> bool:
        """
        Compare this event with another event object for "equality".

        :param other: the other event
        :return: `True` if this event is equal to the other event,
            `False` otherwise
        """
        return (self.__class__ is other.__class__) and (
            self.time == other.time) and (
            self.material == other.material) and (
            self.amount == other.amount) and (
            self.bin_type == other.bin_type)

    def __ne__(self, other) -> bool:
        """
        Compare this event with another event object for "inequality".

        :param other: the other event
        :return: `True` if this event is not equal than the other event,
            `False` otherwise
        """
        return (self.__class__ is not other.__class__) or (
            self.time != other.time) or (
            self.material != other.material) or (
            self.amount != other.amount) or (
            self.bin_type != other.bin_type)

    def __hash__(self) -> int:
        """
        You cannot hash events, because they are mutable.

        :raises TypeError: always
        """
        raise TypeError

    @classmethod
    def eventclass_get_col_desc(cls, col: str) -> str | None:
        """
        Get the column description.

        :param col: the column
        :return: the event description, if any
        """
        if col == COLUMN_BIN_TYPE:
            return ("the type of bin into which is material stored in or "
                    "taken out of")
        return super().eventclass_get_col_desc(col)

    def event_get_csv_value(self, column: str) -> str:
        """
        Get a specific csv value.

        :param column: the csv column
        :return: the value
        """
        if column == COLUMN_BIN_TYPE:
            return self.bin_type.name
        return super().event_get_csv_value(column)

    @classmethod
    def eventclass_get_csv_columns(cls) -> tuple[str, ...]:
        """
        Get the CSV columns of the event.

        :return: the csv columns
        """
        return (*super().eventclass_get_csv_columns(),
                COLUMN_BIN_TYPE)

    @classmethod
    def eventclass_create_event(cls, time: int, cols: dict[
            str, int | None], data: list[str]) -> Event:
        """
        Create the storage event.

        :param time: the time
        :param cols: the csv columns
        :param data: the csv data
        :return: the event
        """
        return cls(time, data[cols[COLUMN_MATERIAL]], int(
            data[cols[COLUMN_AMOUNT]]), data[cols[COLUMN_BIN_TYPE]])


class BinIn(BinEvent):
    """Store material in a bin."""

    @classmethod
    def eventclass_get_csv_type(cls) -> str:
        """
        Get the csv type of the event.

        :return: the csv type
        """
        return "bin_in"

    @classmethod
    def eventclass_get_event_desc(cls) -> str | None:
        """
        Get the event description.

        :return: the event description, if any
        """
        return ("a certain amount of a material is stored in a certain type "
                "of bins; the amount of material and the amount of bins used "
                "are the same, as material always comes in units that are "
                "multiples of bin sizes.")


class BinOut(BinEvent):
    """Retrieve material from a bin."""

    @classmethod
    def eventclass_get_csv_type(cls) -> str:
        """
        Get the csv type of the event.

        :return: the csv type
        """
        return "bin_out"

    @classmethod
    def eventclass_get_event_desc(cls) -> str | None:
        """
        Get the event description.

        :return: the event description, if any
        """
        return ("a certain amount of a material is retrieved from a certain "
                "type of bins; the amount of material and the amount of bins "
                "used are the same, as material always comes in units that "
                "are multiples of bin sizes.")
