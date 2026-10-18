"""A class for identifying a demand."""

from dataclasses import dataclass
from typing import Final, Iterable

from pycommons.io.csv import CsvReader as CsvReaderBase
from pycommons.io.csv import CsvWriter as CsvWriterBase
from pycommons.io.csv import csv_column, csv_scope

from warehouse.instance.checkpoint import COLUMN_CHECKPOINT, Checkpoint
from warehouse.instance.element import (
    COLUMN_AMOUNT,
    check_to_amount,
    context,
)
from warehouse.instance.part import COLUMN_PART, Part
from warehouse.instance.product import COLUMN_PRODUCT, Product
from warehouse.instance.time import (
    COLUMN_DELAY,
    check_timedelta,
    str_to_timedelta,
    timedelta_to_str,
)


@dataclass(frozen=True, init=False, order=True, eq=True)
class Demand:
    """A class for demands."""

    #: the product concerned
    product: Product
    #: the part
    part: Part
    #: the check point which triggers the natural demand
    checkpoint: Checkpoint
    #: the amount of time after the checkpoint where the part is needed
    delay: int
    #: the amount of part units required
    amount: int

    def __init__(self,
                 product: Product | int | str,
                 checkpoint: Checkpoint | int | str,
                 part: Part | int | str,
                 delay: int | str = 0,
                 amount: int | str = 1) -> None:
        """
        Create a new bin type.

        :param product: the product
        :param checkpoint: the checkpoint
        :param part: the part
        :param delay: the delay
        :param amount: the amount of part units
        """
        with context() as ctx:
            product = ctx.resolve(Product, product)
            part = ctx.resolve(Part, part)
            checkpoint = ctx.resolve(Checkpoint, checkpoint)
        object.__setattr__(self, "product", product)
        object.__setattr__(self, "checkpoint", checkpoint)
        object.__setattr__(self, "part", part)
        object.__setattr__(self, "delay", check_timedelta(
            delay) if isinstance(delay, int) else str_to_timedelta(delay))
        object.__setattr__(self, "amount", check_to_amount(amount))

    @classmethod
    def to_csv(cls, data: Iterable["Demand"]) -> Iterable[str]:
        """
        Convert an iterable of the object to a CSV stream.

        :param data: the data
        :return: the stream
        """
        return CsvWriter.write(data)

    @classmethod
    def from_csv(cls, rows: Iterable[str]) -> Iterable["Demand"]:
        """
        Get the data from CSV.

        :param rows: the rows
        :return: the sequence of objects
        """
        with context():
            yield from CsvReader.read(rows=rows, clazz=cls)


class CsvReader(CsvReaderBase[Demand]):
    """A CsvReader that reads demands from a CSV file."""

    def __init__(self, columns: dict[str, int]):
        """
        Initialize.

        :param columns: the named object columns
        """
        super().__init__(columns)

        #: the product key
        self.col_product: Final[int] = csv_column(
            columns, COLUMN_PRODUCT, True)
        #: the checkpoint key
        self.col_checkpoint: Final[int] = csv_column(
            columns, COLUMN_CHECKPOINT, True)
        #: the part key
        self.col_part: Final[int] = csv_column(columns, COLUMN_PART, True)
        #: the delay key
        self.col_delay: Final[int] = csv_column(
            columns, COLUMN_DELAY, True)
        #: the amount key
        self.col_amount: Final[int] = csv_column(
            columns, COLUMN_AMOUNT, True)

    def parse_row(self, data: list[str]) -> Demand:
        """
        Parse a data row.

        :param data: the data row
        :return: the instance
        """
        return Demand(product=data[self.col_product],
                      checkpoint=data[self.col_checkpoint],
                      part=data[self.col_part],
                      delay=data[self.col_delay],
                      amount=data[self.col_amount])


class CsvWriter(CsvWriterBase[Demand]):
    """Write the data to a csv file."""

    def __init__(self, data: Iterable[Demand],
                 scope: str | None = None) -> None:
        """
        Initialize the CSV writer.

        :param data: the data
        :param scope: the scope
        """
        super().__init__(data, scope)
        #: the product column
        self.col_product: Final[str] = csv_scope(scope, COLUMN_PRODUCT)
        #: the part column
        self.col_part: Final[str] = csv_scope(scope, COLUMN_PART)
        #: the checkpoint column
        self.col_checkpoint: Final[str] = csv_scope(scope, COLUMN_CHECKPOINT)
        #: the delay column
        self.col_delay: Final[str] = csv_scope(scope, COLUMN_DELAY)
        #: the amount column
        self.col_amount: Final[str] = csv_scope(scope, COLUMN_AMOUNT)

    def get_column_titles(self) -> Iterable[str]:
        """
        Get the column titles.

        :returns: the column titles
        """
        yield from super().get_column_titles()
        yield self.col_product
        yield self.col_checkpoint
        yield self.col_part
        yield self.col_delay
        yield self.col_amount

    def get_row(self, data: Demand) -> Iterable[str]:
        """
        Render a single named object  CSV row.

        :param data: the named object
        :returns: the row iterator
        """
        yield from super().get_row(data)
        yield data.product.name
        yield data.checkpoint.name
        yield data.part.name
        yield timedelta_to_str(data.delay)
        yield str(data.amount)

    def get_footer_comments(self) -> Iterable[str]:
        """
        Get the footer comments.

        :return: the footer comments
        """
        yield from super().get_footer_comments()
        yield f"{self.col_product}: the product name"
        yield f"{self.col_checkpoint}: the checkpoint name"
        yield f"{self.col_part}: the name of the part that will be required"
        yield (f"{self.col_delay}: the delay after the product reaches the "
               "checkpoint until the parts are required")
        yield (f"{self.col_amount}: the number of part units needed after "
               f"the {self.col_delay}")
