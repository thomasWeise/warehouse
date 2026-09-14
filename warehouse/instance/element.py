"""
A class for identifying an element.

Element objects are the basis for our model.
They are the base classes for bins and materials.

>>> with context():
...     e1 = Element(0, "A")
...     e2 = Element(None, "B")
...     e3 = Element(2, "C")
...     e4 = Element(None, "D")

>>> str(e1)
'E0'
>>> str(e2)
'E1'
>>> str(e3)
'E2'
>>> str(e4)
'E3'

>>> repr(e1)
"Element(key=0, name='A')"
>>> repr(e2)
"Element(key=1, name='B')"
>>> repr(e3)
"Element(key=2, name='C')"
>>> repr(e4)
"Element(key=3, name='D')"


>>> csv1 = list(Element.to_csv((e1, e2, e3, e4)))
>>> for txt in csv1[:-3]:
...     print(txt)
key;name
0;A
1;B
2;C
3;D
# key: the unique key of the element within its type
# name: the unique name of the element (unique over all elements of all types)

>>> for elem in Element.from_csv(csv1):
...     print(repr(elem))
Element(key=0, name='A')
Element(key=1, name='B')
Element(key=2, name='C')
Element(key=3, name='D')
"""

from contextlib import suppress
from dataclasses import dataclass, field
from typing import Final, Iterable, Self, TypeVar, cast

from pycommons.io.csv import (
    CSV_SEPARATOR,
    csv_column,
    csv_column_or_none,
    csv_scope,
    csv_val_or_none,
)
from pycommons.io.csv import CsvReader as CsvReaderBase
from pycommons.io.csv import CsvWriter as CsvWriterBase
from pycommons.types import check_int_range

#: the CSV key column
COLUMN_KEY: Final[str] = "key"
#: the CSV name column
COLUMN_NAME: Final[str] = "name"


@dataclass(frozen=True, init=False, order=False, eq=False)
class Element:
    """A class representing the basic elements of our simulation."""

    #: the internal object id
    key: int = field(init=False, repr=True, hash=False, compare=False)
    #: the name of the element
    name: str = field(init=False, repr=True, hash=False, compare=False)
    #: the unique hash key
    _hash: int = field(init=False, repr=False, hash=False, compare=False)

    def __init__(self, key: int | None, name: str):
        """
        Create a new element.

        :param key: the unique key identifying the object within its type
        :param name: the element name
        """
        with context() as ctx:
            ctx._create_element(self, key, name)  # type: ignore  # noqa

    def __hash__(self) -> int:
        """
        Get the hash code of the element.

        :return: the hash code

        >>> with context():
        ...     a = Element(None, "A")
        ...     b = Element(1, "B")

        >>> hash(a)
        0
        >>> hash(b)
        1
        """
        return self._hash

    def __str__(self) -> str:
        """
        Get the string representation of the element.

        :return: the string representation

        >>> with context():
        ...     a = Element(None, "A")
        ...     b = Element(1, "B")

        >>> str(a)
        'E0'
        >>> str(b)
        'E1'
        """
        return f"{self.__class__.__name__[0]}{self.key}"

    def __lt__(self, other) -> bool:
        """
        Compare two elements for "smaller".

        :param other: the other element
        :return: `True` if this element is less, `False` otherwise

        >>> with context():
        ...     a = Element(None, "A")
        ...     b = Element(1, "B")

        >>> a < b
        True
        >>> a < a
        False
        >>> b < b
        False
        >>> b < a
        False
        """
        return (self.key < other.key) if isinstance(other, Element) \
            else NotImplemented

    def __le__(self, other) -> bool:
        """
        Compare two elements for "smaller or equal".

        :param other: the other element
        :return: `True` if this element is less or equal, `False`
            otherwise

        >>> with context():
        ...     a = Element(None, "A")
        ...     b = Element(1, "B")

        >>> a <= b
        True
        >>> a <= a
        True
        >>> b <= b
        True
        >>> b <= a
        False
        """
        return (self.key <= other.key) if isinstance(other, Element) \
            else NotImplemented

    def __eq__(self, other) -> bool:
        """
        Compare two elements for "equality".

        :param other: the other element
        :return: `True` if this element is equal, `False` otherwise

        >>> with context():
        ...     a = Element(None, "A")
        ...     b = Element(1, "B")

        >>> a == b
        False
        >>> a == a
        True
        >>> b == b
        True
        >>> b == a
        False
        """
        return (self.key == other.key) if isinstance(other, Element) \
            else NotImplemented

    def __ge__(self, other) -> bool:
        """
        Compare two elements for "greater or equal".

        :param other: the other element
        :return: `True` if this element is greater or equal, `False`
            otherwise

        >>> with context():
        ...     a = Element(None, "A")
        ...     b = Element(1, "B")

        >>> a >= b
        False
        >>> a >= a
        True
        >>> b >= b
        True
        >>> b >= a
        True
        """
        return (self.key >= other.key) if isinstance(other, Element) \
            else NotImplemented

    def __gt__(self, other) -> bool:
        """
        Compare two elements for "greater".

        :param other: the other element
        :return: `True` if this element is greater, `False` otherwise

        >>> with context():
        ...     a = Element(None, "A")
        ...     b = Element(1, "B")

        >>> a > b
        False
        >>> a > a
        False
        >>> b > b
        False
        >>> b > a
        True
        """
        return (self.key > other.key) if isinstance(other, Element) \
            else NotImplemented

    def __ne__(self, other) -> bool:
        """
        Compare two elements for "not equal".

        :param other: the other element
        :return: `True` if this element is not equal, `False` otherwise

        >>> with context():
        ...     a = Element(None, "A")
        ...     b = Element(1, "B")

        >>> a != b
        True
        >>> a != a
        False
        >>> b != b
        False
        >>> b != a
        True
        """
        return (self.key != other.key) if isinstance(other, Element) \
            else NotImplemented

    @classmethod
    def to_csv(cls, data: Iterable["Element"]) -> Iterable[str]:
        """
        Convert an iterable of the object to a CSV stream.

        :param data: the data
        :return: the stream
        """
        return CsvWriter.write(data=prepare_to_csv(data))

    @classmethod
    def from_csv(cls, rows: Iterable[str]) -> Iterable["Element"]:
        """
        Get the data from CSV.

        :param rows: the rows
        :return: the sequence of objects
        """
        with context():
            yield from CsvReader.read(rows=rows, clazz=cls)   # type: ignore


#: the type variable for data to be written to CSV or to be read from CSV
T = TypeVar("T", bound="Element")


class CsvReader(CsvReaderBase[T]):
    """A CsvReader that reads named objects from a CSV file."""

    def __init__(self, columns: dict[str, int],
                 clazz: type[T] = cast("type[T]", Element)):
        """
        Initialize.

        :param columns: the named object columns
        """
        super().__init__(columns)
        #: the class function
        self.clazz: Final[type[T]] = clazz
        #: the key column is required
        self.col_key: Final[int | None] = csv_column_or_none(
            columns, COLUMN_KEY, True)
        #: the name column
        self.col_name: Final[int] = csv_column(columns, COLUMN_NAME, True)

    def parse_row(self, data: list[str]) -> T:
        """
        Parse a data row.

        :param data: the data row
        :return: the instance
        """
        return self.clazz(key=csv_val_or_none(
            data, self.col_key, int), name=data[self.col_name])


class CsvWriter(CsvWriterBase[T]):
    """Write the data to a csv file."""

    def __init__(self, data: Iterable[T], scope: str | None = None) -> None:
        """
        Initialize the CSV writer.

        :param data: the data
        :param scope: the scope
        """
        super().__init__(data, scope)
        #: the key column
        self.col_key: Final[str] = csv_scope(scope, COLUMN_KEY)
        #: column name
        self.col_name: Final[str] = csv_scope(scope, COLUMN_NAME)

    def get_column_titles(self) -> Iterable[str]:
        """
        Get the column titles.

        :returns: the column titles
        """
        yield self.col_key
        yield self.col_name

    def get_row(self, data: T) -> Iterable[str]:
        """
        Render a single element  CSV row.

        :param data: the element
        :returns: the row iterator
        """
        yield str(data.key)
        yield data.name

    def get_footer_comments(self) -> Iterable[str]:
        """
        Get the footer comments.

        :return: the footer comments
        """
        yield f"{self.col_key}: the unique key of the element within its type"
        yield (f"{self.col_name}: the unique name of the element (unique over "
               "all elements of all types)")


def prepare_to_csv(data: Iterable[Element]) -> Iterable[Element]:
    """
    Prepare an element stream for CSV output.

    :param data: the data
    :return: the prepared data stream
    """
    if isinstance(data, list):
        data.sort()
        return data
    return sorted(data)


#: the singleton attr name
_ATTR_NAME: Final[str] = "__context_instance"


def _process_name(name: str) -> str:
    """
    Process a name for lookup.

    :param name: the name
    :return: the processed name
    """
    return str.replace(str.lower(str.strip(name)), " ", "")


class ElementResolver:
    """The base class for element resolvers."""

    def resolve(self, cls: type[T], name_or_key: str | int) -> T:
        """
        Get the element of the given name and type.

        :param cls: the element class
        :param name_or_key: the element name or key

        :return: the element
        """
        raise NotImplementedError


class context(ElementResolver):
    """A context for constructing elements."""

    def __new__(cls) -> "context":  # noqa
        """Initialize the context manager."""
        if hasattr(cls, _ATTR_NAME):
            return getattr(cls, _ATTR_NAME)

        inst = super().__new__(cls)
        setattr(cls, _ATTR_NAME, inst)
        inst.__depth = 0  # type: ignore
        inst.__elements_by_name = {}  # type: ignore
        inst.__elements_by_prepared_name = {}  # type: ignore
        inst.__element_lists = {}  # type: ignore
        return inst

    def __enter__(self) -> Self:
        """
        Acquire the element construction context.

        :return: the element construction context
        """
        self.__depth += 1  # type: ignore
        return self

    def __exit__(self, exc_type, _, __) -> bool:
        """
        Leave the element construction context.

        :param exc_type: ignored
        :returns: `True` to suppress an exception, `False` to rethrow it
        """
        self.__depth -= 1  # type: ignore
        if self.__depth <= 0:  # type: ignore
            delattr(self.__class__, _ATTR_NAME)
        return exc_type is None

    def _create_element(self, element: Element,
                        key: int | None,
                        name: str) -> None:
        """
        Register an element and set its memeber variables.

        :param element: the element to register
        """
        use_name: Final[str] = str.strip(name)
        use_cls: Final[type] = element.__class__

        if use_cls not in self.__element_lists:  # type: ignore
            self.__element_lists[use_cls] = lst = []  # type: ignore
        else:
            lst = self.__element_lists[use_cls]  # type: ignore
        cls_key = list.__len__(lst)
        if key is None:
            key = cls_key
        object.__setattr__(element, "key", check_int_range(key, "key"))
        object.__setattr__(element, "name", use_name)

        if key != cls_key:
            raise ValueError(f"Element {element!r} should have "
                             f"key {cls_key} but has key {key}.")
        if str.__len__(use_name) < 1:
            raise ValueError(f"Name of element {element!r} cannot be empty, "
                             f"but got {name!r}.")
        if CSV_SEPARATOR in use_name:
            raise ValueError(f"Name of element {element!r} must not contain "
                             f" {CSV_SEPARATOR!r}, but got {name!r}.")

        check_name: Final[str] = _process_name(use_name)
        if check_name in self.__elements_by_prepared_name:  # type: ignore
            raise ValueError(f"Element {element!r} with name {name!r} clashes"
                             f" with {check_name!r} that is already in use.")
        lst.append(element)
        self.__elements_by_prepared_name[check_name] = element  # type: ignore
        self.__elements_by_name[use_name] = element  # type: ignore
        object.__setattr__(element, "_hash", dict.__len__(
            self.__elements_by_name) - 1)  # type: ignore

    def resolve(self, cls: type[T], name_or_key: str | int) -> T:
        """
        Get the element of the given name and type.

        :param cls: the element class
        :param name_or_key: the element name or key

        :return: the element
        """
        if isinstance(name_or_key, int):
            try:
                got = self.__element_lists[cls][name_or_key]  # type: ignore
            except IndexError as ie:
                raise ValueError(f"{cls.__name__} with key {name_or_key!r} "
                                 "does not exist.") from ie
        else:
            got = self.__elements_by_name.get(name_or_key)  # type: ignore
            if got is None:
                got = self.__elements_by_prepared_name.get(  # type: ignore
                    _process_name(name_or_key))
                if got is None:
                    with suppress(ValueError, IndexError):
                        got = self.__element_lists[cls][  # type: ignore
                            int(name_or_key)]
        if got is None:
            raise ValueError(
                f"{cls.__name__} with name {name_or_key!r} does not exist.")
        if cls is not got.__class__:
            raise TypeError(
                f"Expected {cls.__name__!r} element with name {name_or_key!r}"
                f", but got instance of {got.__class__.__name__!r} instead. ")
        return got
