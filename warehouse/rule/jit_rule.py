"""A class holding the information of a jit rule."""

from dataclasses import dataclass
from typing import Final, Iterable, TypeVar, cast

from pycommons.io.csv import (
    csv_column,
    csv_scope,
    csv_val_or_none,
)

from warehouse.instance.element import (
    context,
)
from warehouse.instance.part import COLUMN_PART, Part
from warehouse.instance.rule import CsvReader as CsvReaderBase
from warehouse.instance.rule import CsvWriter as CsvWriterBase
from warehouse.instance.rule import Rule


@dataclass(frozen=True, init=False, order=False, eq=False)
class JitRule(Rule):
    """A class for identifying a JIT rule."""

    #: the part for which the rule triggers
    part: Part

    def __init__(self, key: int | None, name: str,
                 part: Part | int | str,
                 effect_delay: int | str = 150 * 60 * 1000) -> None:
        """
        Create a new minimum rule.

        :param key: the rule key
        :param name: the rule name
        :param part: the part concerned by the rule
        :param effect_delay: the approximate delay after which the re-ordered
            material will arrive
        """
        super().__init__(key, name, effect_delay)
        with context() as ctx:
            object.__setattr__(self, "part", ctx.resolve(Part, part))

    def __eq__(self, other) -> bool:
        """
        Compare two JIT rules for "equality".

        :param other: the other element
        :return: `True` if this element is equal, `False` otherwise
        """
        return (self.__class__ is other.__class__) and (
            self.key == other.key) and (self.name == other.name) and (
            self.part == other.part) and (
            self.effect_delay == other.effect_delay)

    def __ne__(self, other) -> bool:
        """
        Compare two JIT rules for "not equal".

        :param other: the other element
        :return: `True` if this element is not equal, `False` otherwise
        """
        return (self.__class__ is not other.__class__) or (
            self.key != other.key) or (self.name != other.name) or (
            self.part != other.part) or (
            self.effect_delay != other.effect_delay)

    def __hash__(self) -> int:
        """
        Get the hash code of the minimum rule.

        :return: the hash code
        """
        return self._hash

    @classmethod
    def to_csv(cls,  # type: ignore
               data: Iterable["JitRule"]) -> Iterable[str]:  # type: ignore
        """
        Convert an iterable of the object to a CSV stream.

        :param data: the data
        :return: the stream
        """
        return CsvWriter[JitRule].write(data)

    @classmethod
    def from_csv(cls, rows: Iterable[str]) -> Iterable["JitRule"]:
        """
        Get the data from CSV.

        :param rows: the rows
        :return: the sequence of objects
        """
        with context():
            yield from CsvReader[JitRule].read(rows=rows, clazz=cls)


#: the type variable for data to be written to CSV or to be read from CSV
T = TypeVar("T", bound="JitRule")


class CsvReader(CsvReaderBase[T]):
    """A CsvReader that reads named objects from a CSV file."""

    def __init__(self, columns: dict[str, int],
                 clazz: type[T] = cast("type[T]", JitRule)):
        """
        Initialize.

        :param columns: the named object columns
        """
        super().__init__(columns, clazz)
        #: the part column
        self.col_part: Final[int] = csv_column(
            columns, COLUMN_PART, True)

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

    def get_column_titles(self) -> Iterable[str]:
        """
        Get the column titles.

        :returns: the column titles
        """
        yield from super().get_column_titles()
        yield self.col_part

    def get_row(self, data: T) -> Iterable[str]:
        """
        Render a single named object CSV row.

        :param data: the named object
        :returns: the row iterator
        """
        yield from super().get_row(data)
        yield data.part.name

    def get_footer_comments(self) -> Iterable[str]:
        """
        Get the footer comments.

        :return: the footer comments
        """
        yield from super().get_footer_comments()
        yield f"{self.col_part}: the part for which the rule triggers"
