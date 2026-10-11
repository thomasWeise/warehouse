"""The warehouse simulation."""

from array import array
from heapq import heapify, heappop, heappush
from typing import Callable, Final, Generator, Iterable

from pycommons.types import type_error

from warehouse.event.bins import BinEvent, BinIn, BinOut
from warehouse.event.storage import (
    InsufficientMaterial,
    OverstockIn,
    OverstockOut,
    StorageEvent,
    WarehouseIn,
    WarehouseOut,
)
from warehouse.event.time import (
    EndEvent,
    StartEvent,
)
from warehouse.instance.bin_type import BinType
from warehouse.instance.event import Event
from warehouse.instance.instance import Instance
from warehouse.instance.material import Material
from warehouse.instance.time import EARLIEST_START, LATEST_END


class Simulation:
    """A warehouse simulation."""

    def __init__(self, instance: Instance) -> None:
        """
        Create the simulation.

        :param instance: the scenario/instance to simulate
        """
        if not isinstance(instance, Instance):
            raise type_error(instance, "instance", Instance)

        #: the instance we are simulating
        self.instance: Final[Instance] = instance
        #: the time index
        self.time: int = EARLIEST_START

        #: the internal queue
        self.__queue: Final[list[Event]] = []

        #: the amount of materials currently in overstock
        self.__in_overstock: Final[array[int]] = array(
            "q", [0] * instance.n_materials)
        #: the empty bins of the given types
        self.__empty_bins: Final[array[int]] = array(
            "q", [0] * instance.n_bin_types)
        #: the amount of the material currently inside bins
        self.__in_bins: Final[array[int]] = array(
            "q", self.__in_overstock)

        use_material: Final[Material] = instance.materials[0]
        use_bin_type: Final[BinType] = instance.bin_types[0]

        #: the shared BinIn event
        self.__bin_in: Final[BinIn] = BinIn(
            EARLIEST_START, use_material, 1, use_bin_type)
        #: the shared BinOut event
        self.__bin_out: Final[BinOut] = BinOut(
            EARLIEST_START, use_material, 1, use_bin_type)
        #: the shared overstock in event
        self.__overstock_in: Final[OverstockIn] = OverstockIn(
            EARLIEST_START, use_material, 1)
        #: the shared overstock out event
        self.__overstock_out: Final[OverstockOut] = OverstockOut(
            EARLIEST_START, use_material, 1)
        #: the shared insufficient event
        self.__insufficient: Final[InsufficientMaterial] = \
            InsufficientMaterial(EARLIEST_START, use_material, 1)
        #: the bins
        self.__bin_types: Final[tuple[BinType, ...]] = instance.bin_types

    def __start(self) -> None:
        """Begin the simulation."""
        ios: Final[array[int]] = self.__in_overstock
        ib: Final[array[int]] = self.__in_bins
        eb: Final[array[int]] = self.__empty_bins
        bts: Final[tuple[BinType, ...]] = self.__bin_types

        for i in range(array.__len__(ios)):
            ios[i] = 0
            ib[i] = 0

        for i in range(array.__len__(eb)):
            eb[i] = bts[i].amount

        queue: Final[list[Event]] = self.__queue
        queue.clear()
        queue.extend(self.instance.events)
        heapify(queue)
        self.time = EARLIEST_START

    def simulate(self) -> Generator[Event, None, None]:
        """
        Run the simulation.

        :return: the sequence of events.
        """
        self.__start()

        queue: Final[list[Event]] = self.__queue
        if list.__len__(queue) <= 0:
            yield StartEvent(self.time)
        elif queue[0].__class__ is not StartEvent:
            self.time = queue[0].time
            yield StartEvent(queue[0].time)

        router: Final = _EVENT_ROUTER
        quitter = _QUIT
        end_event: Event | None = None
        end_time: int = LATEST_END
        while queue:
            event: Event = heappop(queue)
            self.time = time = event.time

            eid = id(event.__class__)
            if eid == quitter:
                end_event = event
                end_time = time
                continue
            if time > end_time:
                break
            yield from router(eid)(self, event)

        queue.clear()
        yield end_event if end_event is not None else EndEvent(self.time)

    def enqueue(self, event: Event) -> None:
        """
        Add an event to the simulation's event queue.

        :param event: the event to add
        """
        heappush(self.__queue, event)

    def _forward(self, event: Event) -> Generator[
            Event, None, None]:
        """
        Ignore this kind of event and just forward it directly.

        :param event: the event
        """
        yield event

    def _error(self, event: Event) -> None:
        """
        Handle an event that is not permitted.

        :param event: the event
        """
        raise ValueError(
            f"An event has occurred in the input event stream of a simulation"
            f" at time {self.time} that is not permitted: {event!r}. Such "
            f"events can only be generated by the simulation (as output) but "
            f"you cannot trigger them by yourself as input to the "
            f"simulation.")

    def _warehouse_in(self, event: WarehouseIn) -> Generator[
            Event, None, None]:
        """
        Store material into the warehouse.

        :param event: the event with the information about the material
            to be stored
        :return: the event stream
        """
        yield event

        material: Final[Material] = event.material
        mat_key: Final[int] = material.key
        bin_type: Final[BinType] = material.bin_type
        bin_key: Final[int] = bin_type.key
        amount: int = event.amount
        empty: Final[array[int]] = self.__empty_bins
        in_bin: Final[array[int]] = self.__in_bins

        use: int = min(empty[bin_key], amount)
        if use > 0:
            bin_in: Final[BinIn] = self.__bin_in
            bin_in.material = material
            bin_in.bin_type = bin_type
            bin_in.amount = use
            empty[bin_key] -= use
            in_bin[mat_key] += use
            yield bin_in
            amount -= use
            if amount <= 0:
                return

        self.__in_overstock[mat_key] += amount
        over_in: Final[OverstockIn] = self.__overstock_in
        over_in.material = material
        over_in.amount = amount
        yield over_in

    def _warehouse_out(self, event: WarehouseOut) -> Generator[
            Event, None, None]:
        """
        Remove material from the warehouse.

        :param event: the event
        """
        material: Final[Material] = event.material
        mat_key: Final[int] = material.key
        bin_type: Final[BinType] = material.bin_type
        bin_key: Final[int] = bin_type.key
        amount: int = event.amount

        empty: Final[array[int]] = self.__empty_bins
        in_bin: Final[array[int]] = self.__in_bins
        in_over: Final[array[int]] = self.__in_overstock

        bin_out: Final[BinOut] = self.__bin_out
        bin_out.material = material
        bin_out.bin_type = bin_type

        has_over = in_over[mat_key]
        has_bin = in_bin[mat_key]
        has_empty = empty[bin_key]

        while amount > 0:
            use = min(has_bin, amount)
            if use <= 0:
                ins: InsufficientMaterial = self.__insufficient
                ins.material = material
                ins.amount = amount
                yield ins

                event = event.copy()
                event.amount = amount
                break

            amount -= use
            bin_out.amount = use
            has_bin -= use
            in_bin[mat_key] = has_bin
            has_empty += use
            empty[bin_key] = has_empty
            yield bin_out

            if has_over > 0:
                use = min(has_empty, has_over)
                has_over -= use
                in_over[mat_key] = has_over

                over_out = self.__overstock_out
                over_out.material = material
                over_out.amount = use
                yield over_out

                has_empty -= use
                empty[bin_key] = has_empty
                has_bin += use
                in_bin[mat_key] = has_bin

                bin_in = self.__bin_in
                bin_in.material = material
                bin_in.bin_type = bin_type
                bin_in.amount = use
                yield bin_in

        yield event


#: the end event
_QUIT: Final[int] = id(EndEvent)

#: the event router
_EVENT_ROUTER: Final[Callable[[int], Callable[[
    Simulation, Event], Iterable[Event]]]] = {
    _QUIT: Simulation._forward,  # type: ignore
    id(StartEvent): Simulation._forward,  # type: ignore
    id(Event): Simulation._error,  # type: ignore
    id(StorageEvent): Simulation._error,  # type: ignore
    id(BinEvent): Simulation._error,  # type: ignore
    id(BinIn): Simulation._error,  # type: ignore
    id(BinOut): Simulation._error,  # type: ignore
    id(InsufficientMaterial): Simulation._error,  # type: ignore
    id(OverstockIn): Simulation._error,  # type: ignore
    id(OverstockOut): Simulation._error,  # type: ignore
    id(WarehouseIn): Simulation._warehouse_in,  # type: ignore
    id(WarehouseOut): Simulation._warehouse_out,  # type: ignore
}.__getitem__
