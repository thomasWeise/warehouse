"""The warehouse JIT rule simulation."""
from typing import Callable, Final

from warehouse.event.checkpoint import CheckpointEvent
from warehouse.event.storage import (
    WarehouseIn,
)
from warehouse.instance.instance import Instance
from warehouse.instance.part import Part
from warehouse.rule.jit_rule import JitRule
from warehouse.simulation.module_demand import DemandModule, _flatten_cp
from warehouse.simulation.module_minmax import (
    _get_on_the_way,
    _purge_on_the_way,
    _put_one_the_way,
)


class JitModule(DemandModule):
    """The JIT part of the simulation."""

    def __init__(self, instance: Instance) -> None:
        """
        Create the JIT part of the simulation.

        :param instance: the scenario/instance to simulate
        """
        super().__init__(instance)

        raw: Final[dict[int, dict[int, list[JitRule]]]] = {}
        for checkpoint in instance.checkpoints:
            use: dict[int, list[JitRule]] = {}
            raw[checkpoint.key] = use
            for product in instance.products:
                use[product.key] = []
        for jit in instance.jit_rules:
            raw[jit.checkpoint.key][jit.product.key].append(jit)

        #: the JIT rule lookup
        self.__jit: Final[Callable[[int], Callable[[
            int], tuple[JitRule, ...]]]] = _flatten_cp(raw)
        #: the parts already ordered by the min/max rules
        self.__jit_on_the_way: Final[tuple[list[WarehouseIn], ...]] = tuple(
            [] for _ in range(tuple.__len__(instance.parts)))

    def _start(self) -> None:
        """Begin the simulation."""
        super()._start()
        for queue in self.__jit_on_the_way:
            list.clear(queue)

    def _handle_checkpoint(self, event: CheckpointEvent) -> None:
        """
        Remove part from the warehouse.

        :param event: the event
        """
        for jit_rule in self.__jit(event.checkpoint.key)(event.product.key):
            part: Part = jit_rule.part
            part_key: int = jit_rule.part.key
            otw: list[WarehouseIn] = self.__jit_on_the_way[part_key]
            remaining: int = (self.available_packages(
                part) + _get_on_the_way(otw)) * part.units_per_package
            units: int = jit_rule.minimum_units - remaining
            if units > 0:
                packages = units // part.units_per_package
                self._rule_triggered(0, jit_rule, part, units, packages)
                if packages > 0:
                    _put_one_the_way(otw, self._warehouse_in(
                        jit_rule.effect_delay, part, packages))

        super()._handle_checkpoint(event)

    def _handle_warehouse_in(self, event: WarehouseIn) -> None:
        """
        Put newly arrived parts into the warehouse.

        :param event: the event
        """
        _purge_on_the_way(self.__jit_on_the_way[event.part.key], event)
        super()._handle_warehouse_in(event)
