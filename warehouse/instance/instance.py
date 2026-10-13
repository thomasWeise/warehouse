"""
A warehouse setup.

>>> with context():
...     b1 = BinType(None, "random_small", 50)
...     b2 = BinType(1, "random_large", 100)
...     b3 = BinType(None, "wardrobe", 30)
...     b4 = BinType(None, "drawer", 55)
...     b5 = BinType(4, "shed", 76)
...     m1 = Material(None, "Shoe", "random_small")
...     m2 = Material(1, "Hat", "wardrobe")
...     m3 = Material(2, "Skirt", "random_large")
...     m4 = Material(None, "T-Shirt", "drawer")
...     e1 = StartEvent(1005000000000)
...     e2 = EndEvent(1007000000000)
...     instance = Instance((b1, b2, b3, b4, b5), (m1, m2, m3, m4), (e1, e2))

>>> instance.n_materials
4

>>> instance.materials
(Material(key=0, name='Shoe', bin_type=BinType(key=0, name='random_small', \
amount=50)), \
Material(key=1, name='Hat', bin_type=BinType(key=2, name='wardrobe', \
amount=30)), \
Material(key=2, name='Skirt', bin_type=BinType(key=1, name='random_large', \
amount=100)), \
Material(key=3, name='T-Shirt', bin_type=BinType(key=3, name='drawer', \
amount=55)))

>>> instance.n_bin_types
5

>>> instance.bin_types
(BinType(key=0, name='random_small', amount=50), \
BinType(key=1, name='random_large', amount=100), \
BinType(key=2, name='wardrobe', amount=30), \
BinType(key=3, name='drawer', amount=55), \
BinType(key=4, name='shed', amount=76))

>>> instance.n_events
2

>>> instance.events
(StartEvent(time=1005000000000), EndEvent(time=1007000000000))

>>> from pycommons.io.temp import temp_dir
>>> with temp_dir() as td:
...     _ = instance.to_directory(td)
...     instance_2 = Instance.from_directory(td)

>>> instance_2.n_materials
4

>>> instance_2.materials
(Material(key=0, name='Shoe', bin_type=BinType(key=0, name='random_small', \
amount=50)), \
Material(key=1, name='Hat', bin_type=BinType(key=2, name='wardrobe', \
amount=30)), \
Material(key=2, name='Skirt', bin_type=BinType(key=1, name='random_large', \
amount=100)), \
Material(key=3, name='T-Shirt', bin_type=BinType(key=3, name='drawer', \
amount=55)))

>>> instance_2.n_bin_types
5

>>> instance_2.bin_types
(BinType(key=0, name='random_small', amount=50), \
BinType(key=1, name='random_large', amount=100), \
BinType(key=2, name='wardrobe', amount=30), \
BinType(key=3, name='drawer', amount=55), \
BinType(key=4, name='shed', amount=76))

>>> instance_2.n_events
2

>>> instance_2.events
(StartEvent(time=1005000000000), EndEvent(time=1007000000000))
"""

from dataclasses import dataclass, field
from typing import Final, Iterable, TypeVar

from pycommons.io.console import logger
from pycommons.io.path import Path, directory_path, write_lines
from pycommons.types import type_error

from warehouse.event.time import (
    EndEvent,
    StartEvent,
)
from warehouse.instance.bin_type import BinType
from warehouse.instance.element import Element, ElementResolver, context
from warehouse.instance.event import (
    Event,
)
from warehouse.instance.material import Material
from warehouse.instance.time import (
    EARLIEST_START,
    LATEST_END,
)

#: the bin types file
FILE_BIN_TYPES: Final[str] = "bin_types.csv"
#: the materials file
FILE_MATERIALS: Final[str] = "materials.csv"
#: the events file
FILE_EVENTS: Final[str] = "events.csv"

#: the type variable for data to be written to CSV or to be read from CSV
T = TypeVar("T", bound=Element)


@dataclass(frozen=True, init=False, order=True, eq=True)
class Instance(ElementResolver):
    """A warehousing instance."""

    #: the number of materials
    n_materials: int = field(hash=False, compare=False)
    #: the number of bin types
    n_bin_types: int = field(hash=False, compare=False)
    #: the number of events
    n_events: int = field(hash=False, compare=False)
    #: the bin configuration of the warehouse
    bin_types: tuple[BinType, ...] = field(hash=True, compare=True)
    #: the material types available for the warehouse
    materials: tuple[Material, ...] = field(hash=True, compare=True)
    #: the pre-defined events for the instance
    events: tuple[Event, ...] = field(hash=True, compare=True)

    def __init__(self,
                 bin_types: Iterable[BinType],
                 materials: Iterable[Material],
                 events: Iterable[Event] | None = None) -> None:
        """
        Create an instance of the warehousing instance.

        :param bin_types: the bin types
        :param materials: the materials
        :param events: the events
        """
        if not isinstance(bin_types, Iterable):
            raise type_error(bin_types, "bin_types", Iterable)
        if not isinstance(materials, Iterable):
            raise type_error(materials, "materials", Iterable)

        material_lst: Final[list[Material]] = []
        bin_type_lst: Final[list[BinType]] = []
        names: Final[dict[str, Element]] = {}

        for i, bin_type in enumerate(bin_types):
            if not isinstance(bin_type, BinType):
                raise type_error(bin_type, f"bin_types[{i}]", BinType)
            name = bin_type.name
            if name in names:
                raise ValueError(
                    f"Name of {bin_type!r} already in use for {names[name]}.")
            names[bin_type.name] = bin_type
            bin_type_lst.append(bin_type)

        n_bin_types: Final[int] = list.__len__(bin_type_lst)
        if n_bin_types <= 0:
            raise ValueError("No bin types specified!")

        for i, material in enumerate(materials):
            if not isinstance(material, Material):
                raise type_error(material, f"materials[{i}]", Material)
            name = material.name
            if name in names:
                raise ValueError(
                    f"Name of {material!r} already in use for {names[name]}.")
            mbt = material.bin_type
            if mbt is not bin_type_lst[mbt.key]:
                raise ValueError(f"Inconsistent bin type {mbt!r} of material "
                                 f"{material!r}, because we already got "
                                 f"{bin_type_lst[mbt.key]!r}.")
            names[material.name] = material
            material_lst.append(material)

        n_materials: Final[int] = list.__len__(material_lst)
        if n_materials <= 0:
            raise ValueError("No materials specified.")

        material_lst.sort()
        for i, material in enumerate(material_lst):
            if i != material.key:
                raise ValueError(
                    f"Inconsistent key for {i}-th material {material!r}.")
        bin_type_lst.sort()
        for i, bin_type in enumerate(bin_type_lst):
            if i != bin_type.key:
                raise ValueError(
                    f"Inconsistent key for {i}-th bin type {bin_type!r}.")

        if events is None:
            events = ()
        else:
            events = sorted(events)
            last_time = EARLIEST_START
            i = -1
            for i, event in enumerate(events):
                if not isinstance(event, Event):
                    raise type_error(event, f"event[{i}]", Event)
                time = event.time
                if not (EARLIEST_START <= last_time <= time <= LATEST_END):
                    raise ValueError(f"Inconsistent time for {event!r}.")
                last_time = time
                if isinstance(event, StartEvent):
                    if i > 0:
                        raise ValueError(
                            f"{event!r} not permitted at index {i}.")
                elif isinstance(event, EndEvent) and (
                        i < (list.__len__(events) - 1)):
                    raise ValueError(f"{event!r} not permitted at index {i}.")
            if i <= 0:
                events = ()
            else:
                if not isinstance(events[0], StartEvent):
                    events.insert(0, StartEvent(events[0].time))
                events = tuple(events)

        object.__setattr__(self, "n_materials", n_materials)
        object.__setattr__(self, "n_bin_types", n_bin_types)
        object.__setattr__(self, "n_events", tuple.__len__(events))
        object.__setattr__(self, "materials", tuple(material_lst))
        object.__setattr__(self, "bin_types", tuple(bin_type_lst))
        object.__setattr__(self, "events", events)
        object.__setattr__(self, "_names", names)

    def resolve(self, cls: type[T], name_or_key: str | int) -> T:
        """
        Get the element of the given name and type.

        :param cls: the element class
        :param name_or_key: the element name or key

        :return: the element
        """
        if isinstance(name_or_key, int):
            if cls is BinType:
                return self.bin_types[name_or_key]  # type: ignore
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
    def from_directory(cls, directory: str) -> "Instance":
        """
        Load a instance from a directory.

        :param directory: the directory
        :return: the instance
        """
        source: Final[Path] = directory_path(directory)
        logger(f"Beginning to load instance/scenario from {source!r}.")

        with context():
            file: Path = source.resolve_inside(FILE_BIN_TYPES)
            file.enforce_file()
            logger(f"Now loading bin types from {file!r}.")
            bin_types: Final[list[BinType]] = []
            with file.open_for_read() as stream:
                bin_types.extend(BinType.from_csv(stream))  # type: ignore
            got: int = list.__len__(bin_types)
            if got <= 0:
                raise ValueError(
                    f"File {file!r} does not contain any bin types.")
            logger(f"Finished loading {got} bin types from {file!r}.")

            file = source.resolve_inside(FILE_MATERIALS)
            file.enforce_file()
            logger(f"Now loading materials from {file!r}.")
            materials: Final[list[Material]] = []
            with file.open_for_read() as stream:
                materials.extend(Material.from_csv(stream))  # type: ignore
            got = list.__len__(materials)
            if got <= 0:
                raise ValueError(
                    f"File {file!r} does not contain any materials.")
            logger(f"Finished loading {got} materials from {file!r}.")

            file = source.resolve_inside(FILE_EVENTS)
            events: list[Event] | None = None
            if file.exists():
                file.enforce_file()
                logger(f"Now loading events from {file!r}.")
                events = []
                with file.open_for_read() as stream:
                    events.extend(Event.from_csv(stream))
                got = list.__len__(events)
                if got <= 0:
                    raise ValueError(
                        f"File {file!r} does not contain any events.")
                logger(f"Finished loading {got} events from {file!r}.")
            else:
                logger(f"{file!r} does not exist, so we cannot load events.")

        result = Instance(bin_types=bin_types,
                          materials=materials,
                          events=events)
        logger(f"Finished loading instance/scenario from {source!r}.")
        return result

    def to_directory(self, directory: str) -> Path:
        """
        Store a instance into a directory.

        :param directory: the directory
        :return: the path to the directory
        """
        dest: Final[Path] = Path(directory)
        dest.ensure_dir_exists()
        logger(f"Beginning to store instance/scenario into {dest!r}.")

        file = dest.resolve_inside(FILE_BIN_TYPES)
        logger(f"Storing bin_types into {file!r}.")
        with file.open_for_write() as stream:
            write_lines(BinType.to_csv(self.bin_types), stream)

        file = dest.resolve_inside(FILE_MATERIALS)
        logger(f"Storing materials into {file!r}.")
        with file.open_for_write() as stream:
            write_lines(Material.to_csv(self.materials), stream)

        if tuple.__len__(self.events) > 0:
            file = dest.resolve_inside(FILE_EVENTS)
            logger(f"Storing events into {file!r}.")
            with file.open_for_write() as stream:
                write_lines(Event.to_csv(self.events), stream)
        else:
            if file.exists():
                raise ValueError(f"File {file!r} exists, but we do "
                                 "not have events to store.")
            logger("Instance does not have events, so we don't need to store"
                   f" them and thus won't create file {file!r}.")

        logger(f"Finished storing instance/scenario into {dest!r}.")
        return dest
