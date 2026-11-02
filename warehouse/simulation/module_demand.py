"""The warehouse module implementing demand."""
from typing import Any, Callable, Final

from warehouse.event.checkpoint import CheckpointEvent
from warehouse.instance.demand import Demand
from warehouse.instance.instance import Instance
from warehouse.instance.part import Part
from warehouse.simulation.module_minmax import MinMaxModule


class DemandModule(MinMaxModule):
    """The demand part of the simulation."""

    def __init__(self, instance: Instance) -> None:
        """
        Create the min/max part of the simulation.

        :param instance: the scenario/instance to simulate
        """
        super().__init__(instance)

        raw: Final[dict[int, dict[int, list[Demand]]]] = {}
        for checkpoint in instance.checkpoints:
            use: dict[int, list[Demand]] = {}
            raw[checkpoint.key] = use
            for product in instance.products:
                use[product.key] = []
        for demand in instance.demands:
            raw[demand.checkpoint.key][demand.product.key].append(demand)

        #: the demand lookup
        self.demands_cp_pd: Final[Callable[[int], Callable[[
            int], tuple[Demand, ...]]]] = _flatten_cp(raw)
        #: the pending demands
        self.__pending_dems: Final[list[int]] = [0] * tuple.__len__(
            instance.parts)

    def _start(self) -> None:
        """Begin the simulation."""
        super()._start()
        dems: Final[list[int]] = self.__pending_dems
        for i in range(list.__len__(dems)):
            dems[i] = 0

    def _handle_checkpoint(self, event: CheckpointEvent) -> None:
        """
        Handle that an amount of a given product has reached a checkpoint.

        :param event: the event
        """
        dms: Final[list[int]] = self.__pending_dems
        units: Final[int] = event.units
        for demand in self.demands_cp_pd(
                event.checkpoint.key)(event.product.key):
            part: Part = demand.part
            packs, dms[part.key] = divmod(dms[part.key] + (
                units * demand.units), part.units_per_package)
            if packs > 0:
                self._warehouse_demand(demand.delay, part, packs)


def __empty(_: Any) -> tuple:
    """
    Get an empty tuple.

    :param _: ignored
    :return: the empty tuple
    """
    return ()


def __empty2(_) -> Callable[[Any], tuple]:
    """
    Get an empty 2 tuple.

    :param _: ignored
    :return: the empty tuple
    """
    return __empty


def _flatten_cp(data: dict) -> Callable[[int], Callable[[int], tuple]]:
    """
    Convert a map to a double-callable.

    :param data: the data map
    :return: the function
    """
    has_any: bool = False
    for key, value in data.items():
        has: bool = False
        for kk, vv in value.items():
            if list.__len__(vv) > 0:
                has = True
            value[kk] = tuple(vv)
        if has:
            data[key] = value.__getitem__
            has_any = True
        else:
            data[key] = __empty
    return data.__getitem__ if has_any else __empty2
