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
from warehouse.instance.element import Element, ElementResolver, context
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

#: the type variable for data to be written to CSV or to be read from CSV
T = TypeVar("T", bound=Element)


@dataclass(frozen=True, init=False, order=True, eq=True)
class Instance(ElementResolver):
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
        if not isinstance(bin_types, Iterable):
            raise type_error(bin_types, "bin_types", Iterable)
        if not isinstance(parts, Iterable):
            raise type_error(parts, "parts", Iterable)

        part_lst: Final[list[Part]] = []
        bin_type_lst: Final[list[BinType]] = []
        bin_type_parts: Final[list[int]] = []
        names: Final[dict[str, Element]] = {}

        for i, bin_type in enumerate(bin_types):
            if not isinstance(bin_type, BinType):
                raise type_error(bin_type, f"bin_types[{i}]", BinType)
            if i != list.__len__(bin_type_lst):
                raise ValueError(f"{bin_type!r} cannot be at index {i}.")
            name = bin_type.name
            if name in names:
                raise ValueError(
                    f"Name of {bin_type!r} already in use for {names[name]}.")
            names[bin_type.name] = bin_type
            bin_type_lst.append(bin_type)
            bin_type_parts.append(0)

        n_bin_types: Final[int] = list.__len__(bin_type_lst)
        if n_bin_types <= 0:
            raise ValueError("No bin types specified!")

        for i, part in enumerate(parts):
            if not isinstance(part, Part):
                raise type_error(part, f"parts[{i}]", Part)
            if i != list.__len__(part_lst):
                raise ValueError(f"{part!r} cannot be at index {i}.")
            name = part.name
            if name in names:
                raise ValueError(
                    f"Name of {part!r} already in use for {names[name]}.")
            mbt = part.bin_type
            btk = mbt.key
            if mbt is not bin_type_lst[btk]:
                raise ValueError(f"Inconsistent bin type {mbt!r} of part "
                                 f"{part!r}, because we already got "
                                 f"{bin_type_lst[btk]!r}.")
            names[part.name] = part
            bin_type_parts[btk] += 1
            if (not mbt.is_random) and (bin_type_parts[btk] > 1):
                raise ValueError(
                    f"Bin type {mbt!r} is not random, but has multiple "
                    f"associated materials, including {part!r}.")
            part_lst.append(part)

        n_parts: Final[int] = list.__len__(part_lst)
        if n_parts <= 0:
            raise ValueError("No parts specified.")

        part_lst.sort()
        for i, part in enumerate(part_lst):
            if i != part.key:
                raise ValueError(
                    f"Inconsistent key for {i}-th part {part!r}.")
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
                    events.insert(0, StartEvent(events[0].time, 0))
                events = tuple(events)

        min_rule_lst: Final[list[MinRule]] = []
        min_rule_dct: Final[dict[int, MinRule]] = {}
        if min_rules is not None:
            for i, min_rule in enumerate(min_rules):
                if not isinstance(min_rule, MinRule):
                    raise type_error(min_rule, f"min_rules[{i}]", MinRule)
                if i != list.__len__(min_rule_lst):
                    raise ValueError(f"{min_rule!r} cannot be a index {i}.")
                name = min_rule.name
                if name in names:
                    raise ValueError(f"Name of {min_rule!r} already in use"
                                     f" for {names[name]}.")
                names[name] = min_rule
                part = min_rule.part
                mrpk: int = part.key
                if part is not part_lst[mrpk]:
                    raise ValueError(
                        "Inconsistent part of minimum rule "
                        f"{min_rule!r} and {part_lst[mrpk]!r}.")
                if mrpk in min_rule_dct:
                    raise ValueError(
                        "Two minimum rules for same part:"
                        f" {min_rule!r} and {min_rule_dct[mrpk]!r}.")
                min_rule_dct[mrpk] = min_rule
                min_rule_lst.append(min_rule)

        object.__setattr__(self, "parts", tuple(part_lst))
        object.__setattr__(self, "bin_types", tuple(bin_type_lst))
        object.__setattr__(self, "events", events)
        object.__setattr__(self, "min_rules", tuple(min_rule_lst))
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
            if cls is Part:
                return self.parts[name_or_key]  # type: ignore
            if cls is MinRule:
                return self.min_rules[name_or_key]  # type: ignore
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

            file = source.resolve_inside(FILE_PARTS)
            file.enforce_file()
            logger(f"Now loading parts from {file!r}.")
            parts: Final[list[Part]] = []
            with file.open_for_read() as stream:
                parts.extend(Part.from_csv(stream))  # type: ignore
            got = list.__len__(parts)
            if got <= 0:
                raise ValueError(
                    f"File {file!r} does not contain any parts.")
            logger(f"Finished loading {got} parts from {file!r}.")

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

            file = source.resolve_inside(FILE_MIN_RULES)
            min_rules: list[MinRule] | None = None
            if file.exists():
                file.enforce_file()
                logger(f"Now loading events from {file!r}.")
                min_rules = []
                with file.open_for_read() as stream:
                    min_rules.extend(MinRule.from_csv(stream))
                got = list.__len__(min_rules)
                if got <= 0:
                    raise ValueError(
                        f"File {file!r} does not contain any minimum rules.")
                logger(f"Finished loading {got} minimum rules from {file!r}.")
            else:
                logger(f"{file!r} does not exist, so we cannot "
                       "load minimum rules.")

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

        file = dest.resolve_inside(FILE_BIN_TYPES)
        logger(f"Storing bin_types into {file!r}.")
        with file.open_for_write() as stream:
            write_lines(BinType.to_csv(self.bin_types), stream)

        file = dest.resolve_inside(FILE_PARTS)
        logger(f"Storing parts into {file!r}.")
        with file.open_for_write() as stream:
            write_lines(Part.to_csv(self.parts), stream)

        file = dest.resolve_inside(FILE_EVENTS)
        if tuple.__len__(self.events) > 0:
            logger(f"Storing events into {file!r}.")
            with file.open_for_write() as stream:
                write_lines(Event.to_csv(self.events), stream)
        else:
            if file.exists():
                raise ValueError(f"File {file!r} exists, but we do "
                                 "not have events to store.")
            logger("Instance does not have events, so we don't need to store"
                   f" them and thus won't create file {file!r}.")

        file = dest.resolve_inside(FILE_MIN_RULES)
        if tuple.__len__(self.min_rules) > 0:
            logger(f"Storing minimum rules into {file!r}.")
            with file.open_for_write() as stream:
                write_lines(MinRule.to_csv(self.min_rules), stream)
        else:
            if file.exists():
                raise ValueError(f"File {file!r} exists, but we do "
                                 "not have minimum rules to store.")
            logger("Instance does not have minimum rules, so we don't need to"
                   f" store them and thus won't create file {file!r}.")

        logger(f"Finished storing instance/scenario into {dest!r}.")
        return dest
