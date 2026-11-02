"""The warehouse JIT rule simulation."""
from collections import Counter
from typing import Callable, Final

from warehouse.event.checkpoint import CheckpointEvent
from warehouse.event.rules import JitRuleCheckEvent
from warehouse.instance.demand import Demand
from warehouse.instance.instance import Instance
from warehouse.instance.part import Part
from warehouse.rule.jit_rule import JitRule
from warehouse.simulation.module_demand import DemandModule


class JitModule(DemandModule):
    """The JIT part of the simulation."""

    def __init__(self, instance: Instance) -> None:
        """
        Create the JIT part of the simulation.

        :param instance: the scenario/instance to simulate
        """
        super().__init__(instance)

        jit_dict: Final[dict[int, JitRule]] = {
            jit.part.key: jit for jit in instance.jit_rules}
        #: the jit rules corresponding to parts
        self.__jit_rules: Final[tuple[JitRule | None, ...]] = tuple(
            jit_dict.get(i) for i in range(tuple.__len__(instance.parts)))
        #: whether we need to trigger jit rules for a given
        #: checkpoint/product combo
        self.__needs_jit: Final[tuple[tuple[bool, ...], ...]] = tuple(
            tuple(any(self.__jit_rules[dem.part.key] is not None
                      for dem in self.demands_cp_pd(cp.key)(prod.key))
                  for prod in instance.products)
            for cp in instance.checkpoints)

        #: the products that have passed a given check point
        self.__prod_past: Final[tuple[Counter[int], ...]] = tuple(
            Counter() for _ in range(tuple.__len__(instance.checkpoints))
        )

        #: the pending part orders
        self.__jit_pending: Final[list[int]] = [0] * tuple.__len__(
            instance.parts)
        #: the dict for the part orders, just a re-usable variable
        self.__part_orders: Final[Counter[int]] = Counter()
        #: should the jit rules be triggered?
        self.__trigger_jit: bool = False

    def _start(self) -> None:
        """Begin the simulation."""
        super()._start()
        for prod_past in self.__prod_past:
            prod_past.clear()
        self.__part_orders.clear()
        jp: Final[list[int]] = self.__jit_pending
        for i in range(list.__len__(jp)):
            jp[i] = 0
        self.__trigger_jit = False

    def _handle_checkpoint(self, event: CheckpointEvent) -> None:
        """
        Remove part from the warehouse.

        :param event: the event
        """
        cp: Final[int] = event.checkpoint.key
        prod: Final[int] = event.product.key
        if self.__needs_jit[cp][prod]:
            prod_past: Final[Counter[int]] = self.__prod_past[cp]
            prod_past[prod] += event.units
            if not self.__trigger_jit:
                self.__trigger_jit = True
                self._jit_check()

        super()._handle_checkpoint(event)

    def _handle_jit_check(self, event: JitRuleCheckEvent) -> None:
        """
        Handle the JIT rule checking event.

        :param event: the event
        """
        self.__trigger_jit = False
        orders: Final[Counter] = self.__part_orders
        demands_cp_pd: Final[Callable[[int], Callable[[
            int], tuple[Demand, ...]]]] = self.demands_cp_pd
        jits: Final[tuple[JitRule | None, ...]] = self.__jit_rules
        pending: Final[list[int]] = self.__jit_pending

        for cp, prod_past in enumerate(self.__prod_past):
            for prod, count in prod_past.items():
                for demand in demands_cp_pd(cp)(prod):
                    part = demand.part.key
                    if jits[part] is not None:
                        orders[part] += demand.units * count
            prod_past.clear()

        parts: Final[tuple[Part, ...]] = self.parts
        for part, units in orders.items():
            if units > 0:
                parto = parts[part]
                use_units = units + pending[part]
                packages, pending[part] = divmod(
                    use_units, parto.units_per_package)
                jit = jits[part]
                self._rule_triggered(0, jit, parto, use_units, packages)
                if packages > 0:
                    self._warehouse_in(jit.effect_delay, parto, packages)

        orders.clear()
