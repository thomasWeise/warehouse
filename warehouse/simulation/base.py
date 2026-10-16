"""The warehouse simulation."""

from heapq import heappop, heappush
from typing import Callable, Final, Generator

from warehouse.event.bins import BinEvent, BinIn, BinOut
from warehouse.event.storage import (
    OverstockIn,
    OverstockOut,
    StorageEvent,
    Understock,
    WarehouseDelivers,
    WarehouseDemand,
    WarehouseIn,
)
from warehouse.event.time import (
    EndEvent,
    StartEvent,
)
from warehouse.instance.event import Event
from warehouse.instance.instance import Instance
from warehouse.instance.part import Part
from warehouse.instance.time import EARLIEST_START, LATEST_END


class BaseModule:
    """A warehouse simulation base module."""

    def __init__(self, instance: Instance) -> None:
        """
        Create the simulation.

        :param instance: the scenario/instance to simulate
        """
        #: the instance we are simulating
        self.instance: Final[Instance] = instance
        #: the internal queue
        self.__queue: Final[list[Event]] = []

    def enqueue(self, event: Event) -> None:
        """
        Add an event to the simulation's event queue.

        :param event: the event to add
        """
        heappush(self.__queue, event)

    def _start(self) -> None:
        """Begin the simulation."""
        queue: Final[list[Event]] = self.__queue
        # After this, the queue will definitely be a heap, because a list
        # sorted in ascending order is always a min-heap.
        queue.clear()
        queue.extend(self.instance.events)

    def _handle_start_event(self, event: StartEvent) -> None:
        """
        Handle a start event.

        :param event: the start event
        """

    def _handle_end_event(self, event: EndEvent) -> None:
        """
        Handle a end event.

        :param event: the end event
        """

    def _handle_warehouse_in(self, event: WarehouseIn) -> None:
        """
        Handle a warehouse-in event.

        :param event: the warehouse-in event.
        """

    def _handle_warehouse_demand(self, event: WarehouseDemand) -> None:
        """
        Handle a warehouse-demand event.

        :param event: the warehouse-demand event.
        """

    def _handle_warehouse_delivers(self, event: WarehouseDelivers) -> None:
        """
        Handle a warehouse-delivers event.

        :param event: the warehouse-delivers event.
        """

    def _handle_overstock_in(self, event: OverstockIn) -> None:
        """
        Handle an overstock-in event.

        :param event: the overstock-in event.
        """

    def _handle_overstock_out(self, event: OverstockOut) -> None:
        """
        Handle an overstock-out event.

        :param event: the overstock-out event.
        """

    def _handle_bin_in(self, event: BinIn) -> None:
        """
        Handle a bin-in event.

        :param event: the bin-in event.
        """

    def _handle_bin_out(self, event: BinOut) -> None:
        """
        Handle a bin-out event.

        :param event: the bin-out event.
        """

    def _handle_understock(self, event: Understock) -> None:
        """
        Handle an understock event.

        :param event: the understock event.
        """

    def available_units(self, part: Part) -> int:
        """
        Get the available units of the given part.

        These are units either currently in bins or in overstock, i.e., the
        number of units that we can ship immediately.

        :param part: the part
        :return: the number of units available
        """
        raise NotImplementedError

    def run(self) -> Generator[Event, None, None]:
        """
        Run the simulation.

        :return: the sequence of events.
        """
        self._start()

        first: Event
        queue: Final[list[Event]] = self.__queue
        if list.__len__(queue) <= 0:
            first = StartEvent(EARLIEST_START, 0)
            self.enqueue(first)
        else:
            first = queue[0]
            if first.__class__ is not StartEvent:
                self.enqueue(StartEvent(first.time, first.priority - 1))

        router: Final = self._create_event_router()
        quitter = _QUIT
        end_event: Event | None = None
        time: int = EARLIEST_START
        end_time: int = LATEST_END
        while queue:
            event: Event = heappop(queue)
            time = event.time
            eid = id(event.__class__)
            if eid == quitter:
                if end_event is not None:
                    raise ValueError(
                        f"Cannot have second end event {end_event!r}.")
                end_event = event
                end_time = time
            elif time > end_time:
                break

            yield event
            router(eid)(event)

        queue.clear()
        if end_event is None:
            end_event = EndEvent(time, 0)
            self._handle_end_event(end_event)
            yield end_event

    def _error(self, event: Event) -> None:
        """
        Handle an event that is not permitted.

        :param event: the event
        """
        raise ValueError(
            f"An event has occurred in the input event stream of a simulation"
            f" that is not permitted: {event!r}. Such "
            f"events can only be generated by the simulation (as output) but "
            f"you cannot trigger them by yourself as input to the "
            f"simulation.")

    def _create_event_router(self) -> Callable[[int], Callable[[Event], None]]:
        """
        Create the event router for this class.

        :return: the event router
        """
        return {
            _QUIT: self._handle_end_event,  # type: ignore
            id(StartEvent): self._handle_start_event,  # type: ignore
            id(Event): self._error,  # type: ignore
            id(StorageEvent): self._error,  # type: ignore
            id(BinEvent): self._error,  # type: ignore
            id(BinIn): self._handle_bin_in,  # type: ignore
            id(BinOut): self._handle_bin_out,  # type: ignore
            id(Understock): self._handle_understock,  # type: ignore
            id(OverstockIn): self._handle_overstock_in,  # type: ignore
            id(OverstockOut): self._handle_overstock_out,  # type: ignore
            id(WarehouseIn): self._handle_warehouse_in,  # type: ignore
            id(WarehouseDemand):  # type: ignore
            self._handle_warehouse_demand,  # type: ignore
            id(WarehouseDelivers):  # type: ignore
            self._handle_warehouse_delivers,  # type: ignore
        }.__getitem__


#: the end event
_QUIT: Final[int] = id(EndEvent)
