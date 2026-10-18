"""
A warehouse setup.

>>> with context():
...     b1 = BinType(None, "random_small", 50, True)
...     b2 = BinType(1, "random_large", 100, True)
...     b3 = BinType(None, "wardrobe", 30)
...     b4 = BinType(None, "drawer", 55)
...     b5 = BinType(4, "shed", 76)
...     m1 = Part(None, "Shoe", "random_small")
...     m2 = Part(1, "Hat", "wardrobe")
...     m3 = Part(2, "Skirt", "random_large")
...     m4 = Part(None, "T-Shirt", "drawer")
...     e1 = StartEvent(1005000000000, 0)
...     e2 = EndEvent(1007000000000, 0)
...     instance = Instance((b1, b2, b3, b4, b5), (m1, m2, m3, m4), (e1, e2))

>>> instance.parts
(Part(key=0, name='Shoe', bin_type=BinType(key=0, name='random_small', \
amount=50, is_random=True)), \
Part(key=1, name='Hat', bin_type=BinType(key=2, name='wardrobe', \
amount=30, is_random=False)), \
Part(key=2, name='Skirt', bin_type=BinType(key=1, name='random_large', \
amount=100, is_random=True)), \
Part(key=3, name='T-Shirt', bin_type=BinType(key=3, name='drawer', \
amount=55, is_random=False)))

>>> instance.bin_types
(BinType(key=0, name='random_small', amount=50, is_random=True), \
BinType(key=1, name='random_large', amount=100, is_random=True), \
BinType(key=2, name='wardrobe', amount=30, is_random=False), \
BinType(key=3, name='drawer', amount=55, is_random=False), \
BinType(key=4, name='shed', amount=76, is_random=False))

>>> instance.events
(StartEvent(time=1005000000000, priority=0), \
EndEvent(time=1007000000000, priority=0))

>>> from pycommons.io.temp import temp_dir
>>> with temp_dir() as td:
...     _ = instance.to_directory(td)
...     instance_2 = Instance.from_directory(td)

>>> instance_2.parts
(Part(key=0, name='Shoe', bin_type=BinType(key=0, name='random_small', \
amount=50, is_random=True)), \
Part(key=1, name='Hat', bin_type=BinType(key=2, name='wardrobe', \
amount=30, is_random=False)), \
Part(key=2, name='Skirt', bin_type=BinType(key=1, name='random_large', \
amount=100, is_random=True)), \
Part(key=3, name='T-Shirt', bin_type=BinType(key=3, name='drawer', \
amount=55, is_random=False)))

>>> instance_2.bin_types
(BinType(key=0, name='random_small', amount=50, is_random=True), \
BinType(key=1, name='random_large', amount=100, is_random=True), \
BinType(key=2, name='wardrobe', amount=30, is_random=False), \
BinType(key=3, name='drawer', amount=55, is_random=False), \
BinType(key=4, name='shed', amount=76, is_random=False))

>>> instance_2.events
(StartEvent(time=1005000000000, priority=0), \
EndEvent(time=1007000000000, priority=0))
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
from warehouse.instance.element import Element, context
from warehouse.instance.event import (
    Event,
)
from warehouse.instance.part import Part
from warehouse.instance.time import (
    EARLIEST_START,
    LATEST_END,
)
from warehouse.rule.min_rule import MinRule

#: the bin types file
FILE_BIN_TYPES: Final[str] = "bin_types.csv"
#: the parts file
FILE_PARTS: Final[str] = "parts.csv"
#: the events file
FILE_EVENTS: Final[str] = "events.csv"
#: the minimum rules file
FILE_MIN_RULES: Final[str] = "min_rules.csv"


@dataclass(frozen=True, init=False, order=True, eq=True)
class Instance:
    """A warehousing instance."""

    #: the bin configuration of the warehouse
    bin_types: tuple[BinType, ...] = field(hash=True, compare=True)
    #: the part types available for the warehouse
    parts: tuple[Part, ...] = field(hash=True, compare=True)
    #: the pre-defined events for the instance
    events: tuple[Event, ...] = field(hash=True, compare=True)
    #: the min rules holding for this warehouse
    min_rules: tuple[MinRule, ...] = field(hash=True, compare=True)

    def __init__(self,
                 bin_types: Iterable[BinType],
                 parts: Iterable[Part],
                 events: Iterable[Event] | None = None,
                 min_rules: Iterable[MinRule] | None = None) -> None:
        """
        Create an instance of the warehousing instance.

        :param bin_types: the bin types
        :param parts: the parts
        :param events: the events
        """
        names: Final[dict[str, Element]] = {}
        object.__setattr__(self, "bin_types", _load_type(
            bin_types, BinType, names))

        bin_type_parts: Final[list[int]] = [0] * tuple.__len__(self.bin_types)
        object.__setattr__(self, "parts", _load_type(parts, Part, names))
        for part in self.parts:
            mbt = part.bin_type
            btk = mbt.key
            if mbt is not self.bin_types[btk]:
                raise ValueError(f"Inconsistent bin type {mbt!r} of part "
                                 f"{part!r}, because we already got "
                                 f"{self.bin_types[btk]!r}.")
            names[part.name] = part
            bin_type_parts[btk] += 1
            if (not mbt.is_random) and (bin_type_parts[btk] > 1):
                raise ValueError(
                    f"Bin type {mbt!r} is not random, but has multiple "
                    f"associated materials, including {part!r}.")

        object.__setattr__(self, "events", _load_events(events))
        object.__setattr__(self, "min_rules", _load_type(
            min_rules, MinRule, names))

        min_rule_dct: Final[dict[int, MinRule]] = {}
        for min_rule in self.min_rules:
            part = min_rule.part
            mrpk: int = part.key
            if part is not self.parts[mrpk]:
                raise ValueError(
                    "Inconsistent part of minimum rule "
                    f"{min_rule!r} and {self.parts[mrpk]!r}.")
            if mrpk in min_rule_dct:
                raise ValueError(
                    "Two minimum rules for same part:"
                    f" {min_rule!r} and {min_rule_dct[mrpk]!r}.")
            min_rule_dct[mrpk] = min_rule

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
            bin_types: tuple[BinType, ...] = _load_csv(source.resolve_inside(
                FILE_BIN_TYPES), BinType)
            parts: tuple[Part, ...] = _load_csv(source.resolve_inside(
                FILE_PARTS), Part)
            events: tuple[Event, ...] = _load_csv(
                source.resolve_inside(FILE_EVENTS), Event)
            min_rules: tuple[MinRule, ...] = _load_csv(
                source.resolve_inside(FILE_MIN_RULES), MinRule)

        result = Instance(bin_types=bin_types,
                          parts=parts,
                          events=events,
                          min_rules=min_rules)
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
        _write_csv(dest.resolve_inside(FILE_BIN_TYPES), BinType,
                   self.bin_types)
        _write_csv(dest.resolve_inside(FILE_PARTS), Part, self.parts)
        _write_csv(dest.resolve_inside(FILE_EVENTS), Event, self.events)
        _write_csv(dest.resolve_inside(FILE_MIN_RULES), MinRule,
                   self.min_rules)
        logger(f"Finished storing instance/scenario into {dest!r}.")
        return dest


#: the type variable for data to be written to CSV or to be read from CSV
T = TypeVar("T", bound=Element)

#: the type variable for data to be written to CSV or to be read from CSV
A = TypeVar("A", bound=Element | Event)


def _load_type(source: Iterable[T] | None,
               cls: type[T],
               names: dict[str, Element]) -> tuple[T, ...]:
    """
    Create a tuple of a given data type.

    :param source: the source data
    :param cls: the class
    :param names: the elements already known

    :return: the tuple
    """
    if source is None:
        return ()
    if not isinstance(source, Iterable):
        raise type_error(source, f"source[{cls.__name__}]", (
            Iterable, type[None]))

    found: list[T] = []
    for element in source:
        if not isinstance(element, cls):
            raise type_error(element, "element", cls)

        name: str = element.name
        if name in names:
            raise ValueError(f"Name {name!r} of {element!r} already "
                             f"used by {names[name]!r}.")
        found.append(element)
    found.sort()
    for i, element in enumerate(found):
        if i != element.key:
            raise ValueError(f"{element!r} cannot be at index {i}.")
    return tuple(found)


def _load_events(source: Iterable[Event] | None) -> tuple[Event, ...]:
    """
    Load a source of events.

    :param source: the event source
    :return: the result tuple
    """
    if source is None:
        return ()

    events = sorted(source)
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
        return ()
    if not isinstance(events[0], StartEvent):
        events.insert(0, StartEvent(events[0].time, 0))
    return tuple(events)


def _load_csv(file: Path, cls: type[A]) -> tuple[A, ...]:
    """
    Load data from a CSV file.

    :param file: the file
    :param cls: the class
    :return: the data
    """
    data: tuple[A, ...] | None = None
    if file.exists():
        file.enforce_file()
        logger(f"Now loading {cls.__name__!r} objects from {file!r}.")
        with file.open_for_read() as stream:
            data = tuple(cls.from_csv(stream))  # type: ignore
        got = tuple.__len__(data)
        if got <= 0:
            raise ValueError(f"File {file!r} does not contain any "
                             f"{cls.__name__!r} objects.")
        logger(f"Finished loading {got} {cls.__name__!r} objects "
               f"from {file!r}.")
        return data

    logger(f"{file!r} does not exist, so we cannot load "
           f"{cls.__name__!r} objects.")
    return ()


def _write_csv(file: Path, cls: type[A], source: tuple[A, ...]) -> None:
    """
    Write data to a CSV file.

    :param file: the file
    :param cls: the class
    :param source: the data
    """
    if tuple.__len__(source) > 0:
        logger(f"Storing {cls.__name__} elements into {file!r}.")
        with file.open_for_write() as stream:
            write_lines(cls.to_csv(source), stream)  # type: ignore
    else:
        if file.exists():
            raise ValueError(f"File {file!r} exists, but we do "
                             f"not have any {cls.__name__} to store.")
        logger("Instance does not have any {cls.__name__}, so we don't need "
               f"to store them and thus won't create file {file!r}.")
