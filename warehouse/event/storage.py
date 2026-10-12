"""
Events regarding the storage of material.

>>> from warehouse.instance.bin_type import BinType
>>> with context():
...     BinType(None, "random_small", 1000)
...     BinType(None, "random_large", 500)
...     BinType(None, "hat_bins", 30)
...     Material(None, "hat", "hat_bins")
...     Material(None, "shoe", "random_small")
...     Material(None, "trousers", "random_large")
...     ev01 = WarehouseIn(1500000000000, "hat", 1200)
...     ev02 = WarehouseIn(1500000020000, "shoe", 40)
...     ev03 = WarehouseIn(1500007020000, "trousers", 750)
...     ev04 = OverstockIn(1500009000000, "hat", 200)
...     ev05 = OverstockIn(1500009500000, "shoe", 10)
...     ev06 = OverstockIn(1500029500000, "trousers", 250)
...     ev07 = OverstockOut(1500039000000, "hat", 200)
...     ev08 = OverstockOut(1500049500000, "shoe", 10)
...     ev09 = OverstockOut(1500051500000, "trousers", 250)
...     ev10 = WarehouseOut(1500000000000, "hat", 1200)
...     ev11 = WarehouseOut(1500000020000, "shoe", 40)
...     ev12 = WarehouseOut(1500007020000, "trousers", 750)
...
...     events_1 = (ev01, ev02, ev03, ev04, ev05, ev06, ev07,
...                 ev08, ev09, ev10, ev11, ev12)
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
Material(key=2, name='trousers', bin_type=BinType(key=1, name='random_large', \
amount=500))
WarehouseIn(amount=1200, material=Material(key=0, name='hat', bin_type=\
BinType(key=2, name='hat_bins', amount=30)), time=1500000000000)
WarehouseIn(amount=40, material=Material(key=1, name='shoe', bin_type=\
BinType(key=0, name='random_small', amount=1000)), time=1500000020000)
WarehouseIn(amount=750, material=Material(key=2, name='trousers', bin_type=\
BinType(key=1, name='random_large', amount=500)), time=1500007020000)
OverstockIn(amount=200, material=Material(key=0, name='hat', bin_type=\
BinType(key=2, name='hat_bins', amount=30)), time=1500009000000)
OverstockIn(amount=10, material=Material(key=1, name='shoe', bin_type=\
BinType(key=0, name='random_small', amount=1000)), time=1500009500000)
OverstockIn(amount=250, material=Material(key=2, name='trousers', bin_type=\
BinType(key=1, name='random_large', amount=500)), time=1500029500000)
OverstockOut(amount=200, material=Material(key=0, name='hat', bin_type=\
BinType(key=2, name='hat_bins', amount=30)), time=1500039000000)
OverstockOut(amount=10, material=Material(key=1, name='shoe', bin_type=\
BinType(key=0, name='random_small', amount=1000)), time=1500049500000)
OverstockOut(amount=250, material=Material(key=2, name='trousers', bin_type=\
BinType(key=1, name='random_large', amount=500)), time=1500051500000)
WarehouseOut(amount=1200, material=Material(key=0, name='hat', bin_type=\
BinType(key=2, name='hat_bins', amount=30)), time=1500000000000)
WarehouseOut(amount=40, material=Material(key=1, name='shoe', bin_type=\
BinType(key=0, name='random_small', amount=1000)), time=1500000020000)
WarehouseOut(amount=750, material=Material(key=2, name='trousers', bin_type=\
BinType(key=1, name='random_large', amount=500)), time=1500007020000)
<BLANKLINE>
===================
<BLANKLINE>
time;type;material;amount;binType
2017-07-14T10:40+08;warehouse_in;hat;1200
2017-07-14T10:40:20+08;warehouse_in;shoe;40
2017-07-14T12:37+08;warehouse_in;trousers;750
2017-07-14T13:10+08;overstock_in;hat;200
2017-07-14T13:18:20+08;overstock_in;shoe;10
2017-07-14T18:51:40+08;overstock_in;trousers;250
2017-07-14T21:30+08;overstock_out;hat;200
2017-07-15T00:25+08;overstock_out;shoe;10
2017-07-15T00:58:20+08;overstock_out;trousers;250
2017-07-14T10:40+08;warehouse_out;hat;1200
2017-07-14T10:40:20+08;warehouse_out;shoe;40
2017-07-14T12:37+08;warehouse_out;trousers;750
<BLANKLINE>
===================
<BLANKLINE>
WarehouseIn(amount=1200, material=Material(key=0, name='hat', bin_type=\
BinType(key=2, name='hat_bins', amount=30)), time=1500000000000)
WarehouseIn(amount=40, material=Material(key=1, name='shoe', bin_type=\
BinType(key=0, name='random_small', amount=1000)), time=1500000020000)
WarehouseIn(amount=750, material=Material(key=2, name='trousers', bin_type=\
BinType(key=1, name='random_large', amount=500)), time=1500007020000)
OverstockIn(amount=200, material=Material(key=0, name='hat', bin_type=\
BinType(key=2, name='hat_bins', amount=30)), time=1500009000000)
OverstockIn(amount=10, material=Material(key=1, name='shoe', bin_type=\
BinType(key=0, name='random_small', amount=1000)), time=1500009500000)
OverstockIn(amount=250, material=Material(key=2, name='trousers', bin_type=\
BinType(key=1, name='random_large', amount=500)), time=1500029500000)
OverstockOut(amount=200, material=Material(key=0, name='hat', bin_type=\
BinType(key=2, name='hat_bins', amount=30)), time=1500039000000)
OverstockOut(amount=10, material=Material(key=1, name='shoe', bin_type=\
BinType(key=0, name='random_small', amount=1000)), time=1500049500000)
OverstockOut(amount=250, material=Material(key=2, name='trousers', bin_type=\
BinType(key=1, name='random_large', amount=500)), time=1500051500000)
WarehouseOut(amount=1200, material=Material(key=0, name='hat', bin_type=\
BinType(key=2, name='hat_bins', amount=30)), time=1500000000000)
WarehouseOut(amount=40, material=Material(key=1, name='shoe', bin_type=\
BinType(key=0, name='random_small', amount=1000)), time=1500000020000)
WarehouseOut(amount=750, material=Material(key=2, name='trousers', bin_type=\
BinType(key=1, name='random_large', amount=500)), time=1500007020000)
"""
from typing import Final, Self

from pycommons.types import check_int_range

from warehouse.instance.element import context
from warehouse.instance.event import Event
from warehouse.instance.material import Material

#: the material column
COLUMN_MATERIAL: Final[str] = "material"
#: the amount column
COLUMN_AMOUNT: Final[str] = "amount"


class StorageEvent(Event):
    """An amount of material has changed places."""

    @classmethod
    def eventclass_needs_register(cls) -> bool:
        """
        Check whether the event class need to be registered.

        :returns: `True` if it should be registered as a possible event type,
            `False` otherwise; in this case: `True` if it should be is not
            `Event` or `StorageEvent`.
        """
        return super().eventclass_needs_register() and (
            cls.__name__ != "StorageEvent")

    def __init__(self, time: int, material: Material | int | str,
                 amount: int) -> None:
        """
        Create the storage event.

        :param time: the time when we want to store material in the warehouse
        :param material: the material that we want to store/retrieve
        :param amount: the amount of material to store/retrieve
        """
        super().__init__(time)
        if material.__class__ is not Material:
            with context() as ctx:
                material = ctx.resolve(Material, material)  # type: ignore

        #: the material being transferred
        self.material: Material = material

        #: the amount of material being transfered
        self.amount: int = check_int_range(
            amount, "amount", 1, 1_000_000)

    def copy(self) -> Self:
        """
        Create a copy of this event.

        :return: an independent copy of this event
        """
        return self.__class__(self.time, self.material, self.amount)

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
            self.amount == other.amount)

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
            self.amount != other.amount)

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
        if col == COLUMN_MATERIAL:
            return "the type of material associated with the event"
        if col == COLUMN_AMOUNT:
            return "the amount of material stored or retrieved"
        return None

    def event_get_csv_value(self, column: str) -> str:
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
    def eventclass_get_csv_columns(cls) -> tuple[str, ...]:
        """
        Get the CSV columns of the event.

        :return: the csv columns
        """
        return COLUMN_MATERIAL, COLUMN_AMOUNT

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
            data[cols[COLUMN_AMOUNT]]))


class WarehouseIn(StorageEvent):
    """Store material in the warehouse."""

    @classmethod
    def eventclass_get_csv_type(cls) -> str:
        """
        Get the csv type of the event.

        :return: the csv type
        """
        return "warehouse_in"

    @classmethod
    def eventclass_get_event_desc(cls) -> str | None:
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
    def eventclass_get_csv_type(cls) -> str:
        """
        Get the csv type of the event.

        :return: the csv type
        """
        return "warehouse_out"

    @classmethod
    def eventclass_get_event_desc(cls) -> str | None:
        """
        Get the event description.

        :return: the event description, if any
        """
        return ("a certain amount of a material is requested from the "
                "warehouse and needs to be taken out of the stored amount of "
                "this material; it then needs to be decided from which bin to"
                " take it or, if there is overstock, maybe it can be taken "
                "from there.")


class WarehouseDelivers(StorageEvent):
    """Material was retrieved from the warehouse."""

    @classmethod
    def eventclass_get_csv_type(cls) -> str:
        """
        Get the csv type of the event.

        :return: the csv type
        """
        return "warehouse_delivered"

    @classmethod
    def eventclass_get_event_desc(cls) -> str | None:
        """
        Get the event description.

        :return: the event description, if any
        """
        return "a certain amount of a material is shipped by the warehouse"


class OverstockIn(StorageEvent):
    """Store material in the overstock."""

    @classmethod
    def eventclass_get_csv_type(cls) -> str:
        """
        Get the csv type of the event.

        :return: the csv type
        """
        return "overstock_in"

    @classmethod
    def eventclass_get_event_desc(cls) -> str | None:
        """
        Get the event description.

        :return: the event description, if any
        """
        return ("a certain amount of a material has arrived in the warehouse,"
                " but it could not be put into any bin, because all bins are "
                "full; the material was placed into the 'overstock', meaning "
                "that it is just lying around somewhere.")


class OverstockOut(StorageEvent):
    """Retrieve material from the overstock."""

    @classmethod
    def eventclass_get_csv_type(cls) -> str:
        """
        Get the csv type of the event.

        :return: the csv type
        """
        return "overstock_out"

    @classmethod
    def eventclass_get_event_desc(cls) -> str | None:
        """
        Get the event description.

        :return: the event description, if any
        """
        return ("a certain amount of a material was taken from the overstock:"
                " this material was not in any bin, because all bins were "
                "occupied; so it was just lying around.")


class InsufficientMaterial(StorageEvent):
    """Not enough material was available to satisfy a request."""

    @classmethod
    def eventclass_get_csv_type(cls) -> str:
        """
        Get the csv type of the event.

        :return: the csv type
        """
        return "insufficient"

    @classmethod
    def eventclass_get_event_desc(cls) -> str | None:
        """
        Get the event description.

        :return: the event description, if any
        """
        return ("there was not enough material in the "
                "warehouse to satisfy a warehouse_out request.")
