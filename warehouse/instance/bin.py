"""
A class for identifying a bin.

>>> m1 = Bin(1, "test")
>>> str(m1)
'B1'

>>> repr(m1)
"Bin(key=1, name='test', material_key=None)"

>>> m2 = Bin(2)
>>> str(m2)
'B2'

>>> repr(m2)
'Bin(key=2, name=None, material_key=None)'

>>> csv1 = list(Bin.to_csv((m1, m2)))
>>> for txt in csv1[:-3]:
...     print(txt)
key;name
1;test
2
# key: the unique key identifying the object within its type
# name: the name of the object


>>> for obj in Bin.from_csv(csv1):
...     print(repr(obj))
Bin(key=1, name='test', material_key=None)
Bin(key=2, name=None, material_key=None)

>>> m3 = Bin(3)
>>> str(m3)
'B3'

>>> csv2 = list(Bin.to_csv((m3, m2)))
>>> for txt in csv2[:-3]:
...     print(txt)
key
2
3
# key: the unique key identifying the object within its type

>>> for obj in Bin.from_csv(csv2):
...     print(repr(obj))
Bin(key=2, name=None, material_key=None)
Bin(key=3, name=None, material_key=None)

>>> m4 = Bin(4, material_key=13)
>>> str(m4)
'B4'
>>> repr(m4)
'Bin(key=4, name=None, material_key=13)'

>>> csv3 = list(Bin.to_csv((m3, m2, m4)))
>>> for txt in csv3[:-3]:
...     print(txt)
key;material
2
3
4;13
# key: the unique key identifying the object within its type
# material: the material to be stored in the bin; empty for random bins

>>> for obj in Bin.from_csv(csv3):
...     print(repr(obj))
Bin(key=2, name=None, material_key=None)
Bin(key=3, name=None, material_key=None)
Bin(key=4, name=None, material_key=13)


>>> m5 = Bin(5, name="q", material_key=75)
>>> str(m5)
'B5'
>>> repr(m5)
"Bin(key=5, name='q', material_key=75)"


>>> csv4 = list(Bin.to_csv((m1, m5, m3, m2, m4)))
>>> for txt in csv4[:-3]:
...     print(txt)
key;name;material
1;test
2
3
4;;13
5;q;75
# key: the unique key identifying the object within its type
# name: the name of the object
# material: the material to be stored in the bin; empty for random bins

>>> for obj in Bin.from_csv(csv4):
...     print(repr(obj))
Bin(key=1, name='test', material_key=None)
Bin(key=2, name=None, material_key=None)
Bin(key=3, name=None, material_key=None)
Bin(key=4, name=None, material_key=13)
Bin(key=5, name='q', material_key=75)
"""

from dataclasses import dataclass
from typing import Final, Iterable, TypeVar, cast

from pycommons.io.csv import (
    csv_column_or_none,
    csv_scope,
    csv_str_or_none,
    csv_val_or_none,
)
from pycommons.types import check_int_range, type_error

from warehouse.instance.named import CsvReader as CsvReaderBase
from warehouse.instance.named import CsvWriter as CsvWriterBase
from warehouse.instance.named import Named, _prepare_to_csv

#: the CSV material column
KEY_MATERIAL: Final[str] = "material"


@dataclass(frozen=True, init=False, order=False, eq=False)
class Bin(Named):
    """A class for describing bins."""

    #: the material key for bins that can only contain one material (fixed
    #: bins), `None` for random bins that can contain any material
    material_key: int | None

    def __init__(self, key: int, name: str | None = None,
                 material_key: int | None = None) -> None:
        """
        Create a new bin.

        :param key: the bin key
        :param name: the bin name
        :param material_key: the material key
        """
        super().__init__(key=key, name=name)
        object.__setattr__(
            self, "material_key", None if material_key is None
            else check_int_range(material_key, "material_key"))

    @classmethod
    def to_csv(cls, data: Iterable["Bin"]) -> Iterable[str]:   # type: ignore
        """
        Convert an iterable of the object to a CSV stream.

        :param data: the data
        :return: the stream
        """
        return CsvWriter[Bin].write(  # type: ignore
            data=_prepare_to_csv(data))  # type: ignore

    @classmethod
    def from_csv(cls, rows: Iterable[str]) -> Iterable["Bin"]:
        """
        Get the data from CSV.

        :param rows: the rows
        :return: the sequence of objects
        """
        return CsvReader[Bin].read(rows=rows, clazz=cls)


#: the type variable for data to be written to CSV or to be read from CSV
T = TypeVar("T", bound="Bin")


class CsvReader(CsvReaderBase[T]):
    """A CsvReader that reads named objects from a CSV file."""

    def __init__(self, columns: dict[str, int],
                 clazz: type[T] = cast("type[T]", Bin)):
        """
        Initialize.

        :param columns: the named object columns
        """
        super().__init__(columns, clazz)
        #: the material key
        self.col_material_key: Final[int | None] = csv_column_or_none(
            columns, KEY_MATERIAL, True)

    def parse_row(self, data: list[str]) -> T:
        """
        Parse a data row.

        :param data: the data row
        :return: the instance
        """
        return self.clazz(key=int(data[self.col_key]), name=csv_str_or_none(
            data, self.col_name), material_key=csv_val_or_none(
            data, self.col_material_key, int))


class CsvWriter(CsvWriterBase[T]):
    """Write the data to a csv file."""

    def __init__(self, data: Iterable[T], scope: str | None = None) -> None:
        """
        Initialize the CSV writer.

        :param data: the data
        :param scope: the scope
        """
        super().__init__(data, scope)

        needs_material_key: bool = False
        for i, xbin in enumerate(data):
            if not isinstance(xbin, Bin):
                raise type_error(xbin, f"data[{i}]", Bin)
            if xbin.material_key is not None:
                needs_material_key = True
                break

        #: the key column
        self.col_material_key: Final[str | None] = ((
            KEY_MATERIAL if scope is None else csv_scope(
                scope, KEY_MATERIAL)) if needs_material_key else None)

    def get_column_titles(self) -> Iterable[str]:
        """
        Get the column titles.

        :returns: the column titles
        """
        yield from super().get_column_titles()
        if self.col_material_key is not None:
            yield self.col_material_key

    def get_row(self, data: T) -> Iterable[str]:
        """
        Render a single named object  CSV row.

        :param data: the named object
        :returns: the row iterator
        """
        yield from super().get_row(data)
        if self.col_material_key is not None:
            yield "" if data.material_key is None else str(data.material_key)

    def get_footer_comments(self) -> Iterable[str]:
        """
        Get the footer comments.

        :return: the footer comments
        """
        yield from super().get_footer_comments()
        if self.col_material_key is not None:
            yield (f"{self.col_material_key}: the material to be stored in "
                   "the bin; empty for random bins")
