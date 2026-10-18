"""
A class for identifying a part.

Each Instance of :class:`~Part` corresponds to some part that we need
for production and store in the warehouse.
Each part has an associated bin type (:attr:`~Part.bin_type`) into
which it can be stored.

>>> from warehouse.instance.element import context

>>> with context():
...     b1 = BinType(None, "random_small", 10, True)
...     b2 = BinType(None, "random_large", 10, True)
...     b3 = BinType(None, "shoe_bin", 5)
...     m1 = Part(None, "Shoe", b3)
...     m2 = Part(1, "Hat", "random_small")
...     m3 = Part(2, "Skirt", "random_large")

>>> str(m1)
'Part0'
>>> str(m2)
'Part1'
>>> str(m3)
'Part2'

>>> repr(m1)
"Part(key=0, name='Shoe', bin_type=BinType(key=2, name='shoe_bin', \
amount=5, is_random=False))"
>>> repr(m2)
"Part(key=1, name='Hat', bin_type=BinType(key=0, name='random_small', \
amount=10, is_random=True))"
>>> repr(m3)
"Part(key=2, name='Skirt', bin_type=BinType(key=1, name='random_large', \
amount=10, is_random=True))"

>>> csv1 = list(Part.to_csv((m1, m2, m3)))
>>> for row in csv1:
...     if not str.startswith(row, "#"):
...         print(row)
key;name;bin_type
0;Shoe;shoe_bin
1;Hat;random_small
2;Skirt;random_large

>>> with context():
...     _ = BinType(None, "random_small", 10, True)
...     _ = BinType(None, "random_large", 10, True)
...     _ = BinType(None, "shoe_bin", 5)
...     for mat in Part.from_csv(csv1):
...         print(repr(mat))
Part(key=0, name='Shoe', bin_type=BinType(key=2, name='shoe_bin', \
amount=5, is_random=False))
Part(key=1, name='Hat', bin_type=BinType(key=0, name='random_small', \
amount=10, is_random=True))
Part(key=2, name='Skirt', bin_type=BinType(key=1, name='random_large', \
amount=10, is_random=True))
"""

from dataclasses import dataclass
from typing import Final, Iterable, TypeVar, cast

from pycommons.io.csv import (
    csv_column,
    csv_scope,
    csv_val_or_none,
)

from warehouse.instance.bin_type import COLUMN_BIN_TYPE, BinType
from warehouse.instance.element import CsvReader as CsvReaderBase
from warehouse.instance.element import CsvWriter as CsvWriterBase
from warehouse.instance.element import Element, context

#: the CSV column for parts
COLUMN_PART: Final[str] = "part"


@dataclass(frozen=True, init=False, order=False, eq=False)
class Part(Element):
    """A class for identifying a part type."""

    #: the bin type into which this part is stored
    bin_type: BinType

    def __init__(self, key: int | None, name: str,
                 bin_type: BinType | int | str) -> None:
        """
        Create a new part type.

        :param key: the part key
        :param name: the part name
        :param bin_type: the bin type to use
        """
        super().__init__(key, name)
        with context() as ctx:
            bin_type = ctx.resolve(BinType, bin_type)
        object.__setattr__(self, "bin_type", bin_type)

    def __eq__(self, other) -> bool:
        """
        Compare two parts for "equality".

        :param other: the other element
        :return: `True` if this element is equal, `False` otherwise
        """
        return (self.__class__ is other.__class__) and (
            self.key == other.key) and (self.name == other.name) and (
            self.bin_type == other.bin_type)

    def __ne__(self, other) -> bool:
        """
        Compare two parts for "not equal".

        :param other: the other element
        :return: `True` if this element is not equal, `False` otherwise
        """
        return (self.__class__ is not other.__class__) or (
            self.key != other.key) or (self.name != other.name) or (
            self.bin_type != other.bin_type)

    def __hash__(self) -> int:
        """
        Get the hash code of the part.

        :return: the hash code
        """
        return self._hash

    @classmethod
    def to_csv(cls,  # type: ignore
               data: Iterable["Part"]) -> Iterable[str]:  # type: ignore
        """
        Convert an iterable of the object to a CSV stream.

        :param data: the data
        :return: the stream
        """
        return CsvWriter[Part].write(data=data)

    @classmethod
    def from_csv(cls, rows: Iterable[str]) -> Iterable["Part"]:
        """
        Get the data from CSV.

        :param rows: the rows
        :return: the sequence of objects
        """
        with context():
            yield from CsvReader[Part].read(rows=rows, clazz=cls)


#: the type variable for data to be written to CSV or to be read from CSV
T = TypeVar("T", bound="Part")


class CsvReader(CsvReaderBase[T]):
    """A CsvReader that reads named objects from a CSV file."""

    def __init__(self, columns: dict[str, int],
                 clazz: type[T] = cast("type[T]", Part)):
        """
        Initialize.

        :param columns: the named object columns
        """
        super().__init__(columns, clazz)
        #: the bin type key
        self.col_bin_type: Final[int] = csv_column(
            columns, COLUMN_BIN_TYPE, True)

    def parse_row(self, data: list[str]) -> T:
        """
        Parse a data row.

        :param data: the data row
        :return: the instance
        """
        return self.clazz(key=csv_val_or_none(
            data, self.col_key, int), name=data[self.col_name],
            bin_type=data[self.col_bin_type])


class CsvWriter(CsvWriterBase[T]):
    """Write the data to a csv file."""

    def __init__(self, data: Iterable[T], scope: str | None = None) -> None:
        """
        Initialize the CSV writer.

        :param data: the data
        :param scope: the scope
        """
        super().__init__(data, scope)
        #: the bin type column
        self.col_bin_type: Final[str] = csv_scope(scope, COLUMN_BIN_TYPE)

    def get_column_titles(self) -> Iterable[str]:
        """
        Get the column titles.

        :returns: the column titles
        """
        yield from super().get_column_titles()
        yield self.col_bin_type

    def get_row(self, data: T) -> Iterable[str]:
        """
        Render a single named object CSV row.

        :param data: the named object
        :returns: the row iterator
        """
        yield from super().get_row(data)
        yield data.bin_type.name

    def get_footer_comments(self) -> Iterable[str]:
        """
        Get the footer comments.

        :return: the footer comments
        """
        yield from super().get_footer_comments()
        yield (f"{self.col_bin_type}: the type of bin into which this "
               "part can be stored")
