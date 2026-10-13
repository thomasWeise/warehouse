"""
A class for identifying a bin type.

Each bin in our warehouse has a type.
Usually, there are some part-specific bins.
Additionally, there are small and large random bins that can house different
types of part.
Each bin type has an associated amount of bins (of that type).
The :attr:`~BinType.amount` must be a positive integer number.

>>> with context():
...     b1 = BinType(None, "shelf", 10, True)
...     b2 = BinType(1, "cupboard", 7, False)
...     b3 = BinType(None, "wardrobe", 33, True)
...     b4 = BinType(None, "drawer", 34, True)
...     b5 = BinType(4, "shed", 77, False)

>>> repr(b1)
"BinType(key=0, name='shelf', amount=10, is_random=True)"
>>> repr(b2)
"BinType(key=1, name='cupboard', amount=7, is_random=False)"
>>> repr(b3)
"BinType(key=2, name='wardrobe', amount=33, is_random=True)"
>>> repr(b4)
"BinType(key=3, name='drawer', amount=34, is_random=True)"
>>> repr(b5)
"BinType(key=4, name='shed', amount=77, is_random=False)"

>>> csv_1 = list(BinType.to_csv((b1, b2, b3, b4, b5)))
>>> for row in csv_1:
...     if not str.startswith(row, "#"):
...         print(row)
key;name;amount;is_random
0;shelf;10;T
1;cupboard;7;F
2;wardrobe;33;T
3;drawer;34;T
4;shed;77;F

>>> with context():
...     for xbin in BinType.from_csv(csv_1):
...         print(repr(xbin))
BinType(key=0, name='shelf', amount=10, is_random=True)
BinType(key=1, name='cupboard', amount=7, is_random=False)
BinType(key=2, name='wardrobe', amount=33, is_random=True)
BinType(key=3, name='drawer', amount=34, is_random=True)
BinType(key=4, name='shed', amount=77, is_random=False)
"""

from dataclasses import dataclass
from typing import Final, Iterable, TypeVar, cast

from pycommons.io.csv import csv_column, csv_scope, csv_val_or_none
from pycommons.strings.string_conv import bool_to_str, str_to_bool
from pycommons.types import check_int_range, type_error

from warehouse.instance.element import CsvReader as CsvReaderBase
from warehouse.instance.element import CsvWriter as CsvWriterBase
from warehouse.instance.element import Element, context, prepare_to_csv

#: the CSV amount column, which stores the :attr:`~BinType.amount` values.
COLUMN_AMOUNT: Final[str] = "amount"

#: the CSV amount column, which stores the :attr:`~BinType.is_random` values.
COLUMN_IS_RANDOM: Final[str] = "is_random"


@dataclass(frozen=True, init=False, order=False, eq=False)
class BinType(Element):  # noqa: PLW1641
    """A class for describing bins."""

    #: the amount of bins of this type that are available
    amount: int
    #: is this a random bin type?
    is_random: bool

    def __init__(self, key: int | None, name: str,
                 amount: int = 1,
                 is_random: bool = False) -> None:
        """
        Create a new bin.

        :param key: the bin key
        :param name: the bin name
        :param amount: the number of bins of this type
        :param is_random: is this a random bin?
        """
        super().__init__(key, name)
        if not isinstance(is_random, bool):
            raise type_error(is_random, "is_random", bool)
        object.__setattr__(self, "amount", check_int_range(
            amount, "amount", 1, 1_000_000_000))
        object.__setattr__(self, "is_random", is_random)

    def __hash__(self) -> int:
        """
        Get the hash code of the bin type.

        :return: the hash code
        """
        return self._hash

    def __eq__(self, other) -> bool:
        """
        Compare two bin types for "equality".

        :param other: the other element
        :return: `True` if this element is equal, `False` otherwise
        """
        return (self.__class__ is other.__class__) and (
            self.key == other.key) and (self.name == other.name) and (
            self.amount == other.amount)

    def __ne__(self, other) -> bool:
        """
        Compare two bin types for "not equal".

        :param other: the other element
        :return: `True` if this element is not equal, `False` otherwise
        """
        return (self.__class__ is not other.__class__) or (
            self.key != other.key) or (self.name != other.name) or (
            self.amount != other.amount)

    @classmethod
    def to_csv(cls, data: Iterable[  # type: ignore
            "BinType"]) -> Iterable[str]:  # type: ignore
        """
        Convert an iterable of the object to a CSV stream.

        :param data: the data
        :return: the stream
        """
        return CsvWriter[BinType].write(  # type: ignore
            data=prepare_to_csv(data))  # type: ignore

    @classmethod
    def from_csv(cls, rows: Iterable[str]) -> Iterable["BinType"]:
        """
        Get the data from CSV.

        :param rows: the rows
        :return: the sequence of objects
        """
        with context():
            yield from CsvReader[BinType].read(rows=rows, clazz=cls)


#: the type variable for data to be written to CSV or to be read from CSV
T = TypeVar("T", bound="BinType")


class CsvReader(CsvReaderBase[T]):
    """A CsvReader that reads named objects from a CSV file."""

    def __init__(self, columns: dict[str, int],
                 clazz: type[T] = cast("type[T]", BinType)):
        """
        Initialize.

        :param columns: the named object columns
        """
        super().__init__(columns, clazz)
        #: the amount key
        self.col_amount_key: Final[int] = csv_column(
            columns, COLUMN_AMOUNT, True)
        #: the is-random column
        self.col_is_random_key: Final[int] = csv_column(
            columns, COLUMN_IS_RANDOM, True)

    def parse_row(self, data: list[str]) -> T:
        """
        Parse a data row.

        :param data: the data row
        :return: the instance
        """
        return self.clazz(key=csv_val_or_none(
            data, self.col_key, int), name=data[self.col_name],
            amount=int(data[self.col_amount_key]),
            is_random=str_to_bool(data[self.col_is_random_key]))


class CsvWriter(CsvWriterBase[T]):
    """Write the data to a csv file."""

    def __init__(self, data: Iterable[T], scope: str | None = None) -> None:
        """
        Initialize the CSV writer.

        :param data: the data
        :param scope: the scope
        """
        super().__init__(data, scope)
        #: the amount column
        self.col_amount: Final[str] = csv_scope(scope, COLUMN_AMOUNT)
        #: the is-random column
        self.col_is_random: Final[str] = csv_scope(scope, COLUMN_IS_RANDOM)

    def get_column_titles(self) -> Iterable[str]:
        """
        Get the column titles.

        :returns: the column titles
        """
        yield from super().get_column_titles()
        yield self.col_amount
        yield self.col_is_random

    def get_row(self, data: T) -> Iterable[str]:
        """
        Render a single named object  CSV row.

        :param data: the named object
        :returns: the row iterator
        """
        yield from super().get_row(data)
        yield str(data.amount)
        yield bool_to_str(data.is_random)

    def get_footer_comments(self) -> Iterable[str]:
        """
        Get the footer comments.

        :return: the footer comments
        """
        yield from super().get_footer_comments()
        yield f"{self.col_amount}: the number of bins of this type"
        yield (f"{self.col_is_random}: is this a random bin type, i.e., a bin"
               "type capable of holding multiple different parts? If yes,"
               f"the value is {bool_to_str(True)!r}, otherwise, it is"
               f"{bool_to_str(False)!r}.")
