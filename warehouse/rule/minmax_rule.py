"""
A class holding the information of a Min/Max-Rule.

A Min/Max-Rule specifies five things:

- The :attr:`~warehouse.instance.element.Element.name` of the rule.
- The :attr:`~MinMaxRule.part` for which it applies, the minimum number of
  units of that part that we always want to have in the warehouse
  (in :attr:`~MinMaxRule.minimum_units`),
- the level (:attr:`MinMaxRule.maximum_units`) to which we will replenish the
  warehouse if the stock level falls under the minimum, and
- the delay after which the newly ordered parts will arrive, stored in
  :attr:`~warehouse.instance.rule.Rule.effect_delay`.

If the stock level ever falls under the minimum, we will order at least one
new package of material.
We will basically compute `(units in warehouse + units on the way)` and divide
this by the units per package.
This value is rounded *down*, but never below 1.
Then this gives us the number of packages that we have to order to replenish
the warehouse.

Min/Max-Rules are checked every two minutes by default, starting immediately
at the beginning of the work day.
"""

from dataclasses import dataclass
from typing import Final, Iterable, TypeVar, cast

from pycommons.io.csv import (
    csv_column,
    csv_column_or_none,
    csv_scope,
    csv_val_or_none,
)
from pycommons.types import check_int_range

from warehouse.instance.element import (
    check_to_amount,
    context,
)
from warehouse.instance.part import COLUMN_PART, Part
from warehouse.instance.rule import CsvReader as CsvReaderBase
from warehouse.instance.rule import CsvWriter as CsvWriterBase
from warehouse.instance.rule import Rule

#: the minimum column
COLUMN_MINIMUM: Final[str] = "minimum_units"

#: the maximum column
COLUMN_MAXIMUM: Final[str] = "maximum_units"


@dataclass(frozen=True, init=False, order=False, eq=False)
class MinMaxRule(Rule):
    """A class for identifying a minimum rule."""

    #: the part which is concerned here
    part: Part
    #: the minimum units value triggering the rule
    minimum_units: int
    #: the maximum units value, to whose amount we order
    maximum_units: int

    def __init__(self, key: int | None, name: str,
                 part: Part | int | str,
                 minimum_units: int | str = 1,
                 maximum_units: int | str | None = None,
                 effect_delay: int | str = 150 * 60) -> None:
        """
        Create a new minimum rule.

        :param key: the rule key
        :param name: the rule name
        :param part: the part concerned by the rule
        :param minimum: the minimum value of that part
        :param minimum: the maximum value of that part
        :param effect_delay: the approximate delay after which the re-ordered
            material will arrive
        """
        super().__init__(key, name, effect_delay)
        with context() as ctx:
            part = ctx.resolve(Part, part)
        object.__setattr__(self, "part", part)
        object.__setattr__(self, "minimum_units", check_to_amount(
            minimum_units))
        object.__setattr__(
            self, "maximum_units", self.minimum_units if maximum_units is None
            else check_int_range(check_to_amount(maximum_units),
                                 "maximum_units", self.minimum_units))

    def __eq__(self, other) -> bool:
        """
        Compare two minimum rules for "equality".

        :param other: the other element
        :return: `True` if this element is equal, `False` otherwise
        """
        return (self.__class__ is other.__class__) and (
            self.key == other.key) and (self.name == other.name) and (
            self.part == other.part) and (
            self.minimum_units == other.minimum_units) and (
            self.maximum_units == other.maximum_units) and (
            self.effect_delay == other.effect_delay)

    def __ne__(self, other) -> bool:
        """
        Compare two minimum rules for "not equal".

        :param other: the other element
        :return: `True` if this element is not equal, `False` otherwise
        """
        return (self.__class__ is not other.__class__) or (
            self.key != other.key) or (self.name != other.name) or (
            self.part != other.part) or (
            self.minimum_units != other.minimum_units) or (
            self.maximum_units != other.maximum_units) or (
            self.effect_delay != other.effect_delay)

    def __hash__(self) -> int:
        """
        Get the hash code of the minimum rule.

        :return: the hash code
        """
        return self._hash

    @classmethod
    def to_csv(cls,  # type: ignore
               data: Iterable["MinMaxRule"]) -> Iterable[str]:  # type: ignore
        """
        Convert an iterable of the object to a CSV stream.

        :param data: the data
        :return: the stream
        """
        return CsvWriter[MinMaxRule].write(data)

    @classmethod
    def from_csv(cls, rows: Iterable[str]) -> Iterable["MinMaxRule"]:
        """
        Get the data from CSV.

        :param rows: the rows
        :return: the sequence of objects
        """
        with context():
            yield from CsvReader[MinMaxRule].read(rows=rows, clazz=cls)


#: the type variable for data to be written to CSV or to be read from CSV
T = TypeVar("T", bound="MinMaxRule")


class CsvReader(CsvReaderBase[T]):
    """A CsvReader that reads named objects from a CSV file."""

    def __init__(self, columns: dict[str, int],
                 clazz: type[T] = cast("type[T]", MinMaxRule)):
        """
        Initialize.

        :param columns: the named object columns
        """
        super().__init__(columns, clazz)
        #: the part column
        self.col_part: Final[int] = csv_column(columns, COLUMN_PART, True)
        #: the minimum column
        self.col_min: Final[int] = csv_column(columns, COLUMN_MINIMUM, True)
        #: the maximum column
        self.col_max: Final[int | None] = csv_column_or_none(
            columns, COLUMN_MAXIMUM, True)

    def parse_row(self, data: list[str]) -> T:
        """
        Parse a data row.

        :param data: the data row
        :return: the instance
        """
        return self.clazz(
            key=csv_val_or_none(data, self.col_key, int),
            name=data[self.col_name],
            part=data[self.col_part],
            minimum_units=data[self.col_min],
            maximum_units=csv_val_or_none(data, self.col_max, int),
            effect_delay=data[self.col_delay])


class CsvWriter(CsvWriterBase[T]):
    """Write the data to a csv file."""

    def __init__(self, data: Iterable[T], scope: str | None = None) -> None:
        """
        Initialize the CSV writer.

        :param data: the data
        :param scope: the scope
        """
        super().__init__(data, scope)
        #: the part column
        self.col_part: Final[str] = csv_scope(scope, COLUMN_PART)
        #: the minimum column
        self.col_min: Final[str] = csv_scope(scope, COLUMN_MINIMUM)

        needs_max: bool = False
        for row in data:
            if row.maximum_units > row.minimum_units:
                needs_max = True
                break
        #: the maximum column
        self.col_max: Final[str | None] = csv_scope(
            scope, COLUMN_MAXIMUM) if needs_max else None

    def get_column_titles(self) -> Iterable[str]:
        """
        Get the column titles.

        :returns: the column titles
        """
        yield from super().get_column_titles()
        yield self.col_part
        yield self.col_min
        if self.col_max is not None:
            yield self.col_max

    def get_row(self, data: T) -> Iterable[str]:
        """
        Render a single named object CSV row.

        :param data: the named object
        :returns: the row iterator
        """
        yield from super().get_row(data)
        yield data.part.name
        yield str(data.minimum_units)
        if self.col_max is not None:
            yield str(data.maximum_units)

    def get_footer_comments(self) -> Iterable[str]:
        """
        Get the footer comments.

        :return: the footer comments
        """
        yield from super().get_footer_comments()
        yield f"{self.col_part}: the part for which the minimum is defined"
        if self.col_max is not None:
            yield (f"{self.col_max}: the goal number of part units to which"
                   f"we will order")
        yield f"{self.col_min}: the minimum number of part units required"
