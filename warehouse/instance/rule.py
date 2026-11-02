"""Classes containing rule information."""

from dataclasses import dataclass
from typing import Final, Iterable, TypeVar, cast

from pycommons.io.csv import (
    csv_column,
    csv_scope,
    csv_val_or_none,
)

from warehouse.instance.element import CsvReader as CsvReaderBase
from warehouse.instance.element import CsvWriter as CsvWriterBase
from warehouse.instance.element import Element
from warehouse.instance.time import (
    COLUMN_EFFECT_DELAY,
    check_timedelta,
    str_to_timedelta,
    timedelta_to_str,
)


@dataclass(frozen=True, init=False, order=False, eq=False)
class Rule(Element):
    """A class representing the basic rules in our simulation."""

    #: the delay after which the rule's effect will take place
    effect_delay: int

    def __init__(self, key: int | None, name: str,
                 effect_delay: int | str = 150 * 60 * 1000) -> None:
        """
        Create a new minimum rule.

        :param key: the rule key
        :param name: the rule name
        :param effect_delay: the approximate delay until the effect of the
            action triggered by the rule comes into effect
        """
        super().__init__(key, name)
        object.__setattr__(
            self, "effect_delay", check_timedelta(effect_delay) if isinstance(
                effect_delay, int) else str_to_timedelta(effect_delay))

    def __eq__(self, other) -> bool:
        """
        Compare two parts for "equality".

        :param other: the other element
        :return: `True` if this element is equal, `False` otherwise
        """
        return (self.__class__ is other.__class__) and (
            self.key == other.key) and (self.name == other.name) and (
                self.effect_delay == other.effect_delay)

    def __ne__(self, other) -> bool:
        """
        Compare two parts for "not equal".

        :param other: the other element
        :return: `True` if this element is not equal, `False` otherwise
        """
        return (self.__class__ is not other.__class__) or (
            self.key != other.key) or (self.name != other.name) or (
                self.effect_delay != other.effect_delay)

    def __hash__(self) -> int:
        """
        Get the hash code of the minimum rule.

        :return: the hash code
        """
        return self._hash


#: the type variable for data to be written to CSV or to be read from CSV
T = TypeVar("T", bound="Rule")


class CsvReader(CsvReaderBase[T]):
    """A CsvReader that reads named objects from a CSV file."""

    def __init__(self, columns: dict[str, int],
                 clazz: type[T] = cast("type[T]", Rule)):
        """
        Initialize.

        :param columns: the named object columns
        """
        super().__init__(columns, clazz)
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
        #: the delay column
        self.col_delay: Final[str] = csv_scope(scope, COLUMN_EFFECT_DELAY)

    def get_column_titles(self) -> Iterable[str]:
        """
        Get the column titles.

        :returns: the column titles
        """
        yield from super().get_column_titles()
        yield self.col_delay

    def get_row(self, data: T) -> Iterable[str]:
        """
        Render a single named object CSV row.

        :param data: the named object
        :returns: the row iterator
        """
        yield from super().get_row(data)
        yield timedelta_to_str(data.effect_delay)

    def get_footer_comments(self) -> Iterable[str]:
        """
        Get the footer comments.

        :return: the footer comments
        """
        yield from super().get_footer_comments()
        yield (f"{self.col_delay}: the time until the rule's effects become "
               f"visible")
