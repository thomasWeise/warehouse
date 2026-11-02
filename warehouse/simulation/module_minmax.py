"""The warehouse min-max rule simulation."""
from heapq import heapify, heappop, heappush
from typing import Callable, Final, Iterable

from warehouse.event.rules import MinMaxRuleCheckEvent
from warehouse.event.storage import (
    WarehouseDemand,
    WarehouseIn,
)
from warehouse.event.time import InitializationComplete
from warehouse.instance.instance import Instance
from warehouse.instance.part import Part
from warehouse.rule.minmax_rule import MinMaxRule
from warehouse.simulation.module_storage import StorageModule


class MinMaxModule(StorageModule):
    """The min-max part of the simulation."""

    def __init__(self, instance: Instance) -> None:
        """
        Create the min/max part of the simulation.

        :param instance: the scenario/instance to simulate
        """
        super().__init__(instance)

        n_parts: Final[int] = tuple.__len__(self.parts)

        #: the parts already ordered by the min/max rules
        self.__mm_on_the_way: Final[tuple[list[WarehouseIn], ...]] = tuple(
            [] for _ in range(n_parts))
        rule_dict: dict[int, MinMaxRule] = {
            rule.part.key: rule for rule in instance.minmax_rules}
        #: the minimum rules
        self.__mm_min: Final[tuple[MinMaxRule | None, ...]] = tuple(
            rule_dict.get(k) for k in range(n_parts))
        #: has a rule check already been requested?
        self.__check_requested: bool = False
        #: the set of product IDs requiring rule checks
        self.__check_rules: Final[set[int]] = set()

    def _start(self) -> None:
        """Begin the simulation."""
        super()._start()
        self.__check_requested = False
        self.__check_rules.clear()
        for queue in self.__mm_on_the_way:
            list.clear(queue)

    def __check_min_max_rules(self, parts: Iterable[int]) -> None:
        """
        Check all the min-max rules for the given parts.

        :param parts: the parts to check
        """
        pks: Final[tuple[Part, ...]] = self.parts
        mm_min: Final[tuple[MinMaxRule | None, ...]] = self.__mm_min
        for part_key in parts:
            part = pks[part_key]
            min_rule: MinMaxRule | None = mm_min[part_key]
            if min_rule is not None:
                otw: list[WarehouseIn] = self.__mm_on_the_way[part_key]
                remaining: int = (self.available_packages(
                    part) + _get_on_the_way(otw)) * part.units_per_package
                if min_rule.minimum_units > remaining:
                    units = min_rule.maximum_units - remaining
                    packages = max(1, units // part.units_per_package)
                    self._rule_triggered(0, min_rule, part, units, packages)
                    _put_one_the_way(otw, self._warehouse_in(
                        min_rule.effect_delay, part, packages))

    def _handle_initizalization_complete(
            self, event: InitializationComplete) -> None:
        """
        Handle the event denoting the completion of the initialization.

        :param event: the event
        """
        self.__check_min_max_rules(p.key for p in self.parts)

    def _handle_warehouse_demand(self, event: WarehouseDemand) -> None:
        """
        Remove part from the warehouse.

        :param event: the event
        """
        part: Final[Part] = event.part
        part_key: Final[int] = part.key
        min_rule: Final[MinMaxRule | None] = self.__mm_min[part_key]

        if min_rule is not None:
            otw: Final[list[WarehouseIn]] = self.__mm_on_the_way[part_key]
            remaining: Final[int] = ((self.available_packages(
                part) + _get_on_the_way(otw) - event.packages)
                * part.units_per_package)
            trigger: Final[int] = min_rule.minimum_units - remaining
            if trigger > 0:
                self.__check_rules.add(part_key)
                if not self.__check_requested:
                    self.__check_requested = True
                    self._minmax_check()
        super()._handle_warehouse_demand(event)

    def _handle_minmax_check(self, event: MinMaxRuleCheckEvent) -> None:
        """
        Handle the min/max rule checking event.

        :param event: the event
        """
        self.__check_requested = False
        self.__check_min_max_rules(sorted(self.__check_rules))
        self.__check_rules.clear()

    def _handle_warehouse_in(self, event: WarehouseIn) -> None:
        """
        Put newly arrived parts into the warehouse.

        :param event: the event
        """
        _purge_on_the_way(self.__mm_on_the_way[event.part.key], event)
        super()._handle_warehouse_in(event)


def _get_on_the_way(otw: list[WarehouseIn]) -> int:
    """
    Get the packages of parts on the way.

    :param otw: the on-the-way list
    :return: the amount of packages of the part on the way
    """
    return sum(ev.packages for ev in otw)


def _purge_on_the_way(otw: list[WarehouseIn],
                      event: WarehouseIn) -> None:
    """
    Purge an event from the on-the-way queue.

    :param otw: the queue
    :param event: the event
    """
    if not otw:
        return
    if event is otw[0]:
        heappop(otw)
        return
    for idx, ev in enumerate(otw):
        if ev is event:
            del otw[idx]
            heapify(otw)
            return


#: we can directly reference the heappush function here.
_put_one_the_way: Final[Callable[[
    list[WarehouseIn], WarehouseIn], None]] = heappush
