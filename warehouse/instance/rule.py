"""Classes containing rule information."""

from dataclasses import dataclass

from warehouse.instance.element import Element
from warehouse.instance.time import (
    check_timedelta,
    str_to_timedelta,
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
