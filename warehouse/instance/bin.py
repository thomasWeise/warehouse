"""
A class for identifying a bin.

>>> with context():
...     m1 = Material(None, "Shoe")
...     m2 = Material(1, "Hat")
...     m3 = Material(2, "Skirt")
...     m4 = Material(None, "T-Shirt")
...     b1 = Bin(None, "shelf", m1)
...     b2 = Bin(1, "cupboard")
...     b3 = Bin(None, "wardrobe", 3)
...     b4 = Bin(None, "drawer", "Skirt")
...     b5 = Bin(4, "shed", None)

>>> repr(b1)
"Bin(key=0, name='shelf', material=Material(key=0, name='Shoe'))"
>>> repr(b2)
"Bin(key=1, name='cupboard', material=None)"
>>> repr(b3)
"Bin(key=2, name='wardrobe', material=Material(key=3, name='T-Shirt'))"
>>> repr(b4)
"Bin(key=3, name='drawer', material=Material(key=2, name='Skirt'))"
>>> repr(b5)
"Bin(key=4, name='shed', material=None)"

>>> csv_1 = list(Bin.to_csv((b1, b2, b3, b4, b5)))
>>> for row in csv_1[:-3]:
...     print(row)
key;name;material
0;shelf;Shoe
1;cupboard
2;wardrobe;T-Shirt
3;drawer;Skirt
4;shed
# key: the unique key of the element within its type
# name: the unique name of the element (unique over all elements of all types)
# material: the material to be stored in the bin; empty for random bins

>>> with context():
...     m1 = Material(None, "Shoe")
...     m2 = Material(1, "Hat")
...     m3 = Material(2, "Skirt")
...     m4 = Material(None, "T-Shirt")
...     for xbin in Bin.from_csv(csv_1):
...         print(repr(xbin))
Bin(key=0, name='shelf', material=Material(key=0, name='Shoe'))
Bin(key=1, name='cupboard', material=None)
Bin(key=2, name='wardrobe', material=Material(key=3, name='T-Shirt'))
Bin(key=3, name='drawer', material=Material(key=2, name='Skirt'))
Bin(key=4, name='shed', material=None)
"""

from dataclasses import dataclass
from typing import Final, Iterable, TypeVar, cast

from pycommons.io.csv import (
    csv_column_or_none,
    csv_scope,
    csv_str_or_none,
    csv_val_or_none,
)
from pycommons.types import type_error

from warehouse.instance.element import CsvReader as CsvReaderBase
from warehouse.instance.element import CsvWriter as CsvWriterBase
from warehouse.instance.element import Element, context, prepare_to_csv
from warehouse.instance.material import Material

#: the CSV material column
COLUMN_MATERIAL: Final[str] = "material"


@dataclass(frozen=True, init=False, order=False, eq=False)
class Bin(Element):
    """A class for describing bins."""

    #: the material bins that can only contain one material (fixed
    #: bins), `None` for random bins that can contain any material
    material: Material | None

    def __init__(self, key: int | None, name: str,
                 material: Material | str | int | None = None) -> None:
        """
        Create a new bin.

        :param key: the bin key
        :param name: the bin name
        :param material: the material or material name
        """
        with context() as ctx:
            super().__init__(key=key, name=name)
            if material is not None:
                if isinstance(material, str | int):
                    material = ctx.resolve(Material, material)
                if not isinstance(material, Material):
                    raise type_error(material, "material", (
                        str, Material, type(None)))
        object.__setattr__(self, "material", material)

    @classmethod
    def to_csv(cls, data: Iterable["Bin"]) -> Iterable[str]:   # type: ignore
        """
        Convert an iterable of the object to a CSV stream.

        :param data: the data
        :return: the stream
        """
        return CsvWriter[Bin].write(  # type: ignore
            data=prepare_to_csv(data))  # type: ignore

    @classmethod
    def from_csv(cls, rows: Iterable[str]) -> Iterable["Bin"]:
        """
        Get the data from CSV.

        :param rows: the rows
        :return: the sequence of objects
        """
        with context():
            yield from CsvReader[Bin].read(rows=rows, clazz=cls)


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
            columns, COLUMN_MATERIAL, True)

    def parse_row(self, data: list[str]) -> T:
        """
        Parse a data row.

        :param data: the data row
        :return: the instance
        """
        return self.clazz(key=csv_val_or_none(
            data, self.col_key, int), name=data[self.col_name],
            material=csv_str_or_none(data, self.col_material_key))


class CsvWriter(CsvWriterBase[T]):
    """Write the data to a csv file."""

    def __init__(self, data: Iterable[T], scope: str | None = None) -> None:
        """
        Initialize the CSV writer.

        :param data: the data
        :param scope: the scope
        """
        super().__init__(data, scope)

        needs_material: bool = False
        for xbin in data:
            if xbin.material is not None:
                needs_material = True
                break

        #: the key column
        self.col_material: Final[str | None] = csv_scope(
            scope, COLUMN_MATERIAL) if needs_material else None

    def get_column_titles(self) -> Iterable[str]:
        """
        Get the column titles.

        :returns: the column titles
        """
        yield from super().get_column_titles()
        if self.col_material is not None:
            yield self.col_material

    def get_row(self, data: T) -> Iterable[str]:
        """
        Render a single named object  CSV row.

        :param data: the named object
        :returns: the row iterator
        """
        yield from super().get_row(data)
        if self.col_material is not None:
            yield "" if data.material is None else data.material.name

    def get_footer_comments(self) -> Iterable[str]:
        """
        Get the footer comments.

        :return: the footer comments
        """
        yield from super().get_footer_comments()
        if self.col_material is not None:
            yield (f"{self.col_material}: the material to be stored in "
                   "the bin; empty for random bins")
