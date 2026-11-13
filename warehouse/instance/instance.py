"""
A warehouse setup.

>>> with context():
...     b1 = BinType(None, "random_small", 50, True)
...     b2 = BinType(1, "random_large", 100, True)
...     b3 = BinType(None, "wardrobe", 30)
...     b4 = BinType(None, "drawer", 55)
...     b5 = BinType(4, "shed", 76)
...     m1 = Part(None, "Shoe", "random_small")
...     m2 = Part(1, "Hat", "wardrobe", units_per_package=3)
...     m3 = Part(2, "Skirt", "random_large", units_per_package=9)
...     m4 = Part(None, "T-Shirt", "drawer")
...     e1 = StartEvent(1005000000, 0)
...     e2 = EndEvent(1007000000, 0)
...     instance = Instance((b1, b2, b3, b4, b5), (m1, m2, m3, m4), (e1, e2))

>>> instance.parts
(Part(key=0, name='Shoe', bin_type=BinType(\
key=0, name='random_small', packages=50, is_random=True), \
units_per_package=1), \
Part(key=1, name='Hat', bin_type=BinType(key=2, name='wardrobe', packages=30, \
is_random=False), units_per_package=3), \
Part(key=2, name='Skirt', bin_type=BinType(key=1, name='random_large', \
packages=100, is_random=True), units_per_package=9), \
Part(key=3, name='T-Shirt', bin_type=BinType(key=3, name='drawer', \
packages=55, is_random=False), units_per_package=1))

>>> instance.bin_types
(BinType(key=0, name='random_small', packages=50, is_random=True), \
BinType(key=1, name='random_large', packages=100, is_random=True), \
BinType(key=2, name='wardrobe', packages=30, is_random=False), \
BinType(key=3, name='drawer', packages=55, is_random=False), \
BinType(key=4, name='shed', packages=76, is_random=False))

>>> instance.events
(StartEvent(time=1005000000, priority=0), \
EndEvent(time=1007000000, priority=0))

>>> from pycommons.io.temp import temp_dir
>>> with temp_dir() as td:
...     _ = instance.to_directory(td)
...     instance_2 = Instance.from_directory(td)

>>> instance_2.parts
(Part(key=0, name='Shoe', bin_type=BinType(\
key=0, name='random_small', packages=50, is_random=True), \
units_per_package=1), \
Part(key=1, name='Hat', bin_type=BinType(key=2, name='wardrobe', packages=30, \
is_random=False), units_per_package=3), \
Part(key=2, name='Skirt', bin_type=BinType(key=1, name='random_large', \
packages=100, is_random=True), units_per_package=9), \
Part(key=3, name='T-Shirt', bin_type=BinType(key=3, name='drawer', \
packages=55, is_random=False), units_per_package=1))

>>> instance_2.bin_types
(BinType(key=0, name='random_small', packages=50, is_random=True), \
BinType(key=1, name='random_large', packages=100, is_random=True), \
BinType(key=2, name='wardrobe', packages=30, is_random=False), \
BinType(key=3, name='drawer', packages=55, is_random=False), \
BinType(key=4, name='shed', packages=76, is_random=False))

>>> instance_2.events
(StartEvent(time=1005000000, priority=0), \
EndEvent(time=1007000000, priority=0))

>>> instance.next_multiple_of(1007000000, 32)
1007000000
"""

from dataclasses import dataclass, field
from itertools import batched
from typing import Any, Callable, Final, Iterable, Sequence, TypeVar

from pycommons.io.console import logger
from pycommons.io.csv import COMMENT_START, CSV_SEPARATOR
from pycommons.io.path import Path, directory_path, write_lines
from pycommons.types import check_int_range, type_error

from warehouse.event.time import (
    EndEvent,
    StartEvent,
)
from warehouse.instance.bin_type import BinType
from warehouse.instance.checkpoint import Checkpoint
from warehouse.instance.demand import Demand
from warehouse.instance.element import Element, context
from warehouse.instance.event import (
    Event,
)
from warehouse.instance.part import Part
from warehouse.instance.product import Product
from warehouse.instance.time import (
    EARLIEST_START,
    LATEST_END,
    end_of_job,
    load_day_map,
    next_multiple_of,
    str_to_timedelta,
    timedelta_to_str,
)
from warehouse.rule.jit_rule import JitRule
from warehouse.rule.minmax_rule import MinMaxRule

#: the bin types file
FILE_BIN_TYPES: Final[str] = "bin_types.csv"
#: the parts file
FILE_PARTS: Final[str] = "parts.csv"
#: the events file
FILE_EVENTS: Final[str] = "events.csv"
#: the minmax rules file
FILE_MINMAX_RULES: Final[str] = "minmax_rules.csv"
#: the JIT rules file
FILE_JIT_RULES: Final[str] = "jit_rules.csv"
#: the products file
FILE_PRODUCTS: Final[str] = "products.csv"
#: the checkpoints file
FILE_CHECKPOINTS: Final[str] = "checkpoints.csv"
#: the demands file
FILE_DEMANDS: Final[str] = "demands.csv"
#: the properties file
FILE_PROPERTIES: Final[str] = "properties.txt"

#: the default days
_DAYS: Final[Callable[[int], str]] = (
    "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun").__getitem__
_DAY_MAP: Final[Callable[[str | int], int]] = {
    0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6,
    "0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "mo": 0, "tu": 1, "we": 2, "th": 3, "fr": 4, "sa": 5, "su": 6,
    "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6,
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4,
    "saturday": 5, "sunday": 6,
    "montag": 0, "dienstag": 1, "mittwoch": 2, "donnerstag": 3, "freitag": 4,
    "samstag": 5, "sonnabend": 5, "sonntag": 6,
    "di": 1, "mi": 2, "do": 3, "so": 6,
    "一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6,
    "星期一": 0, "星期二": 1, "星期三": 2, "星期四": 3,
    "星期五": 4, "星期六": 5,
    "星期日": 6, "星期天": 6,
}.__getitem__


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
    minmax_rules: tuple[MinMaxRule, ...] = field(hash=True, compare=True)
    #: the JIT rules holding for this warehouse
    jit_rules: tuple[JitRule, ...] = field(hash=True, compare=True)
    #: the set of products
    products: tuple[Product, ...] = field(hash=True, compare=True)
    #: the set of checkpoints
    checkpoints: tuple[Checkpoint, ...] = field(hash=True, compare=True)
    #: the set of demands
    demands: tuple[Demand, ...] = field(hash=True, compare=True)
    #: the delay until the warehouse delivers: default=4min
    warehouse_delivers_delay: int = field(hash=True, compare=True)
    #: do checkpoints trigger demands?
    checkpoints_trigger_demands: bool = field(hash=True, compare=True)
    #: the interval in which min/max rules are triggered: default=2min
    minmaxrule_interval: int = field(hash=True, compare=True)
    #: the interval in which JIT rules are triggered: default=5min
    jitrule_interval: int = field(hash=True, compare=True)
    #: the work days
    workdays: tuple[int, ...] = field(hash=True, compare=True)
    #: the work time windows
    worktimes: tuple[tuple[int, int], ...] = field(hash=True, compare=True)
    #: the internal work date map, see :func:`load_day_map`
    _workdays: Sequence[int] = field(hash=False, compare=False)

    def __init__(self,
                 bin_types: Iterable[BinType] | None = None,
                 parts: Iterable[Part] | None = None,
                 events: Iterable[Event] | None = None,
                 minmax_rules: Iterable[MinMaxRule] | None = None,
                 jit_rules: Iterable[JitRule] | None = None,
                 products: Iterable[Product] | None = None,
                 checkpoints: Iterable[Checkpoint] | None = None,
                 demands: Iterable[Demand] | None = None,
                 warehouse_delivers_delay: int | str = 240,
                 checkpoints_trigger_demands: bool | str = False,
                 minmaxrule_interval: int | str = 120,
                 jitrule_interval: int | str = 300,
                 workdays: Iterable[int] | str = (0, 1, 2, 3, 4, 5),
                 worktimes: Iterable[int] | str = (8 * 3600, 11 * 3600,
                                                   12 * 3600, 19 * 3600),
                 **_) -> None:
        """
        Create an instance of the warehousing instance.

        :param bin_types: the bin types
        :param parts: the parts
        :param events: the events
        :param minmax_rules: the minimum/maximum rules
        :param jit_rules: the JIT rules
        :param products: the products
        :param checkpoints: the checkpoints
        :param demands: the demands
        :param checkpoints_trigger_demands: do check points trigger demands?
        :param warehouse_delivers_delay: the delay until the warehouse
            delivers
        :param minmaxrule_interval: the interval for min/max rules.
        :param jitrule_interval: the interval for JIT rules.
        :param worktimes: the work time slots
        """
        names: Final[dict[str, Element]] = {}
        object.__setattr__(self, "bin_types", _load_type(
            bin_types, BinType, names))
        object.__setattr__(self, "parts", _load_parts(
            parts, names, self.bin_types))
        object.__setattr__(self, "minmax_rules", _load_minmax_rules(
            minmax_rules, names, self.parts))
        object.__setattr__(self, "products", _load_type(
            products, Product, names))
        object.__setattr__(self, "checkpoints", _load_type(
            checkpoints, Checkpoint, names))
        object.__setattr__(self, "demands", _load_demands(
            demands, self.products, self.checkpoints, self.parts))
        object.__setattr__(self, "jit_rules", _load_jit_rules(
            jit_rules, names, self.parts))
        object.__setattr__(self, "events", _load_events(events))

        if isinstance(checkpoints_trigger_demands, str):
            checkpoints_trigger_demands = str.startswith(str.lower(
                checkpoints_trigger_demands), "t")
        if not isinstance(checkpoints_trigger_demands, bool):
            raise type_error(checkpoints_trigger_demands,
                             "checkpoints_trigger_demands", bool)
        object.__setattr__(self, "warehouse_delivers_delay", check_int_range(
            warehouse_delivers_delay, "warehouse_delivers_delay", 0)
            if isinstance(warehouse_delivers_delay, int) else
            str_to_timedelta(warehouse_delivers_delay))
        object.__setattr__(
            self, "checkpoints_trigger_demands", checkpoints_trigger_demands)
        object.__setattr__(self, "minmaxrule_interval", check_int_range(
            minmaxrule_interval, "minmaxrule_interval", 0) if isinstance(
            minmaxrule_interval, int) else str_to_timedelta(
            minmaxrule_interval))
        object.__setattr__(self, "jitrule_interval", check_int_range(
            jitrule_interval, "jitrule_interval", 0) if isinstance(
            jitrule_interval, int) else str_to_timedelta(
            jitrule_interval))

        if isinstance(workdays, str):
            workdays = map(_DAY_MAP, map(str.lower, str.split(
                workdays, CSV_SEPARATOR)))
        workdays = tuple(sorted(set(workdays)))
        for workday in workdays:
            if not (0 <= workday <= 6):
                raise ValueError(f"Inconsistent workdays {workday!r}.")
        object.__setattr__(self, "workdays", workdays)

        object.__setattr__(self, "_workdays", load_day_map(
            workdays.__contains__))

        if isinstance(worktimes, str):
            worktimes = tuple(map(str_to_timedelta, str.split(
                worktimes, CSV_SEPARATOR)))
        else:
            worktimes = tuple(worktimes)
        if (tuple.__len__(worktimes) & 1) != 0:
            raise ValueError(
                f"Invalid work times {worktimes!r}, must be value pairs.")
        old: int = 0
        for v in worktimes:
            if not (old < v < 86400):
                raise ValueError(f"Invalid work times record {worktimes!r}.")
            old = v
        object.__setattr__(self, "worktimes", tuple(batched(worktimes, 2)))

    def end_of_job(self, start: int, worktime: int,
                   can_wrap: bool = False) -> int:
        """
        Adjust work time based on this instance.

        :param start: the time stamp of the start of the work
        :param worktime: the amount of time needed
        :param can_wrap: whether the job can be split over multiple work days
            or whether it needs to be done as one
        :return: the adjusted time stamp
        """
        return end_of_job(
            start, worktime, can_wrap, self.worktimes, self._workdays)

    def next_multiple_of(self, start: int, multiple_in_s: int) -> int:
        """
        Get the next multiple of the specified number of seconds.

        :param start: the time stamp of the start of the work
        :param multiple_in_s: the multiple in seconds
        :return: the adjusted time stamp
        """
        return next_multiple_of(
            start, multiple_in_s, self.worktimes, self._workdays)

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
            minmax_rules: tuple[MinMaxRule, ...] = _load_csv(
                source.resolve_inside(FILE_MINMAX_RULES), MinMaxRule)
            products: tuple[Product, ...] = _load_csv(
                source.resolve_inside(FILE_PRODUCTS), Product)
            checkpoints: tuple[Checkpoint, ...] = _load_csv(
                source.resolve_inside(FILE_CHECKPOINTS), Checkpoint)
            jit_rules: tuple[JitRule, ...] = _load_csv(
                source.resolve_inside(FILE_JIT_RULES), JitRule)
            demands: tuple[Demand, ...] = _load_csv(
                source.resolve_inside(FILE_DEMANDS), Demand)
            events: tuple[Event, ...] = _load_csv(
                source.resolve_inside(FILE_EVENTS), Event)
            properties = _read_properties(source.resolve_inside(
                FILE_PROPERTIES))

        result = Instance(bin_types=bin_types,
                          parts=parts,
                          events=events,
                          minmax_rules=minmax_rules,
                          jit_rules=jit_rules,
                          products=products,
                          checkpoints=checkpoints,
                          demands=demands,
                          **properties)
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
        _write_csv(dest.resolve_inside(FILE_MINMAX_RULES), MinMaxRule,
                   self.minmax_rules)
        _write_csv(dest.resolve_inside(FILE_JIT_RULES), JitRule,
                   self.jit_rules)
        _write_csv(dest.resolve_inside(FILE_PRODUCTS), Product,
                   self.products)
        _write_csv(dest.resolve_inside(FILE_CHECKPOINTS), Checkpoint,
                   self.checkpoints)
        _write_csv(dest.resolve_inside(FILE_DEMANDS), Demand,
                   self.demands)
        _write_properties(dest.resolve_inside(FILE_PROPERTIES), {
            "workdays": CSV_SEPARATOR.join(map(_DAYS, self.workdays)),
            "worktimes": CSV_SEPARATOR.join(map(
                timedelta_to_str, (j for k in self.worktimes for j in k))),
            "warehouse_delivers_delay": timedelta_to_str(
                self.warehouse_delivers_delay),
            "checkpoints_trigger_demands": self.checkpoints_trigger_demands,
            "minmaxrule_interval": timedelta_to_str(self.minmaxrule_interval),
            "jitrule_interval": timedelta_to_str(self.jitrule_interval),
        })
        logger(f"Finished storing instance/scenario into {dest!r}.")
        return dest


#: the type variable for data to be written to CSV or to be read from CSV
T = TypeVar("T", bound=Element)

#: the type variable for data to be written to CSV or to be read from CSV
A = TypeVar("A", bound=Element | Event | Demand)


def __iterable(source: Iterable[A], cls: type[A]) -> Iterable[A]:
    """
    Enforce that `source` is an iterable.

    :param source: the source
    :param cls: the class
    :return: the source
    """
    if not isinstance(source, Iterable):
        raise type_error(source, f"source[{cls.__name__}]", (
            Iterable, type[None]))
    return source


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

    found: Final[list[T]] = sorted(__iterable(source, cls))
    for i, element in enumerate(found):
        if not isinstance(element, cls):
            raise type_error(element, "element", cls)
        if i != element.key:
            raise ValueError(f"{element!r} cannot be at index {i}.")
        name: str = element.name
        if name in names:
            raise ValueError(f"Name {name!r} of {element!r} already "
                             f"used by {names[name]!r}.")

    return tuple(found)


def _load_events(source: Iterable[Event] | None) -> tuple[Event, ...]:
    """
    Load a source of events.

    :param source: the event source
    :return: the result tuple
    """
    if source is None:
        return ()

    events = sorted(__iterable(source, Event))
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


def _load_parts(parts: Iterable[Part] | None,
                names: dict[str, Element],
                bin_types: tuple[BinType, ...]) -> tuple[Part, ...]:
    """
    Load the parts.

    :param parts: the parts
    :param names: the names dictionary
    :param bin_types: the bin types
    :return: the parts tuple
    """
    result: Final[tuple[Part, ...]] = _load_type(parts, Part, names)
    if tuple.__len__(result) <= 0:
        return result

    bin_type_parts: Final[list[int]] = [0] * tuple.__len__(bin_types)
    for part in result:
        mbt = part.bin_type
        btk = mbt.key
        if mbt is not bin_types[btk]:
            raise ValueError(f"Inconsistent bin type {mbt!r} of part "
                             f"{part!r}, because we already got "
                             f"{bin_types[btk]!r}.")
        names[part.name] = part
        bin_type_parts[btk] += 1
        if (not mbt.is_random) and (bin_type_parts[btk] > 1):
            raise ValueError(
                f"Bin type {mbt!r} is not random, but has multiple "
                f"associated materials, including {part!r}.")
    return result


def _load_minmax_rules(minmax_rules: Iterable[MinMaxRule] | None,
                       names: dict[str, Element],
                       parts: tuple[Part, ...]) -> tuple[MinMaxRule, ...]:
    """
    Load the minimum rules.

    :param minmax_rules: the minimum/maximum rules
    :param names: the names
    :param parts: the parts
    :return: the result
    """
    result: Final[tuple[MinMaxRule, ...]] = _load_type(
        minmax_rules, MinMaxRule, names)
    if tuple.__len__(result) <= 0:
        return result

    min_rule_dct: Final[dict[int, MinMaxRule]] = {}
    for min_rule in result:
        part = min_rule.part
        mrpk: int = part.key
        if part is not parts[mrpk]:
            raise ValueError(
                "Inconsistent part of minimum rule "
                f"{min_rule!r} and {parts[mrpk]!r}.")
        if mrpk in min_rule_dct:
            raise ValueError(
                "Two minimum rules for same part:"
                f" {min_rule!r} and {min_rule_dct[mrpk]!r}.")
        min_rule_dct[mrpk] = min_rule

    return result


def _load_jit_rules(jit_rules: Iterable[JitRule] | None,
                    names: dict[str, Element],
                    parts: tuple[Part, ...]) -> tuple[JitRule, ...]:
    """
    Load the JIT rules.

    :param jit_rules: the JIT rules source
    :param names: the names
    :param parts: the parts
    :return: the result
    """
    result: Final[tuple[JitRule, ...]] = _load_type(jit_rules, JitRule, names)
    if tuple.__len__(result) <= 0:
        return result

    jit_rule_dct: Final[dict[int, JitRule]] = {}
    for jit_rule in result:
        part = jit_rule.part
        pak: int = part.key

        if part is not parts[pak]:
            raise ValueError(
                "Inconsistent part of JIT rule "
                f"{jit_rule!r} and {parts[pak]!r}.")

        if pak in jit_rule_dct:
            raise ValueError(
                "Two JIT rules for same part :"
                f" {jit_rule!r} and {jit_rule_dct[pak]!r}.")
        jit_rule_dct[pak] = jit_rule

    return result


def _load_demands(source: Iterable[Demand] | None,
                  products: tuple[Product, ...],
                  checkpoints: tuple[Checkpoint, ...],
                  parts: tuple[Part, ...]) -> tuple[Demand, ...]:
    """
    Load a source of demands.

    :param source: the source data
    :param products: the products
    :param checkpoints: the checkpoints
    :param parts: the parts
    :return: the tuple
    """
    if source is None:
        return ()

    found: Final[list[Demand]] = []
    for i, demand in enumerate(sorted(__iterable(source, Demand))):
        if not isinstance(demand, Demand):
            raise type_error(demand, f"demand[{i}]", Demand)
        prod: Product = demand.product
        if prod is not products[prod.key]:
            raise ValueError(
                f"{demand!r} product {prod!r} is not {products[prod.key]!r}.")
        cp: Checkpoint = demand.checkpoint
        if cp is not checkpoints[cp.key]:
            raise ValueError(f"{demand!r} checkpoint {cp!r} is not"
                             f" {checkpoints[cp.key]!r}.")
        prt: Part = demand.part
        if prt is not parts[prt.key]:
            raise ValueError(f"{demand!r} part {prt!r} is not"
                             f" {parts[prt.key]!r}.")
        found.append(demand)

    return tuple(found)


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


def _read_properties(file: Path) -> dict[str, str]:
    """
    Read the properties from a file.

    :param file: the properties file
    :return: the properties
    """
    if not file.exists():
        logger(f"Properties file {field!r} does not exist.")
        return {}

    file.enforce_file()
    result: dict[str, str] = {}
    with file.open_for_read() as stream:
        for lidx, oline in enumerate(stream):
            idx: int = str.find(oline, COMMENT_START)
            line: str = str.strip(oline[:idx] if idx > 0 else oline)
            if str.__len__(line) <= 0:
                continue
            idx = str.find(line, "=")
            if idx <= 0:
                continue
            key: str = str.lower(str.strip(line[:idx]))
            val: str = str.strip(line[idx + 1:])
            if (str.__len__(key) <= 0) or (str.__len__(val) <= 0):
                raise ValueError(
                    f"Invalid key values pair {key!r} = {val!r} in line"
                    f" {lidx + 1} of properties file {file!r}.")
            if key in result:
                raise ValueError(
                    f"Key {key!r} already exists in properties, cannot get "
                    f"new value {val!r} in line {lidx + 1} of properties "
                    f"file {file!r}. ")
            result[key] = val
    return result


def _write_properties(file: Path, properties: dict[str, Any]) -> None:
    """
    Write the properties to a file.

    :param file: the file
    :param properties: the properties
    """
    if dict.__len__(properties) > 0:
        logger(f"Storing properties elements into {file!r}.")

        with file.open_for_write() as stream:
            write_lines((f"{k} = {v}" for k, v in properties.items()), stream)
    else:
        if file.exists():
            raise ValueError(f"File {file!r} exists, but we do not have any"
                             " properties to store.")
        logger("Instance does not have any properties, so we don't need "
               f"to store them and thus won't create file {file!r}.")
