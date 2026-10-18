"""A class holding the information of a minimum rule."""

from dataclasses import dataclass
from typing import Final, Iterable, TypeVar, cast

from pycommons.io.csv import (
    csv_column,
    csv_scope,
    csv_val_or_none,
)

from warehouse.instance.element import CsvReader as CsvReaderBase
from warehouse.instance.element import CsvWriter as CsvWriterBase
from warehouse.instance.element import (
    check_to_amount,
    context,
    prepare_to_csv,
)
from warehouse.instance.part import COLUMN_PART, Part
from warehouse.instance.rule import COLUMN_EFFECT_DELAY, Rule
from warehouse.instance.time import (
    str_to_timedelta,
    timedelta_to_str,
)

#: the minimum column
COLUMN_MINIMUM: Final[str] = "minimum"


@dataclass(frozen=True, init=False, order=False, eq=False)
class MinRule(Rule):
    """A class for identifying a minimum rule."""

    #: the part which is concerned here
    part: Part
    #: the minimum value triggering the rule
    minimum: int

    def __init__(self, key: int | None, name: str,
                 part: Part | int | str,
                 minimum: int | str = 1,
                 effect_delay: int = 150 * 60 * 1000) -> None:
        """
        Create a new minimum rule.

        :param key: the rule key
        :param name: the rule name
        :param part: the part concerned by the rule
        :param minimum: the minimum value of that part
        :param effect_delay: the approximate delay after which the re-ordered
            material will arrive
        """
        super().__init__(key, name, effect_delay)
        if not isinstance(part, Part):
            with context() as ctx:
                part = ctx.resolve(Part, part)
        object.__setattr__(self, "part", part)
        object.__setattr__(self, "minimum", check_to_amount(minimum))

    def __eq__(self, other) -> bool:
        """
        Compare two parts for "equality".

        :param other: the other element
        :return: `True` if this element is equal, `False` otherwise
        """
        return (self.__class__ is other.__class__) and (
            self.key == other.key) and (self.name == other.name) and (
            self.part == other.part) and (self.minimum == other.minimum) and (
                self.effect_delay == other.effect_delay)

    def __ne__(self, other) -> bool:
        """
        Compare two parts for "not equal".

        :param other: the other element
        :return: `True` if this element is not equal, `False` otherwise
        """
        return (self.__class__ is not other.__class__) or (
            self.key != other.key) or (self.name != other.name) or (
            self.part != other.part) or (self.minimum != other.minimum) or (
                self.effect_delay != other.effect_delay)

    def __hash__(self) -> int:
        """
        Get the hash code of the minimum rule.

        :return: the hash code
        """
        return self._hash

    @classmethod
    def to_csv(cls,  # type: ignore
               data: Iterable["MinRule"]) -> Iterable[str]:  # type: ignore
        """
        Convert an iterable of the object to a CSV stream.

        :param data: the data
        :return: the stream
        """
        return CsvWriter[MinRule].write(  # type: ignore
            data=prepare_to_csv(data))  # type: ignore

    @classmethod
    def from_csv(cls, rows: Iterable[str]) -> Iterable["MinRule"]:
        """
        Get the data from CSV.

        :param rows: the rows
        :return: the sequence of objects
        """
        with context():
            yield from CsvReader[MinRule].read(rows=rows, clazz=cls)


#: the type variable for data to be written to CSV or to be read from CSV
T = TypeVar("T", bound="MinRule")


class CsvReader(CsvReaderBase[T]):
    """A CsvReader that reads named objects from a CSV file."""

    def __init__(self, columns: dict[str, int],
                 clazz: type[T] = cast("type[T]", Part)):
        """
        Initialize.

        :param columns: the named object columns
        """
        super().__init__(columns, clazz)
        #: the part column
        self.col_part: Final[int] = csv_column(columns, COLUMN_PART, True)
        #: the minimum column
        self.col_min: Final[int] = csv_column(columns, COLUMN_MINIMUM, True)
        #: the delay column
        self.col_delay: Final[int] = csv_column(
            columns, COLUMN_EFFECT_DELAY, True)

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
            minimum=check_to_amount(data[self.col_min]),
            effect_delay=str_to_timedelta(data[self.col_delay]))


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
        #: the delay column
        self.col_delay: Final[str] = csv_scope(scope, COLUMN_EFFECT_DELAY)

    def get_column_titles(self) -> Iterable[str]:
        """
        Get the column titles.

        :returns: the column titles
        """
        yield from super().get_column_titles()
        yield self.col_part
        yield self.col_min
        yield self.col_delay

    def get_row(self, data: T) -> Iterable[str]:
        """
        Render a single named object CSV row.

        :param data: the named object
        :returns: the row iterator
        """
        yield from super().get_row(data)
        yield data.part.name
        yield str(data.minimum)
        yield timedelta_to_str(data.effect_delay)

    def get_footer_comments(self) -> Iterable[str]:
        """
        Get the footer comments.

        :return: the footer comments
        """
        yield from super().get_footer_comments()
        yield f"{self.col_part}: the part for which the minimum is defined"
        yield f"{self.col_min}: the minimum number of parts required"
        yield (f"{self.col_delay}: the time until the rule's effects become "
               f"visible")
