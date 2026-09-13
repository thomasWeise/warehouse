"""
A class for identifying a named object.

Named objects are the basis for our model.
They are the base classes for bins and materials.

>>> m1 = Named(1, "test")
>>> str(m1)
'N1'

>>> repr(m1)
"Named(key=1, name='test')"

>>> m2 = Named(2)
>>> str(m2)
'N2'

>>> repr(m2)
'Named(key=2, name=None)'

>>> csv1 = list(Named.to_csv((m1, m2)))
>>> for txt in csv1[:-3]:
...     print(txt)
key;name
1;test
2
# key: the unique key identifying the object within its type
# name: the name of the object

>>> m3 = Named(3)
>>> str(m3)
'N3'

>>> csv2 = list(Named.to_csv((m3, m2)))
>>> for txt in csv2[:-3]:
...     print(txt)
key
2
3
# key: the unique key identifying the object within its type

>>> for obj in Named.from_csv(csv1):
...     print(repr(obj))
Named(key=1, name='test')
Named(key=2, name=None)

>>> for obj in Named.from_csv(csv2):
...     print(repr(obj))
Named(key=2, name=None)
Named(key=3, name=None)
"""

from dataclasses import dataclass
from typing import Final, Iterable, TypeVar, cast

from pycommons.io.csv import CsvReader as CsvReaderBase
from pycommons.io.csv import CsvWriter as CsvWriterBase
from pycommons.io.csv import (
    csv_column,
    csv_column_or_none,
    csv_scope,
    csv_str_or_none,
)
from pycommons.types import check_int_range, type_error

#: the CSV key column
KEY_KEY: Final[str] = "key"
#: the CSV name column
KEY_NAME: Final[str] = "name"


@dataclass(frozen=True, init=False, order=False, eq=False)
class Named:
    """
    A class representing a named object.

    >>> m = Named(1, "a")
    >>> m
    Named(key=1, name='a')
    >>> m.name
    'a'
    >>> m.key
    1

    >>> m = Named(2)
    >>> m
    Named(key=2, name=None)
    >>> print(m.name)
    None
    >>> m.key
    2
    """

    #: the named object id
    key: int

    #: the name of the named object
    name: str | None

    def __init__(self, key: int, name: str | None = None):
        """
        Create a new named object.

        :param key: the named object key
        :param name: the named object name
        """
        object.__setattr__(self, "key", check_int_range(key, "key"))
        if name is not None:
            name = str.strip(name)
            if str.__len__(name) < 1:
                raise ValueError("Mame must not be empty if specified.")
        object.__setattr__(self, "name", name)

    def __hash__(self) -> int:
        """
        Get the hash code of the named object.

        :return: the hash code

        >>> hash(Named(1))
        1

        >>> hash(Named(2, "b"))
        2
        """
        return self.key

    def __str__(self) -> str:
        """
        Get the string representation of the named object.

        :return: the string representation

        >>> str(Named(1))
        'N1'

        >>> str(Named(2, "x"))
        'N2'
        """
        return f"{self.__class__.__name__[0]}{self.key}"

    def __lt__(self, other) -> bool:
        """
        Compare two named objects for "smaller".

        :param other: the other named object
        :return: `True` if this named object is less, `False` otherwise

        >>> Named(1) < Named(2)
        True

        >>> Named(1) < Named(1)
        False

        >>> Named(2) < Named(1)
        False
        """
        return (self.key < other.key) if isinstance(other, Named) \
            else NotImplemented

    def __le__(self, other) -> bool:
        """
        Compare two named objects for "smaller or equal".

        :param other: the other named object
        :return: `True` if this named object is less or equal, `False`
            otherwise

        >>> Named(1) <= Named(2)
        True

        >>> Named(1) <= Named(1)
        True

        >>> Named(2) <= Named(1)
        False
        """
        return (self.key <= other.key) if isinstance(other, Named) \
            else NotImplemented

    def __eq__(self, other) -> bool:
        """
        Compare two named objects for "equality".

        :param other: the other named object
        :return: `True` if this named object is equal, `False` otherwise

        >>> Named(1) == Named(2)
        False

        >>> Named(1) == Named(1)
        True

        >>> Named(2) == Named(1)
        False
        """
        return (self.key == other.key) if isinstance(other, Named) \
            else NotImplemented

    def __ge__(self, other) -> bool:
        """
        Compare two named objects for "greater or equal".

        :param other: the other named object
        :return: `True` if this named object is greater or equal, `False`
            otherwise

        >>> Named(1) >= Named(2)
        False

        >>> Named(1) >= Named(1)
        True

        >>> Named(2) >= Named(1)
        True
        """
        return (self.key >= other.key) if isinstance(other, Named) \
            else NotImplemented

    def __gt__(self, other) -> bool:
        """
        Compare two named objects for "greater".

        :param other: the other named object
        :return: `True` if this named object is greater, `False` otherwise

        >>> Named(1) > Named(2)
        False

        >>> Named(1) > Named(1)
        False

        >>> Named(2) > Named(1)
        True
        """
        return (self.key > other.key) if isinstance(other, Named) \
            else NotImplemented

    def __ne__(self, other) -> bool:
        """
        Compare two named objects for "not equal".

        :param other: the other named object
        :return: `True` if this named object is not equal, `False` otherwise

        >>> Named(1) != Named(2)
        True

        >>> Named(1) != Named(1)
        False

        >>> Named(2) != Named(1)
        True
        """
        return (self.key != other.key) if isinstance(other, Named) \
            else NotImplemented

    @classmethod
    def to_csv(cls, data: Iterable["Named"]) -> Iterable[str]:
        """
        Convert an iterable of the object to a CSV stream.

        :param data: the data
        :return: the stream
        """
        return CsvWriter.write(data=_prepare_to_csv(data))

    @classmethod
    def from_csv(cls, rows: Iterable[str]) -> Iterable["Named"]:
        """
        Get the data from CSV.

        :param rows: the rows
        :return: the sequence of objects
        """
        return CsvReader.read(rows=rows, clazz=cls)   # type: ignore


#: the type variable for data to be written to CSV or to be read from CSV
T = TypeVar("T", bound="Named")


class CsvReader(CsvReaderBase[T]):
    """A CsvReader that reads named objects from a CSV file."""

    def __init__(self, columns: dict[str, int],
                 clazz: type[T] = cast("type[T]", Named)):
        """
        Initialize.

        :param columns: the named object columns
        """
        super().__init__(columns)
        #: the class function
        self.clazz: Final[type[T]] = clazz
        #: the key column is required
        self.col_key: Final[int] = csv_column(columns, KEY_KEY, True)
        #: the name column
        self.col_name: Final[int | None] = csv_column_or_none(
            columns, KEY_NAME, True)

    def parse_row(self, data: list[str]) -> T:
        """
        Parse a data row.

        :param data: the data row
        :return: the instance
        """
        return self.clazz(key=int(data[self.col_key]), name=csv_str_or_none(
            data, self.col_name))


class CsvWriter(CsvWriterBase[T]):
    """Write the data to a csv file."""

    def __init__(self, data: Iterable[T], scope: str | None = None) -> None:
        """
        Initialize the CSV writer.

        :param data: the data
        :param scope: the scope
        """
        super().__init__(data, scope)

        needs_name: bool = False
        i = -1
        for i, named in enumerate(data):
            if not isinstance(named, Named):
                raise type_error(named, f"data[{i}]", Named)
            if named.name is not None:
                needs_name = True
                break
        if i < 0:
            raise ValueError("Data is empty.")

        #: the key column
        self.col_key: Final[str] = KEY_KEY if scope is None else csv_scope(
            scope, KEY_KEY)
        #: column name
        self.col_name: Final[str | None] = (
            KEY_NAME if scope is None else csv_scope(
                scope, KEY_KEY)) if needs_name else None

    def get_column_titles(self) -> Iterable[str]:
        """
        Get the column titles.

        :returns: the column titles
        """
        yield self.col_key
        if self.col_name is not None:
            yield self.col_name

    def get_row(self, data: T) -> Iterable[str]:
        """
        Render a single named object  CSV row.

        :param data: the named object
        :returns: the row iterator
        """
        yield str(data.key)
        if self.col_name is not None:
            yield "" if data.name is None else data.name

    def get_footer_comments(self) -> Iterable[str]:
        """
        Get the footer comments.

        :return: the footer comments
        """
        yield (f"{self.col_key}: the unique key identifying the object "
               "within its type")
        if self.col_name is not None:
            yield f"{self.col_name}: the name of the object"


def _prepare_to_csv(data: Iterable[Named]) -> Iterable[Named]:
    """
    Prepare a named object stream for CSV output.

    :param data: the data
    :return: the prepared data stream
    """
    if isinstance(data, list):
        data.sort()
        return data
    return sorted(data)
