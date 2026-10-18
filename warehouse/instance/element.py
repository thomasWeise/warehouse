"""
A class for identifying an element of our simulations.

Element objects are the basis for our model.
They are the base classes for bin types and parts as well as events.
All elements, i.e., subclasses of this class, such as instances of
:class:`~warehouse.instance.event.Event`,
:class:`~warehouse.instance.bin_type.BinType`, and
:class:`~warehouse.instance.part.Part`,
are immutable and hashable, too.

**Note** regarding the comparison functions: `<`, `<=`, `>`, and `>=` *only*
use the :attr:`~Element.key` attribute.
The same holds for the hash code returned by :func:`hash`.
This if for performance reasons, as sorting and priority-queueing usually only
use `<` comparisons and each element with a different key must also have a
different name anyway.

However, `==` and `!=` *also* use the :attr:`~Element.name` attribute.
This may be useful for comparing data across instances.

>>> with context():
...     e1 = Element(0, "A")
...     e2 = Element(None, "B")
...     e3 = Element(2, "C")
...     e4 = Element(None, "D")

>>> str(e1)
'Element0'
>>> str(e2)
'Element1'
>>> str(e3)
'Element2'
>>> str(e4)
'Element3'

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
from itertools import chain
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
from pycommons.types import check_int_range, check_to_int_range, type_error

#: the CSV key column
COLUMN_KEY: Final[str] = "key"
#: the CSV name column
COLUMN_NAME: Final[str] = "name"
#: the CSV column for everything concerning amounts
COLUMN_AMOUNT: Final[str] = "amount"

#: the multi-element separator
MULTI_SEPARATOR: Final[str] = "," if CSV_SEPARATOR != "," else ";"


def check_to_amount(amount: int | str) -> int:
    """
    Check an amount for validity.

    :param amount: the amount integer or string
    :return: the amount integer
    """
    return check_to_int_range(amount, "amount", 1, 1_000_000)


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
        'Element0'
        >>> str(b)
        'Element1'
        """
        return f"{self.__class__.__name__}{self.key}"

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
        return ((self.key == other.key) and (self.name == other.name)) \
            if isinstance(other, Element) else NotImplemented

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
        return ((self.key != other.key) or (self.name != other.name)) \
            if isinstance(other, Element) else NotImplemented

    @classmethod
    def to_csv(cls, data: Iterable[Self]) -> Iterable[str]:
        """
        Convert an iterable of the object to a CSV stream.

        :param data: the data
        :return: the stream
        """
        return CsvWriter.write(data=prepare_to_csv(data))

    @classmethod
    def from_csv(cls, rows: Iterable[str]) -> Iterable[Self]:
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


class context:
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
        Register an element and set its member variables.

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
        for chrx in f"{MULTI_SEPARATOR}{CSV_SEPARATOR}":
            if chrx in use_name:
                raise ValueError(f"Name of element {element!r} must not"
                                 f" contain {chrx!r}, but got {name!r}.")

        check_name: Final[str] = _process_name(use_name)
        if check_name in self.__elements_by_prepared_name:  # type: ignore
            raise ValueError(f"Element {element!r} with name {name!r} clashes"
                             f" with {check_name!r} that is already in use.")
        lst.append(element)
        self.__elements_by_prepared_name[check_name] = element  # type: ignore
        self.__elements_by_name[use_name] = element  # type: ignore
        object.__setattr__(element, "_hash", dict.__len__(
            self.__elements_by_name) - 1)  # type: ignore

    def resolve(self, cls: type[T], value: T | str | int) -> T:
        """
        Get the element of the given name and type.

        :param cls: the element class
        :param value: the value to be resolved

        :return: the element

        >>> class SubElement(Element):
        ...     pass

        >>> with context() as ctx:
        ...     a = Element(None, "hello")
        ...     b = SubElement(None, "world")
        ...     print(ctx.resolve(Element, "hello"))
        ...     print(ctx.resolve(Element, 0))
        ...     print(ctx.resolve(Element, a))
        ...     print(ctx.resolve(SubElement, "world"))
        ...     print(ctx.resolve(SubElement, b))
        ...     print(ctx.resolve(SubElement, 0))
        ...     print(ctx.resolve(Element, b))
        ...     print(ctx.resolve(Element, "world"))
        Element0
        Element0
        Element0
        SubElement0
        SubElement0
        SubElement0
        SubElement0
        SubElement0
        """
        if isinstance(value, cls):
            return value

        got: T | None = None
        if isinstance(value, str):
            got = self.__elements_by_name.get(value)  # type: ignore
            if got is None:
                got = self.__elements_by_prepared_name.get(  # type: ignore
                    _process_name(value))
                if got is None:
                    with suppress(ValueError):
                        value = int(value)
        if (got is None) and isinstance(value, int):
            for source in chain((cls, ),  # type: ignore
                                self.__element_lists.keys()):  # type: ignore
                if issubclass(source, cls):
                    with suppress(IndexError):
                        got = self.__element_lists[  # type: ignore
                            source][value]  # type: ignore
                        if got is not None:
                            break
        if got is None:
            raise ValueError(
                f"{cls.__name__} with name {value!r} does not exist.")
        if not isinstance(got, cls):
            raise TypeError(
                f"Expected {cls.__name__!r} element with name {value!r}"
                f", but got instance of {got.__class__.__name__!r} instead. ")
        return got

    def multi_resolve(self, cls: type[T], value: T | str | Iterable[
            T | str | int]) -> tuple[T, ...]:
        """
        Resolve several elements of a given type.

        :param cls: the class
        :param value: the raw value
        :return: the result of the resolution
        """
        if isinstance(value, cls):
            return (value, )
        dataset: Final[set[T]] = set()
        if isinstance(value, str):
            value = str.split(value, MULTI_SEPARATOR)
        if not isinstance(value, Iterable):
            raise type_error(value, "value", Iterable)
        for data in value:
            use: T = self.resolve(cls, data)  # type: ignore
            if use in dataset:
                raise ValueError(
                    f"Already encountered {data!r} as {use!r}.")
            dataset.add(use)
        return tuple(sorted(dataset))
