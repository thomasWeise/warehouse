"""
Events regarding the storage and retrieval of parts in/from the warehouse.

>>> from warehouse.instance.bin_type import BinType
>>> with context():
...     BinType(None, "random_small", 1000, is_random=True)
...     BinType(None, "random_large", 500, is_random=True)
...     BinType(None, "hat_bins", 30)
...     Part(None, "hat", "hat_bins")
...     Part(None, "shoe", "random_small")
...     Part(None, "trousers", "random_large")
...     ev01 = WarehouseIn.create(1500000000000, 0, "hat", 1200)
...     ev02 = WarehouseIn.create(1500000020000, 0, "shoe", 40)
...     ev03 = WarehouseIn.create(1500007020000, 0, "trousers", 750)
...     ev04 = OverstockIn.create(1500009000000, 0, "hat", 200)
...     ev05 = OverstockIn.create(1500009500000, 0, "shoe", 10)
...     ev06 = OverstockIn.create(1500029500000, 0, "trousers", 250)
...     ev07 = OverstockOut.create(1500039000000, 0, "hat", 200)
...     ev08 = OverstockOut.create(1500049500000, 0, "shoe", 10)
...     ev09 = OverstockOut.create(1500051500000, 0, "trousers", 250)
...     ev10 = WarehouseDemand.create(1600000000000, 0, "hat", 1200)
...     ev11 = WarehouseDemand.create(1600000020000, 0, "shoe", 40)
...     ev12 = WarehouseDemand.create(1600007020000, 0, "trousers", "750")
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
...     for row in csv[1:]:
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
BinType(key=0, name='random_small', amount=1000, is_random=True)
BinType(key=1, name='random_large', amount=500, is_random=True)
BinType(key=2, name='hat_bins', amount=30, is_random=False)
Part(key=0, name='hat', bin_type=BinType(key=2, name='hat_bins', amount=30, \
is_random=False))
Part(key=1, name='shoe', bin_type=BinType(key=0, name='random_small', \
amount=1000, is_random=True))
Part(key=2, name='trousers', bin_type=BinType(key=1, name='random_large', \
amount=500, is_random=True))
WarehouseIn(time=1500000000000, priority=0, part=Part(key=0, name='hat', \
bin_type=BinType(key=2, name='hat_bins', amount=30, is_random=False)), \
amount=1200)
WarehouseIn(time=1500000020000, priority=0, part=Part(key=1, name='shoe', \
bin_type=BinType(key=0, name='random_small', amount=1000, \
is_random=True)), amount=40)
WarehouseIn(time=1500007020000, priority=0, part=Part(key=2, \
name='trousers', bin_type=BinType(key=1, name='random_large', amount=500, \
is_random=True)), amount=750)
OverstockIn(time=1500009000000, priority=0, part=Part(key=0, name='hat', \
bin_type=BinType(key=2, name='hat_bins', amount=30, \
is_random=False)), amount=200)
OverstockIn(time=1500009500000, priority=0, part=Part(key=1, name='shoe', \
bin_type=BinType(key=0, name='random_small', amount=1000, \
is_random=True)), amount=10)
OverstockIn(time=1500029500000, priority=0, part=Part(key=2, \
name='trousers', bin_type=BinType(key=1, name='random_large', \
amount=500, is_random=True)), amount=250)
OverstockOut(time=1500039000000, priority=0, part=Part(key=0, name='hat', \
bin_type=BinType(key=2, name='hat_bins', amount=30, \
is_random=False)), amount=200)
OverstockOut(time=1500049500000, priority=0, part=Part(key=1, name='shoe', \
bin_type=BinType(key=0, name='random_small', amount=1000, \
is_random=True)), amount=10)
OverstockOut(time=1500051500000, priority=0, part=Part(key=2, \
name='trousers', bin_type=BinType(key=1, name='random_large', amount=500, \
is_random=True)), amount=250)
WarehouseDemand(time=1600000000000, priority=0, part=Part(key=0, name='hat', \
bin_type=BinType(key=2, name='hat_bins', amount=30, \
is_random=False)), amount=1200)
WarehouseDemand(time=1600000020000, priority=0, part=Part(key=1, \
name='shoe', bin_type=BinType(key=0, name='random_small', amount=1000, \
is_random=True)), amount=40)
WarehouseDemand(time=1600007020000, priority=0, part=Part(key=2, \
name='trousers', bin_type=BinType(key=1, name='random_large', amount=500, \
is_random=True)), amount=750)
<BLANKLINE>
===================
<BLANKLINE>
2017-07-14 10:40;warehouse_in;hat;1200
2017-07-14 10:40:20;warehouse_in;shoe;40
2017-07-14 12:37;warehouse_in;trousers;750
2017-07-14 13:10;overstock_in;hat;200
2017-07-14 13:18:20;overstock_in;shoe;10
2017-07-14 18:51:40;overstock_in;trousers;250
2017-07-14 21:30;overstock_out;hat;200
2017-07-15 00:25;overstock_out;shoe;10
2017-07-15 00:58:20;overstock_out;trousers;250
2020-09-13 20:26:40;warehouse_demand;hat;1200
2020-09-13 20:27;warehouse_demand;shoe;40
2020-09-13 22:23:40;warehouse_demand;trousers;750
<BLANKLINE>
===================
<BLANKLINE>
WarehouseIn(time=1500000000000, priority=0, part=Part(key=0, name='hat', \
bin_type=BinType(key=2, name='hat_bins', amount=30, is_random=False)), \
amount=1200)
WarehouseIn(time=1500000020000, priority=0, part=Part(key=1, name='shoe', \
bin_type=BinType(key=0, name='random_small', amount=1000, \
is_random=True)), amount=40)
WarehouseIn(time=1500007020000, priority=0, part=Part(key=2, \
name='trousers', bin_type=BinType(key=1, name='random_large', amount=500, \
is_random=True)), amount=750)
OverstockIn(time=1500009000000, priority=0, part=Part(key=0, name='hat', \
bin_type=BinType(key=2, name='hat_bins', amount=30, \
is_random=False)), amount=200)
OverstockIn(time=1500009500000, priority=0, part=Part(key=1, name='shoe', \
bin_type=BinType(key=0, name='random_small', amount=1000, \
is_random=True)), amount=10)
OverstockIn(time=1500029500000, priority=0, part=Part(key=2, \
name='trousers', bin_type=BinType(key=1, name='random_large', \
amount=500, is_random=True)), amount=250)
OverstockOut(time=1500039000000, priority=0, part=Part(key=0, name='hat', \
bin_type=BinType(key=2, name='hat_bins', amount=30, \
is_random=False)), amount=200)
OverstockOut(time=1500049500000, priority=0, part=Part(key=1, name='shoe', \
bin_type=BinType(key=0, name='random_small', amount=1000, \
is_random=True)), amount=10)
OverstockOut(time=1500051500000, priority=0, part=Part(key=2, \
name='trousers', bin_type=BinType(key=1, name='random_large', amount=500, \
is_random=True)), amount=250)
WarehouseDemand(time=1600000000000, priority=0, part=Part(key=0, name='hat', \
bin_type=BinType(key=2, name='hat_bins', amount=30, \
is_random=False)), amount=1200)
WarehouseDemand(time=1600000020000, priority=0, part=Part(key=1, \
name='shoe', bin_type=BinType(key=0, name='random_small', amount=1000, \
is_random=True)), amount=40)
WarehouseDemand(time=1600007020000, priority=0, part=Part(key=2, \
name='trousers', bin_type=BinType(key=1, name='random_large', amount=500, \
is_random=True)), amount=750)

>>> hash(ev02)
7497175492123864008
"""
from dataclasses import dataclass, field

from warehouse.instance.element import COLUMN_AMOUNT, check_to_amount, context
from warehouse.instance.event import Event
from warehouse.instance.part import COLUMN_PART, Part


@dataclass(frozen=True, init=True, order=False, eq=False, unsafe_hash=True)
class StorageEvent(Event):  # noqa: PLW1641
    """An amount of part has changed places."""

    #: the part
    part: Part = field(hash=True)
    #: the amount to store/retrieve
    amount: int = field(hash=True)

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

    def __eq__(self, other) -> bool:
        """
        Compare this event with another event object for "equality".

        :param other: the other event
        :return: `True` if this event is equal to the other event,
            `False` otherwise
        """
        return (self.__class__ is other.__class__) and (
            self.time == other.time) and (
            self.priority == other.priority) and (
            self.part == other.part) and (
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
            self.priority != other.priority) or (
            self.part != other.part) or (
            self.amount != other.amount)

    @classmethod
    def eventclass_get_col_desc(cls, col: str) -> str | None:
        """
        Get the column description.

        :param col: the column
        :return: the event description, if any
        """
        if col == COLUMN_PART:
            return "the type of part associated with the event"
        if col == COLUMN_AMOUNT:
            return "the amount of part stored or retrieved"
        return None

    def event_get_csv_value(self, column: str) -> str:
        """
        Get a specific csv value.

        :param column: the csv column
        :return: the value
        """
        if column == COLUMN_PART:
            return self.part.name
        if column == COLUMN_AMOUNT:
            return str(self.amount)
        return ""

    @classmethod
    def eventclass_get_csv_columns(cls) -> tuple[str, ...]:
        """
        Get the CSV columns of the event.

        :return: the csv columns
        """
        return COLUMN_PART, COLUMN_AMOUNT

    @classmethod
    def create(  # type: ignore  # pylint: disable=W0221
            cls, time: int, priority: int, part: int | str | Part,
            amount: int | str, **_) -> "StorageEvent":  # type: ignore
        """
        Create the storage event.

        :param time: the time
        :param priority: the event priority
        :param part: the part to use
        :param amount: the amount of the part to use
        :return: the storage event
        """
        with context() as ctx:
            part = ctx.resolve(Part, part)
        return cls(time, priority, part,  # type: ignore
                   check_to_amount(amount))  # type: ignore


class WarehouseIn(StorageEvent):
    """Store part in the warehouse."""

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
        return ("a certain amount of a part has arrived at the warehouse "
                "and needs to be stored; it then needs to be decided where to"
                " put it.")


class WarehouseDemand(StorageEvent):
    """Retrieve parts from the warehouse."""

    @classmethod
    def eventclass_get_csv_type(cls) -> str:
        """
        Get the csv type of the event.

        :return: the csv type
        """
        return "warehouse_demand"

    @classmethod
    def eventclass_get_event_desc(cls) -> str | None:
        """
        Get the event description.

        :return: the event description, if any
        """
        return ("a certain amount of a part is requested from the "
                "warehouse and needs to be taken out of the stored amount of "
                "this part; it then needs to be decided from which bin to"
                " take it or, if there is overstock, maybe it can be taken "
                "from there.")


class WarehouseDelivers(StorageEvent):
    """Part was retrieved from the warehouse."""

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
        return "a certain amount of a part is shipped by the warehouse"


class OverstockIn(StorageEvent):
    """Store part in the overstock."""

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
        return ("a certain amount of a part has arrived in the warehouse,"
                " but it could not be put into any bin, because all bins are "
                "full; the part was placed into the 'overstock', meaning "
                "that it is just lying around somewhere.")


class OverstockOut(StorageEvent):
    """Retrieve part from the overstock."""

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
        return ("a certain amount of a part was taken from the overstock:"
                " this part was not in any bin, because all bins were "
                "occupied; so it was just lying around.")


class Understock(StorageEvent):
    """Not enough part was available to satisfy a request."""

    @classmethod
    def eventclass_get_csv_type(cls) -> str:
        """
        Get the csv type of the event.

        :return: the csv type
        """
        return "understock"

    @classmethod
    def eventclass_get_event_desc(cls) -> str | None:
        """
        Get the event description.

        :return: the event description, if any
        """
        return ("there was not enough part in the "
                "warehouse to satisfy a warehouse_demand request.")
