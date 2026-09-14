"""
A warehouse setup.

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
...     scenario = Scenario((m1, m2, m3, m4), (b1, b2, b3, b4, b5))

>>> scenario.n_materials
4
>>> scenario.materials
(Material(key=0, name='Shoe'), Material(key=1, name='Hat'), \
Material(key=2, name='Skirt'), Material(key=3, name='T-Shirt'))
>>> scenario.n_bins
5
>>> scenario.bins
(Bin(key=0, name='shelf', material=Material(key=0, name='Shoe')), \
Bin(key=1, name='cupboard', material=None), \
Bin(key=2, name='wardrobe', material=Material(key=3, name='T-Shirt')), \
Bin(key=3, name='drawer', material=Material(key=2, name='Skirt')), \
Bin(key=4, name='shed', material=None))

>>> from pycommons.io.temp import temp_dir
>>> with temp_dir() as td:
...     scenario.to_directory(td)
...     scenario_2 = Scenario.from_directory(td)

>>> scenario_2.n_materials
4
>>> scenario_2.materials
(Material(key=0, name='Shoe'), Material(key=1, name='Hat'), \
Material(key=2, name='Skirt'), Material(key=3, name='T-Shirt'))
>>> scenario_2.n_bins
5
>>> scenario_2.bins
(Bin(key=0, name='shelf', material=Material(key=0, name='Shoe')), \
Bin(key=1, name='cupboard', material=None), \
Bin(key=2, name='wardrobe', material=Material(key=3, name='T-Shirt')), \
Bin(key=3, name='drawer', material=Material(key=2, name='Skirt')), \
Bin(key=4, name='shed', material=None))

>>> scenario_2.resolve(Bin, "shed")
Bin(key=4, name='shed', material=None)
>>> scenario_2.resolve(Bin, 3)
Bin(key=3, name='drawer', material=Material(key=2, name='Skirt'))

>>> scenario_2.resolve(Material, "Shoe")
Material(key=0, name='Shoe')

>>> scenario_2.resolve(Material, 2)
Material(key=2, name='Skirt')
"""

from dataclasses import dataclass
from typing import Final, Iterable, TypeVar

from pycommons.io.path import Path, directory_path
from pycommons.types import type_error

from warehouse.instance.bin import Bin
from warehouse.instance.element import Element, ElementResolver, context
from warehouse.instance.material import Material

#: the materials file
FILE_MATERIALS: Final[str] = "materials.txt"
#: the bins file
FILE_BINS: Final[str] = "bins.txt"

#: the type variable for data to be written to CSV or to be read from CSV
T = TypeVar("T", bound="Element")


@dataclass(frozen=True, init=False, order=False, eq=False)
class Scenario(ElementResolver):
    """A warehousing scenario."""

    #: the number of materials
    n_materials: int
    #: the number of bins
    n_bins: int
    #: the material types available for the warehouse
    materials: tuple[Material, ...]
    #: the bin configuration of the warehouse
    bins: tuple[Bin, ...]

    def __init__(self, materials: Iterable[Material],
                 bins: Iterable[Bin]) -> None:
        """
        Create an instance of the warehousing scenario.

        :param materials: the materials
        :param bins: the bins
        """
        if not isinstance(materials, Iterable):
            raise type_error(materials, "materials", Iterable)
        if not isinstance(bins, Iterable):
            raise type_error(bins, "bins", Iterable)

        material_lst: Final[list[Material]] = []
        bin_lst: Final[list[Bin]] = []
        names: Final[dict[str, Element]] = {}

        for i, material in enumerate(materials):
            if not isinstance(material, Material):
                raise type_error(material, f"materials[{i}]", Material)
            name = material.name
            if name in names:
                raise ValueError(f"Name of {material!r} already in use.")
            names[material.name] = material
            material_lst.append(material)

        n_materials: Final[int] = list.__len__(material_lst)
        if n_materials <= 0:
            raise ValueError("No materials specified.")

        for i, xbin in enumerate(bins):
            if not isinstance(xbin, Bin):
                raise type_error(xbin, f"bins[{i}]", Bin)
            name = xbin.name
            if name in names:
                raise ValueError(f"Name of {xbin!r} already in use.")
            names[xbin.name] = xbin
            bin_lst.append(xbin)

        n_bins: Final[int] = list.__len__(bin_lst)
        if n_bins <= 0:
            raise ValueError("No bins specified.")

        material_lst.sort()
        for i, material in enumerate(material_lst):
            if i != material.key:
                raise ValueError(f"Inconsistent key for {material!r}.")
        bin_lst.sort()
        for i, xbin in enumerate(bin_lst):
            if i != xbin.key:
                raise ValueError(f"Inconsistent key for {xbin!r}.")

        object.__setattr__(self, "n_materials", n_materials)
        object.__setattr__(self, "n_bins", n_bins)
        object.__setattr__(self, "materials", tuple(material_lst))
        object.__setattr__(self, "bins", tuple(bin_lst))
        object.__setattr__(self, "_names", names)

    def resolve(self, cls: type[T], name_or_key: str | int) -> T:
        """
        Get the element of the given name and type.

        :param cls: the element class
        :param name_or_key: the element name or key

        :return: the element
        """
        if isinstance(name_or_key, int):
            if cls is Bin:
                return self.bins[name_or_key]  # type: ignore
            if cls is Material:
                return self.materials[name_or_key]  # type: ignore
            raise TypeError(f"Unsupported type {cls} for {name_or_key!r}.")
        res = self._names[  # type: ignore  # noqa  # pylint: disable=E1101
            str.strip(name_or_key)]
        if res.__class__ is not cls:
            raise TypeError(f"Excepted instance of {cls} for {name_or_key!r},"
                            f" but got {res!r}.")
        return res

    @classmethod
    def from_directory(cls, directory: str) -> "Scenario":
        """
        Load a scenario from a directory.

        :param directory: the directory
        :return: the scenario
        """
        source: Final[Path] = directory_path(directory)

        with context():
            materials: Final[list[Material]] = []
            with source.resolve_inside(
                    FILE_MATERIALS).open_for_read() as stream:
                materials.extend(Material.from_csv(stream))  # type: ignore

            bins: Final[list[Bin]] = []
            with source.resolve_inside(
                    FILE_BINS).open_for_read() as stream:
                bins.extend(Bin.from_csv(stream))  # type: ignore

            return Scenario(materials=materials, bins=bins)

    def to_directory(self, directory: str) -> None:
        """
        Store a scenario into a directory.

        :param directory: the directory
        """
        dest: Final[Path] = Path(directory)
        dest.ensure_dir_exists()

        with dest.resolve_inside(FILE_MATERIALS).open_for_write() as stream:
            w = stream.write
            for row in Material.to_csv(self.materials):
                w(row)
                w("\n")

        with dest.resolve_inside(FILE_BINS).open_for_write() as stream:
            w = stream.write
            for row in Bin.to_csv(self.bins):
                w(row)
                w("\n")
