"""
A warehouse setup.

>>> mat_0 = Material(0, "sock")
>>> mat_1 = Material(1, "shoe")
>>> mat_2 = Material(2, "hat")
>>> mat_3 = Material(3, "t-shirt")

>>> bin_0 = Bin(0, "closet")
>>> bin_1 = Bin(1, "drawer_1", 2)
>>> bin_2 = Bin(2, "drawer_2", 3)
>>> bin_3 = Bin(3, "cupboard")
>>> bin_4 = Bin(4, "shed")

>>> scneario_1 = Scenario((mat_0, mat_2, mat_3, mat_1),
...                       (bin_0, bin_3, bin_1, bin_2, bin_4))
>>> scneario_1.n_bins
5
>>> scneario_1.n_materials
4
>>> scneario_1.bin_min_key
0
>>> scneario_1.bin_max_key
4
>>> scneario_1.get_material(1)
Material(key=1, name='shoe')
>>> scneario_1.get_bin(2)
Bin(key=2, name='drawer_2', material_key=3)

>>> from pycommons.io.temp import temp_dir
>>> with temp_dir() as td:
...     scneario_1.to_directory(td)
...     scenario_1b = Scenario.from_directory(td)

>>> scneario_1.bins == scenario_1b.bins
True
>>> scneario_1.materials == scenario_1b.materials
True

>>> scneario_2 = Scenario((mat_2, mat_3),
...                       (bin_1, bin_4))
>>> scneario_2.get_material(2)
Material(key=2, name='hat')
>>> scneario_2.get_bin(4)
Bin(key=4, name='shed', material_key=None)
>>> scneario_2.n_bins
2
>>> scneario_2.n_materials
2
>>> scneario_2.bin_min_key
1
>>> scneario_2.bin_max_key
4
>>> with temp_dir() as td:
...     scneario_2.to_directory(td)
...     scenario_2b = Scenario.from_directory(td)

>>> scneario_2.bins == scenario_2b.bins
True
>>> scneario_2.materials == scenario_2b.materials
True
"""

from dataclasses import dataclass
from typing import Callable, Final, Iterable

from pycommons.io.path import Path, directory_path
from pycommons.types import type_error

from warehouse.instance.bin import Bin
from warehouse.instance.material import Material

#: the materials file
FILE_MATERIALS: Final[str] = "materials.txt"
#: the bins file
FILE_BINS: Final[str] = "bins.txt"


@dataclass(frozen=True, init=False, order=False, eq=False)
class Scenario:
    """A warehousing scenario."""

    #: the number of materials
    n_materials: Final[int]
    #: the number of bins
    n_bins: Final[int]
    #: the smallest bin key
    bin_min_key: Final[int]
    #: the largest bin key
    bin_max_key: Final[int]

    #: the material types available for the warehouse
    materials: tuple[Material, ...]
    #: the bin configuration of the warehouse
    bins: tuple[Bin, ...]

    #: the material getter
    get_material: Callable[[int], Material]
    #: the bin getter
    get_bin: Callable[[int], Bin]

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
        names: Final[set[str]] = set()
        material_keys: Final[set[int]] = set()
        bin_keys: Final[set[int]] = set()

        for i, material in enumerate(materials):
            if not isinstance(material, Material):
                raise type_error(material, f"materials[{i}]", Material)
            name = material.name
            if name is not None:
                if name in names:
                    raise ValueError(
                        f"Duplicate name for materials[{i}]: {material!r}.")
                names.add(name)
            if material.key in material_keys:
                raise ValueError(
                    f"Duplicate key for materials[{i}]: {material!r}.")
            material_keys.add(material.key)
            material_lst.append(material)

        n_materials: Final[int] = list.__len__(material_lst)
        if n_materials <= 0:
            raise ValueError("No materials specified.")

        for i, xbin in enumerate(bins):
            if not isinstance(xbin, Bin):
                raise type_error(xbin, f"bins[{i}]", Bin)
            name = xbin.name
            if name is not None:
                if name in names:
                    raise ValueError(
                        f"Duplicate name for bins[{i}]: {xbin!r}.")
                names.add(name)
            if xbin.key in bin_keys:
                raise ValueError(
                    f"Duplicate key for bins[{i}]: {bin!r}.")
            xmat = xbin.material_key
            if (xmat is not None) and (xmat not in material_keys):
                raise ValueError(
                    f"Unknown material key for bins[{i}]: {xbin!r}.")

            bin_keys.add(xbin.key)
            bin_lst.append(xbin)

        n_bins: Final[int] = list.__len__(bin_lst)
        if n_bins <= 0:
            raise ValueError("No bins specified.")

        material_lst.sort()
        bin_lst.sort()

        object.__setattr__(self, "n_materials", n_materials)
        object.__setattr__(self, "n_bins", n_bins)
        object.__setattr__(self, "bin_min_key", bin_lst[0].key)
        object.__setattr__(self, "bin_max_key", bin_lst[-1].key)
        object.__setattr__(self, "materials", tuple(material_lst))
        object.__setattr__(self, "bins", tuple(bin_lst))
        object.__setattr__(self, "get_material", _make_getter(self.materials))
        object.__setattr__(self, "get_bin", _make_getter(self.bins))

    @classmethod
    def from_directory(cls, directory: str) -> "Scenario":
        """
        Load a scenario from a directory.

        :param directory: the directory
        :return: the scenario
        """
        source: Final[Path] = directory_path(directory)

        materials: Final[list[Material]] = []
        with source.resolve_inside(FILE_MATERIALS).open_for_read() as stream:
            materials.extend(Material.from_csv(stream))  # type: ignore

        bins: Final[list[Bin]] = []
        with source.resolve_inside(FILE_BINS).open_for_read() as stream:
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


def _make_getter(raw: tuple) -> Callable:
    """
    Make an efficient getter.

    :param raw: the raw data
    :return: the getter
    """
    can_use_direct: bool = True
    can_use_offset: bool = True
    offset: int | None = None
    for i, nam in enumerate(raw):
        if i != nam.key:
            can_use_direct = False
            if not can_use_offset:
                break

        if can_use_offset:
            if offset is None:
                offset = nam.key - i
            elif nam.key - offset != i:
                can_use_offset = False
                if not can_use_direct:
                    break

    if can_use_direct:
        return raw.__getitem__

    if can_use_offset:

        def __conv(key: int,  # noqa # type: ignore
                   cl=raw.__getitem__,
                   ofs: int = offset):  # noqa # type: ignore
            """
            Get the item.

            :returns: the item
            """
            return cl(key - ofs)

        return __conv

    return {nam.key: nam for nam in raw}.__getitem__
