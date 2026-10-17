"""
Events regarding rules.

>>> from warehouse.instance.bin_type import BinType
>>> from warehouse.instance.part import Part
>>> from warehouse.rule.min_rule import MinRule
>>> with context():
...     BinType(None, "random_small", 1000, is_random=True)
...     BinType(None, "random_large", 500, is_random=True)
...     BinType(None, "hat_bins", 30)
...     Part(None, "hat", "hat_bins")
...     Part(None, "shoe", "random_small")
...     Part(None, "trousers", "random_large")
...     MinRule(None, "min_hat", "hat", 10, 100)
...     ev01 = RuleTriggeredEvent.create(1500000000000, 0, "min_hat", 1200)
...
...     events_1 = (ev01, )
...
...     for ev in events_1:
...         print(ev)
...
...     print()
...     print("===================")
...     print()
...
...     csv = list(Event.to_csv(events_1))
...     for row in csv[1:]:
...         if not str.startswith(row, "#"):
...             print(row)
...
...     print()
...     print("===================")
...     print()
...
...     events_2 = tuple(Event.from_csv(csv))
...     for ev in events_2:
...         print(ev)
BinType(key=0, name='random_small', amount=1000, is_random=True)
BinType(key=1, name='random_large', amount=500, is_random=True)
BinType(key=2, name='hat_bins', amount=30, is_random=False)
Part(key=0, name='hat', bin_type=BinType(key=2, name='hat_bins', amount=30, \
is_random=False))
Part(key=1, name='shoe', bin_type=BinType(key=0, name='random_small', \
amount=1000, is_random=True))
Part(key=2, name='trousers', bin_type=BinType(key=1, name='random_large', \
amount=500, is_random=True))
MinRule(key=0, name='min_hat', effect_delay=100, parts=(Part(key=0, \
name='hat', bin_type=BinType(key=2, name='hat_bins', amount=30, \
is_random=False)),), minimum=10)
RuleTriggeredEvent(time=1500000000000, priority=0, rule=MinRule(key=0, \
name='min_hat', effect_delay=100, parts=(Part(key=0, name='hat', \
bin_type=BinType(key=2, name='hat_bins', amount=30, is_random=False)),), \
minimum=10), amount=1200)
<BLANKLINE>
===================
<BLANKLINE>
2017-07-14 10:40;rule_triggered;;1200;;min_hat
<BLANKLINE>
===================
<BLANKLINE>
RuleTriggeredEvent(time=1500000000000, priority=0, rule=MinRule(key=0, \
name='min_hat', effect_delay=100, parts=(Part(key=0, name='hat', \
bin_type=BinType(key=2, name='hat_bins', amount=30, is_random=False)),), \
minimum=10), amount=1200)

>>> hash(ev01)
2467865476099009763
"""
from dataclasses import dataclass, field
from typing import Final

from warehouse.instance.element import (
    COLUMN_AMOUNT,
    check_to_amount,
    context,
)
from warehouse.instance.event import Event
from warehouse.instance.rule import Rule

#: the rule that was triggered, if any
COLUMN_RULE: Final[str] = "rule"


@dataclass(frozen=True, init=True, order=False, eq=False, unsafe_hash=True)
class RuleTriggeredEvent(Event):  # noqa: PLW1641
    """A rule was triggered."""

    #: the rule that was triggered
    rule: Rule = field(hash=True)
    #: the amount involved in the triggering
    amount: int | None = field(hash=True)

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
            self.rule == other.rule) and (
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
            self.rule != other.rule) or (
            self.amount != other.amount)

    @classmethod
    def eventclass_get_col_desc(cls, col: str) -> str | None:
        """
        Get the column description.

        :param col: the column
        :return: the event description, if any
        """
        if col == COLUMN_RULE:
            return "the name of the rule that was triggered"
        if col == COLUMN_AMOUNT:
            return "the amount involved in triggering the rule, if any"
        return None

    def event_get_csv_value(self, column: str) -> str:
        """
        Get a specific csv value.

        :param column: the csv column
        :return: the value
        """
        if column == COLUMN_RULE:
            return self.rule.name
        if column == COLUMN_AMOUNT:
            return "" if self.amount is None else str(self.amount)
        return ""

    @classmethod
    def eventclass_get_csv_columns(cls) -> tuple[str, ...]:
        """
        Get the CSV columns of the event.

        :return: the csv columns
        """
        return COLUMN_RULE, COLUMN_AMOUNT

    @classmethod
    def create(  # type: ignore  # pylint: disable=W0221
            cls, time: int, priority: int,
            rule: str | Rule,
            amount: int | str | None, **_) \
            -> "RuleTriggeredEvent":  # type: ignore
        """
        Create the storage event.

        :param time: the time
        :param priority: the event priority
        :param rule: the rule involved
        :param amount: the amount of the part to use
        :return: the storage event
        """
        if not isinstance(rule, Rule):
            with context() as ctx:
                rule = ctx.resolve(Rule, rule)
        return cls(time, priority, rule,  # type: ignore
                   None if amount is None else  # type: ignore
                   check_to_amount(amount))  # type: ignore

    @classmethod
    def eventclass_get_csv_type(cls) -> str:
        """
        Get the csv type of the event.

        :return: the csv type
        """
        return "rule_triggered"

    @classmethod
    def eventclass_get_event_desc(cls) -> str | None:
        """
        Get the event description.

        :return: the event description, if any
        """
        return (f"The rule of the given {COLUMN_RULE} was triggered. "
                f"It may be parameterized with the given {COLUMN_AMOUNT}.")
