"""Classes containing rule information."""

from dataclasses import dataclass

from warehouse.instance.element import Element


@dataclass(frozen=True, init=False, order=False, eq=False)
class Rule(Element):
    """A class representing the basic rules in our simulation."""
