"""Events regarding the checkpoints."""
from dataclasses import dataclass, field

from warehouse.instance.checkpoint import COLUMN_CHECKPOINT, Checkpoint
from warehouse.instance.element import COLUMN_AMOUNT, check_to_amount, context
from warehouse.instance.event import Event
from warehouse.instance.product import COLUMN_PRODUCT, Product


@dataclass(frozen=True, init=True, order=False, eq=False, unsafe_hash=True)
class CheckpointEvent(Event):  # noqa: PLW1641
    """An amount of product has reached a certain checkpoint."""

    #: the checkpoint
    checkpoint: Checkpoint = field(hash=True)
    #: the product
    product: Product = field(hash=True)
    #: the amount to store/retrieve
    amount: int = field(hash=True)

    def __eq__(self, other) -> bool:
        """
        Compare this event with another event object for "equality".

        :param other: the other event
        :return: `True` if this event is equal to the other event,
            `False` otherwise
        """
        return (self.__class__ is other.__class__) and (
            self.time == other.time) and (
            self.priority == other.priority) and (
            self.checkpoint == other.checkpoint) and (
            self.product == other.product) and (
            self.amount == other.amount)

    def __ne__(self, other) -> bool:
        """
        Compare this event with another event object for "inequality".

        :param other: the other event
        :return: `True` if this event is not equal than the other event,
            `False` otherwise
        """
        return (self.__class__ is not other.__class__) or (
            self.time != other.time) or (
            self.priority != other.priority) or (
            self.checkpoint != other.checkpoint) or (
            self.product != other.product) or (
            self.amount != other.amount)

    @classmethod
    def eventclass_get_col_desc(cls, col: str) -> str | None:
        """
        Get the column description.

        :param col: the column
        :return: the event description, if any
        """
        if col == COLUMN_CHECKPOINT:
            return "the checkpoint that was reached"
        if col == COLUMN_PRODUCT:
            return "the product that reached the checkpoint"
        if col == COLUMN_AMOUNT:
            return ("the amount of product that reached the checkpoint, "
                    "usually 1")
        return None

    def event_get_csv_value(self, column: str) -> str:
        """
        Get a specific csv value.

        :param column: the csv column
        :return: the value
        """
        if column == COLUMN_CHECKPOINT:
            return self.checkpoint.name
        if column == COLUMN_PRODUCT:
            return self.product.name
        if column == COLUMN_AMOUNT:
            return str(self.amount)
        return ""

    @classmethod
    def eventclass_get_csv_columns(cls) -> tuple[str, ...]:
        """
        Get the CSV columns of the event.

        :return: the csv columns
        """
        return COLUMN_CHECKPOINT, COLUMN_PRODUCT, COLUMN_AMOUNT

    @classmethod
    def create(  # type: ignore  # pylint: disable=W0221
            cls, time: int, priority: int,
            checkpoint: int | str | Checkpoint,
            product: int | str | Product,
            amount: int | str | None, **_) \
            -> "CheckpointEvent":  # type: ignore
        """
        Create the checkpoint event.

        :param time: the time
        :param priority: the event priority
        :param checkpoint: the checkpoint that was reached
        :param product: the product that reached the checkpoint
        :param amount: the amount of the product reaching the checkpoint
        :return: the checkpoint event
        """
        with context() as ctx:
            checkpoint = ctx.resolve(Checkpoint, checkpoint)
            product = ctx.resolve(Product, product)
        return cls(time, priority, checkpoint, product,  # type: ignore
                   1 if amount is None else  # type: ignore
                   check_to_amount(amount))  # type: ignore

    @classmethod
    def eventclass_get_csv_type(cls) -> str:
        """
        Get the csv type of the event.

        :return: the csv type
        """
        return "checkpoint"

    @classmethod
    def eventclass_get_event_desc(cls) -> str | None:
        """
        Get the event description.

        :return: the event description, if any
        """
        return (f"a certain {COLUMN_AMOUNT} (usually 1) of a {COLUMN_PRODUCT}"
                f" has reached a {COLUMN_CHECKPOINT}")
