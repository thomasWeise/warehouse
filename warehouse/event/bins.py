"""
Events regarding the storage and retrieval of part to and from bins.

>>> from warehouse.instance.bin_type import BinType
>>> with context():
...     BinType(None, "random_small", 1000, True)
...     BinType(None, "random_large", 500, True)
...     BinType(None, "hat_bins", 30, False)
...     Part(None, "hat", "hat_bins")
...     Part(None, "shoe", "random_small")
...     Part(None, "trousers", "random_large")
...     ev01 = BinIn.create(1500000000000, 0, "hat", 10, "hat_bins")
...     ev02 = BinIn.create(1700000000000, 0, "shoe", 15, "random_small")
...     ev03 = BinIn.create(1800000000000, 0, "trousers", 7)
...     ev04 = BinOut.create(1900000000000, 0, "hat", 9, "hat_bins")
...     ev05 = BinOut.create(2000000000000, 0, "shoe", 8, "random_small")
...     ev06 = BinOut.create(2100000000000, 0, "trousers", 3)
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
BinType(key=0, name='random_small', amount=1000, is_random=True)
BinType(key=1, name='random_large', amount=500, is_random=True)
BinType(key=2, name='hat_bins', amount=30, is_random=False)
Part(key=0, name='hat', bin_type=BinType(key=2, name='hat_bins', \
amount=30, is_random=False))
Part(key=1, name='shoe', bin_type=BinType(key=0, name='random_small', \
amount=1000, is_random=True))
Part(key=2, name='trousers', bin_type=BinType(key=1, \
name='random_large', amount=500, is_random=True))
BinIn(time=1500000000000, priority=0, part=Part(key=0, name='hat', \
bin_type=BinType(key=2, name='hat_bins', amount=30, is_random=False)), \
amount=10)
BinIn(time=1700000000000, priority=0, part=Part(key=1, name='shoe', \
bin_type=BinType(key=0, name='random_small', amount=1000, is_random=True)), \
amount=15)
BinIn(time=1800000000000, priority=0, part=Part(key=2, name='trousers', \
bin_type=BinType(key=1, name='random_large', amount=500, is_random=True)), \
amount=7)
BinOut(time=1900000000000, priority=0, part=Part(key=0, name='hat', \
bin_type=BinType(key=2, name='hat_bins', amount=30, is_random=False)), \
amount=9)
BinOut(time=2000000000000, priority=0, part=Part(key=1, name='shoe', \
bin_type=BinType(key=0, name='random_small', amount=1000, is_random=True)), \
amount=8)
BinOut(time=2100000000000, priority=0, part=Part(key=2, name='trousers', \
bin_type=BinType(key=1, name='random_large', amount=500, is_random=True)), \
amount=3)
<BLANKLINE>
===================
<BLANKLINE>
time;type;part;amount;bin_type;rule
2017-07-14 10:40;bin_in;hat;10;hat_bins
2023-11-15 06:13:20;bin_in;shoe;15;random_small
2027-01-15 16:00;bin_in;trousers;7;random_large
2030-03-18 01:46:40;bin_out;hat;9;hat_bins
2033-05-18 11:33:20;bin_out;shoe;8;random_small
2036-07-18 21:20;bin_out;trousers;3;random_large
<BLANKLINE>
===================
<BLANKLINE>
BinIn(time=1500000000000, priority=0, part=Part(key=0, name='hat', \
bin_type=BinType(key=2, name='hat_bins', amount=30, is_random=False)), \
amount=10)
BinIn(time=1700000000000, priority=0, part=Part(key=1, name='shoe', \
bin_type=BinType(key=0, name='random_small', amount=1000, is_random=True)), \
amount=15)
BinIn(time=1800000000000, priority=0, part=Part(key=2, name='trousers', \
bin_type=BinType(key=1, name='random_large', amount=500, is_random=True)), \
amount=7)
BinOut(time=1900000000000, priority=0, part=Part(key=0, name='hat', \
bin_type=BinType(key=2, name='hat_bins', amount=30, is_random=False)), \
amount=9)
BinOut(time=2000000000000, priority=0, part=Part(key=1, name='shoe', \
bin_type=BinType(key=0, name='random_small', amount=1000, is_random=True)), \
amount=8)
BinOut(time=2100000000000, priority=0, part=Part(key=2, name='trousers', \
bin_type=BinType(key=1, name='random_large', amount=500, is_random=True)), \
amount=3)

>>> hash(ev06)
-2497297457874468673
"""


from warehouse.event.storage import (
    COLUMN_AMOUNT,
    StorageEvent,
    check_to_amount,
)
from warehouse.instance.bin_type import COLUMN_BIN_TYPE, BinType
from warehouse.instance.element import context
from warehouse.instance.part import COLUMN_PART, Part


class BinEvent(StorageEvent):  # noqa: PLW1641
    """An amount of part has changed places."""

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

    @classmethod
    def eventclass_get_col_desc(cls, col: str) -> str | None:
        """
        Get the column description.

        :param col: the column
        :return: the event description, if any
        """
        if col == COLUMN_BIN_TYPE:
            return ("the type of bin into which is part stored in or "
                    "taken out of")
        return super().eventclass_get_col_desc(col)

    def event_get_csv_value(self, column: str) -> str:
        """
        Get a specific csv value.

        :param column: the csv column
        :return: the value
        """
        if column == COLUMN_BIN_TYPE:
            return self.part.bin_type.name
        return super().event_get_csv_value(column)

    @classmethod
    def eventclass_get_csv_columns(cls) -> tuple[str, ...]:
        """
        Get the CSV columns of the event.

        :return: the csv columns
        """
        return COLUMN_PART, COLUMN_AMOUNT, COLUMN_BIN_TYPE

    @classmethod
    def create(  # type: ignore  # pylint: disable=W0221
            cls, time: int, priority: int,
            part: int | str | Part, amount: int | str,
            bin_type: int | str | BinType | None = None) -> "BinEvent":
        """
        Create the storage event.

        :param time: the time
        :param priority: the priority
        :param part: the part to use
        :param amount: the amount of the part to use
        :param bin_type: the optional bin type
        :return: the bin event
        """
        need_bin: bool = (bin_type is not None) and (
            bin_type.__class__ is not BinType)
        need_part: bool = part.__class__ is not Part
        if need_part or need_bin:
            with context() as ctx:
                if need_part:
                    part = ctx.resolve(Part, part)  # type: ignore
                if need_bin:
                    bin_type = ctx.resolve(BinType, bin_type)  # type: ignore

        rv = cls(time, priority, part,  # type: ignore
                 check_to_amount(amount))  # type: ignore
        if (bin_type is not None) and (rv.part.bin_type is not bin_type):
            raise ValueError(f"Expected bin type {bin_type!r} for {rv!r}.")
        return rv


class BinIn(BinEvent):
    """Store part in a bin."""

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
        return ("a certain amount of a part is stored in a certain type "
                "of bins; the amount of part and the amount of bins used "
                "are the same, as part always comes in units that are "
                "multiples of bin sizes.")


class BinOut(BinEvent):
    """Retrieve part from a bin."""

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
        return ("a certain amount of a part is retrieved from a certain "
                "type of bins; the amount of part and the amount of bins "
                "used are the same, as part always comes in units that "
                "are multiples of bin sizes.")
