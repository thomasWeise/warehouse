"""
A class for identifying a material.

Each Instance of :class:`~Material` corresponds to some material that we need
for production and store in the warehouse.
Each material has an associated bin type (:attr:`~Material.bin_type`) into
which it can be stored.

>>> from warehouse.instance.element import context

>>> with context():
...     b1 = BinType(None, "random_small", 10)
...     b2 = BinType(None, "random_large", 10)
...     b3 = BinType(None, "shoe_bin", 5)
...     m1 = Material(None, "Shoe", b3)
...     m2 = Material(1, "Hat", "random_small")
...     m3 = Material(2, "Skirt", "random_large")

>>> str(m1)
'M0'
>>> str(m2)
'M1'
>>> str(m3)
'M2'

>>> repr(m1)
"Material(key=0, name='Shoe', bin_type=BinType(key=2, name='shoe_bin', \
amount=5))"
>>> repr(m2)
"Material(key=1, name='Hat', bin_type=BinType(key=0, name='random_small', \
amount=10))"
>>> repr(m3)
"Material(key=2, name='Skirt', bin_type=BinType(key=1, name='random_large', \
amount=10))"

>>> csv1 = list(Material.to_csv((m1, m2, m3)))
>>> for row in csv1:
...     if not str.startswith(row, "#"):
...         print(row)
key;name;bin_type
0;Shoe;shoe_bin
1;Hat;random_small
2;Skirt;random_large

>>> with context():
...     _ = BinType(None, "random_small", 10)
...     _ = BinType(None, "random_large", 10)
...     _ = BinType(None, "shoe_bin", 5)
...     for mat in Material.from_csv(csv1):
...         print(repr(mat))
Material(key=0, name='Shoe', bin_type=BinType(key=2, name='shoe_bin', \
amount=5))
Material(key=1, name='Hat', bin_type=BinType(key=0, name='random_small', \
amount=10))
Material(key=2, name='Skirt', bin_type=BinType(key=1, name='random_large', \
amount=10))
"""

from dataclasses import dataclass
from typing import Final, Iterable, TypeVar, cast

from pycommons.io.csv import (
    csv_column,
    csv_scope,
    csv_val_or_none,
)

from warehouse.instance.bin_type import BinType
from warehouse.instance.element import CsvReader as CsvReaderBase
from warehouse.instance.element import CsvWriter as CsvWriterBase
from warehouse.instance.element import Element, context, prepare_to_csv

#: the CSV material column
COLUMN_BIN_TYPE: Final[str] = "bin_type"


@dataclass(frozen=True, init=False, order=False, eq=False)
class Material(Element):
    """A class for identifying a material."""

    #: the amount of bins of this type
    bin_type: BinType

    def __init__(self, key: int | None, name: str,
                 bin_type: BinType | int | str) -> None:
        """
        Create a new bin.

        :param key: the bin key
        :param name: the bin name
        :param bin-tyoe: the bin type to use
        """
        super().__init__(key, name)
        with context() as ctx:
            object.__setattr__(self, "bin_type", bin_type if isinstance(
                bin_type, BinType) else ctx.resolve(BinType, bin_type))

    def __eq__(self, other) -> bool:
        """
        Compare two materials for "equality".

        :param other: the other element
        :return: `True` if this element is equal, `False` otherwise
        """
        return (self.__class__ is other.__class__) and (
            self.key == other.key) and (self.name == other.name) and (
            self.bin_type == other.bin_type)

    def __ne__(self, other) -> bool:
        """
        Compare two materials for "not equal".

        :param other: the other element
        :return: `True` if this element is not equal, `False` otherwise
        """
        return (self.__class__ is not other.__class__) or (
            self.key != other.key) or (self.name != other.name) or (
            self.bin_type != other.bin_type)

    def __hash__(self) -> int:
        """
        Get the hash code of the bin type.

        :return: the hash code
        """
        return self._hash

    @classmethod
    def to_csv(cls,  # type: ignore
               data: Iterable["Material"]) -> Iterable[str]:  # type: ignore
        """
        Convert an iterable of the object to a CSV stream.

        :param data: the data
        :return: the stream
        """
        return CsvWriter[Material].write(  # type: ignore
            data=prepare_to_csv(data))  # type: ignore

    @classmethod
    def from_csv(cls, rows: Iterable[str]) -> Iterable["Material"]:
        """
        Get the data from CSV.

        :param rows: the rows
        :return: the sequence of objects
        """
        with context():
            yield from CsvReader[Material].read(rows=rows, clazz=cls)


#: the type variable for data to be written to CSV or to be read from CSV
T = TypeVar("T", bound="Material")


class CsvReader(CsvReaderBase[T]):
    """A CsvReader that reads named objects from a CSV file."""

    def __init__(self, columns: dict[str, int],
                 clazz: type[T] = cast("type[T]", Material)):
        """
        Initialize.

        :param columns: the named object columns
        """
        super().__init__(columns, clazz)
        #: the bin type key
        self.col_bin_type_key: Final[int] = csv_column(
            columns, COLUMN_BIN_TYPE, True)

    def parse_row(self, data: list[str]) -> T:
        """
        Parse a data row.

        :param data: the data row
        :return: the instance
        """
        return self.clazz(key=csv_val_or_none(
            data, self.col_key, int), name=data[self.col_name],
            bin_type=data[self.col_bin_type_key])


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
               "material can be stored")
