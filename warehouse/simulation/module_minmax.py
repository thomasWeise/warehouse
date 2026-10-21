"""The warehouse min-max rule simulation."""
from heapq import heapify, heappop, heappush
from typing import Callable, Final

from warehouse.event.rules import RuleTriggeredEvent
from warehouse.event.storage import (
    WarehouseDemand,
    WarehouseIn,
)
from warehouse.event.time import InitializationComplete
from warehouse.instance.instance import Instance
from warehouse.instance.part import Part
from warehouse.rule.min_rule import MinRule
from warehouse.simulation.module_storage import StorageModule


class MinMaxModule(StorageModule):
    """The min-max part of the simulation."""

    def __init__(self, instance: Instance) -> None:
        """
        Create the min/max part of the simulation.

        :param instance: the scenario/instance to simulate
        """
        super().__init__(instance)

        n_parts: Final[int] = tuple.__len__(self._parts)

        #: the parts already ordered by the min/max rules
        self.__mm_on_the_way: Final[tuple[list[WarehouseIn], ...]] = tuple(
            [] for _ in range(n_parts))
        rule_dict: dict[int, MinRule] = {
            rule.part.key: rule for rule in instance.min_rules}
        #: the minimum rules
        self.__mm_min: Final[tuple[MinRule | None, ...]] = tuple(
            rule_dict.get(k) for k in range(n_parts))

    def _start(self) -> None:
        """Begin the simulation."""
        super()._start()
        for queue in self.__mm_on_the_way:
            list.clear(queue)

    def _handle_initizalization_complete(
            self, event: InitializationComplete) -> None:
        """
        Handle the event denoting the completion of the initialization.

        :param event: the event
        """
        time: int = event.time

        for part in self._parts:
            part_key = part.key
            min_rule: MinRule | None = self.__mm_min[part_key]

            if min_rule is not None:
                otw: list[WarehouseIn] = self.__mm_on_the_way[part_key]
                remaining: int = self.available_units(part)
                trigger: int = min_rule.minimum - remaining
                if trigger > 0:
                    self.enqueue(RuleTriggeredEvent(
                        time, self._priority(), min_rule, part, trigger))
                    request: WarehouseIn = WarehouseIn(
                        time + min_rule.effect_delay, self._priority(),
                        part, trigger)
                    self.enqueue(request)
                    _put_one_the_way(otw, request)

    def _handle_warehouse_demand(self, event: WarehouseDemand) -> None:
        """
        Remove part from the warehouse.

        :param event: the event
        """
        part: Final[Part] = event.part
        part_key: Final[int] = part.key
        min_rule: Final[MinRule | None] = self.__mm_min[part_key]

        if min_rule is not None:
            otw: Final[list[WarehouseIn]] = self.__mm_on_the_way[part_key]
            remaining: Final[int] = self.available_units(
                part) + _get_on_the_way(otw) - event.amount
            trigger: Final[int] = min_rule.minimum - remaining
            if trigger > 0:
                time: Final[int] = event.time
                self.enqueue(RuleTriggeredEvent(
                    time, self._priority(), min_rule, part, trigger))
                request: Final[WarehouseIn] = WarehouseIn(
                    time + min_rule.effect_delay, self._priority(),
                    part, trigger)
                self.enqueue(request)
                _put_one_the_way(otw, request)

        super()._handle_warehouse_demand(event)

    def _handle_warehouse_in(self, event: WarehouseIn) -> None:
        """
        Put newly arrived parts into the warehouse.

        :param event: the event
        """
        _purge_on_the_way(self.__mm_on_the_way[event.part.key], event)
        super()._handle_warehouse_in(event)


def _get_on_the_way(otw: list[WarehouseIn]) -> int:
    """
    Get the amount of parts on the way.

    :param otw: the on-the-way list
    :return: the amount of parts on the way
    """
    return sum(ev.amount for ev in otw)


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
