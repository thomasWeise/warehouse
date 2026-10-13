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
...     ev01 = BinIn.create(1500000000000, "hat", 10, "hat_bins")
...     ev02 = BinIn.create(1700000000000, "shoe", 15, "random_small")
...     ev03 = BinIn.create(1800000000000, "trousers", 7, "random_large")
...     ev04 = BinOut.create(1900000000000, "hat", 9, "hat_bins")
...     ev05 = BinOut.create(2000000000000, "shoe", 8, "random_small")
...     ev06 = BinOut.create(2100000000000, "trousers", 3, "random_large")
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
...     csv = list(BinEvent.to_csv(events_1))
...     for row in csv:
...         if not str.startswith(row, "#"):
...             print(row)
...
...     print()
...     print("===================")
...     print()
...
...     events_2 = tuple(BinEvent.from_csv(csv))
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
BinIn(time=1500000000000, material=Material(key=0, name='hat', \
bin_type=BinType(key=2, name='hat_bins', amount=30)), amount=10, \
bin_type=BinType(key=2, name='hat_bins', amount=30))
BinIn(time=1700000000000, material=Material(key=1, name='shoe', \
bin_type=BinType(key=0, name='random_small', amount=1000)), \
amount=15, bin_type=BinType(key=0, name='random_small', amount=1000))
BinIn(time=1800000000000, material=Material(key=2, name='trousers', \
bin_type=BinType(key=1, name='random_large', amount=500)), amount=7, \
bin_type=BinType(key=1, name='random_large', amount=500))
BinOut(time=1900000000000, material=Material(key=0, name='hat', \
bin_type=BinType(key=2, name='hat_bins', amount=30)), amount=9, \
bin_type=BinType(key=2, name='hat_bins', amount=30))
BinOut(time=2000000000000, material=Material(key=1, name='shoe', \
bin_type=BinType(key=0, name='random_small', amount=1000)), amount=8, \
bin_type=BinType(key=0, name='random_small', amount=1000))
BinOut(time=2100000000000, material=Material(key=2, name='trousers', \
bin_type=BinType(key=1, name='random_large', amount=500)), amount=3, \
bin_type=BinType(key=1, name='random_large', amount=500))
<BLANKLINE>
===================
<BLANKLINE>
time;type;material;amount;bin_type
2017-07-14T10:40+08;bin_in;hat;10;hat_bins
2023-11-15T06:13:20+08;bin_in;shoe;15;random_small
2027-01-15T16+08;bin_in;trousers;7;random_large
2030-03-18T01:46:40+08;bin_out;hat;9;hat_bins
2033-05-18T11:33:20+08;bin_out;shoe;8;random_small
2036-07-18T21:20+08;bin_out;trousers;3;random_large
<BLANKLINE>
===================
<BLANKLINE>
BinIn(time=1500000000000, material=Material(key=0, name='hat', \
bin_type=BinType(key=2, name='hat_bins', amount=30)), amount=10, \
bin_type=BinType(key=2, name='hat_bins', amount=30))
BinIn(time=1700000000000, material=Material(key=1, name='shoe', \
bin_type=BinType(key=0, name='random_small', amount=1000)), \
amount=15, bin_type=BinType(key=0, name='random_small', amount=1000))
BinIn(time=1800000000000, material=Material(key=2, name='trousers', \
bin_type=BinType(key=1, name='random_large', amount=500)), amount=7, \
bin_type=BinType(key=1, name='random_large', amount=500))
BinOut(time=1900000000000, material=Material(key=0, name='hat', \
bin_type=BinType(key=2, name='hat_bins', amount=30)), amount=9, \
bin_type=BinType(key=2, name='hat_bins', amount=30))
BinOut(time=2000000000000, material=Material(key=1, name='shoe', \
bin_type=BinType(key=0, name='random_small', amount=1000)), amount=8, \
bin_type=BinType(key=0, name='random_small', amount=1000))
BinOut(time=2100000000000, material=Material(key=2, name='trousers', \
bin_type=BinType(key=1, name='random_large', amount=500)), amount=3, \
bin_type=BinType(key=1, name='random_large', amount=500))

>>> hash(ev06)
-6371751855485235984
"""


from dataclasses import dataclass, field

from warehouse.event.storage import (
    COLUMN_AMOUNT,
    COLUMN_MATERIAL,
    StorageEvent,
    check_to_amount,
)
from warehouse.instance.bin_type import BinType
from warehouse.instance.element import context
from warehouse.instance.material import COLUMN_BIN_TYPE, Material


@dataclass(frozen=True, init=True, order=False, eq=False, unsafe_hash=True)
class BinEvent(StorageEvent):  # noqa: PLW1641
    """An amount of material has changed places."""

    bin_type: BinType = field(hash=True)

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
        return COLUMN_MATERIAL, COLUMN_AMOUNT, COLUMN_BIN_TYPE

    @classmethod
    def create(  # type: ignore  # pylint: disable=W0221
            cls, time: int, material: int | str | Material,
            amount: int | str,
            bin_type: int | str | BinType) -> "BinEvent":  # type: ignore
        """
        Create the storage event.

        :param time: the time
        :param material: the material to use
        :param amount: the amount of the material to use
        :return: the bin event
        """
        need_bin: bool = bin_type.__class__ is not BinType
        need_material: bool = material.__class__ is not Material
        if need_material or need_bin:
            with context() as ctx:
                if need_material:
                    material = ctx.resolve(Material, material)  # type: ignore
                if need_bin:
                    bin_type = ctx.resolve(BinType, bin_type)  # type: ignore
        return cls(
            time, material, check_to_amount(amount), bin_type)  # type: ignore


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
