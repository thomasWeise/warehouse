"""The warehouse simulation."""

from heapq import heappop, heappush
from typing import Callable, Final, Generator

from warehouse.event.bins import BinEvent, BinIn, BinOut
from warehouse.event.checkpoint import CheckpointEvent
from warehouse.event.rules import (
    JitRuleCheckEvent,
    MinMaxRuleCheckEvent,
    RuleTriggeredEvent,
)
from warehouse.event.storage import (
    OverstockIn,
    OverstockOut,
    StorageEvent,
    Understock,
    WarehouseDelivers,
    WarehouseDemand,
    WarehouseIn,
)
from warehouse.event.time import EndEvent, InitializationComplete, StartEvent
from warehouse.instance.event import Event
from warehouse.instance.instance import Instance
from warehouse.instance.part import Part
from warehouse.instance.rule import Rule
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
        #: the start priority
        self.__max_priority: Final[int] = 2 + max(
            ev.priority for ev in instance.events)
        #: the next priority value
        self.__priority: int = 0
        #: the internal timestamp
        self.__time: int = EARLIEST_START
        #: the time adjustment function for job lengths
        self.__end_of_job: Final[Callable[[int, int, bool], int]] = (
            instance.end_of_job)
        #: the time adjustment function for next multiples
        self.__next_multiple_of: Final[Callable[[int, int], int]] = (
            instance.next_multiple_of)

    def _start(self) -> None:
        """Begin the simulation."""
        queue: Final[list[Event]] = self.__queue
        # After this, the queue will definitely be a heap, because a list
        # sorted in ascending order is always a min-heap.
        queue.clear()
        queue.extend(self.instance.events)
        self.__priority = self.__max_priority
        self.__time = EARLIEST_START

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

    def _minmax_check(self) -> MinMaxRuleCheckEvent:
        """
        Create a min/max rule check event.

        :return: the min max rule check event
        """
        self.__priority = p = self.__priority + 1
        res: Final[MinMaxRuleCheckEvent] = MinMaxRuleCheckEvent(
            self.__next_multiple_of(self.__time, 120), p)
        heappush(self.__queue, res)
        return res

    def _handle_minmax_check(self, event: MinMaxRuleCheckEvent) -> None:
        """
        Handle the min/max rule checking event.

        :param event: the event
        """

    def _jit_check(self) -> JitRuleCheckEvent:
        """
        Create a JIT rule check event.

        :return: the JIT rule check event
        """
        self.__priority = p = self.__priority + 1
        res: Final[JitRuleCheckEvent] = JitRuleCheckEvent(
            self.__next_multiple_of(self.__time, 300), p)
        heappush(self.__queue, res)
        return res

    def _handle_jit_check(self, event: JitRuleCheckEvent) -> None:
        """
        Handle the JIT rule checking event.

        :param event: the event
        """

    def _warehouse_in(self, delta: int,
                      part: Part,
                      amount: int) -> WarehouseIn:
        """
        Enqueue a warehouse-in event.

        :param delta: the time delta from now
        :param part: the part to enter the warehouse
        :param amount: the amount of the part
        :return: the event
        """
        self.__priority = p = self.__priority + 1
        res: Final[WarehouseIn] = WarehouseIn(
            self.__end_of_job(self.__time, delta, True), p, part, amount)
        heappush(self.__queue, res)
        return res

    def _handle_warehouse_in(self, event: WarehouseIn) -> None:
        """
        Handle a warehouse-in event.

        :param event: the warehouse-in event.
        """

    def _warehouse_demand(self, delta: int,
                          part: Part,
                          amount: int) -> WarehouseDemand:
        """
        Enqueue a warehouse-demand event.

        :param delta: the time delta from now
        :param part: the part to enter the warehouse
        :param amount: the amount of the part
        :return: the event
        """
        self.__priority = p = self.__priority + 1
        res: Final[WarehouseDemand] = WarehouseDemand(
            self.__end_of_job(self.__time, delta, False), p, part, amount)
        heappush(self.__queue, res)
        return res

    def _handle_warehouse_demand(self, event: WarehouseDemand) -> None:
        """
        Handle a warehouse-demand event.

        :param event: the warehouse-demand event.
        """

    def _warehouse_delivers(self, delta: int,
                            part: Part,
                            amount: int) -> WarehouseDelivers:
        """
        Enqueue a warehouse-delivers event.

        :param delta: the time delta from now
        :param part: the part to enter the warehouse
        :param amount: the amount of the part
        :return: the event
        """
        self.__priority = p = self.__priority + 1
        res: Final[WarehouseDelivers] = WarehouseDelivers(
            self.__end_of_job(self.__time, delta, False), p, part, amount)
        heappush(self.__queue, res)
        return res

    def _handle_warehouse_delivers(self, event: WarehouseDelivers) -> None:
        """
        Handle a warehouse-delivers event.

        :param event: the warehouse-delivers event.
        """

    def _overstock_in(self, delta: int,
                      part: Part,
                      amount: int) -> OverstockIn:
        """
        Enqueue an overstock-in event.

        :param delta: the time delta from now
        :param part: the part to enter the warehouse
        :param amount: the amount of the part
        :return: the event
        """
        self.__priority = p = self.__priority + 1
        res: Final[OverstockIn] = OverstockIn(
            self.__end_of_job(self.__time, delta, False), p, part, amount)
        heappush(self.__queue, res)
        return res

    def _handle_overstock_in(self, event: OverstockIn) -> None:
        """
        Handle an overstock-in event.

        :param event: the overstock-in event.
        """

    def _overstock_out(self, delta: int,
                       part: Part,
                       amount: int) -> OverstockOut:
        """
        Enqueue an overstock-out event.

        :param delta: the time delta from now
        :param part: the part to enter the warehouse
        :param amount: the amount of the part
        :return: the event
        """
        self.__priority = p = self.__priority + 1
        res: Final[OverstockOut] = OverstockOut(
            self.__end_of_job(self.__time, delta, False), p, part, amount)
        heappush(self.__queue, res)
        return res

    def _handle_overstock_out(self, event: OverstockOut) -> None:
        """
        Handle an overstock-out event.

        :param event: the overstock-out event.
        """

    def _bin_in(self, delta: int,
                part: Part, amount) -> BinIn:
        """
        Enqueue a bin-in event.

        :param delta: the time delta from now
        :param part: the part to enter the warehouse
        :param amount: the amount of the part
        :return: the event
        """
        self.__priority = p = self.__priority + 1
        res: Final[BinIn] = BinIn(
            self.__end_of_job(self.__time, delta, False), p, part, amount)
        heappush(self.__queue, res)
        return res

    def _handle_bin_in(self, event: BinIn) -> None:
        """
        Handle a bin-in event.

        :param event: the bin-in event.
        """

    def _bin_out(self, delta: int,
                 part: Part, amount) -> BinOut:
        """
        Enqueue a bin-out event.

        :param delta: the time delta from now
        :param part: the part to enter the warehouse
        :param amount: the amount of the part
        :return: the event
        """
        self.__priority = p = self.__priority + 1
        res: Final[BinOut] = BinOut(
            self.__end_of_job(self.__time, delta, False), p, part, amount)
        heappush(self.__queue, res)
        return res

    def _handle_bin_out(self, event: BinOut) -> None:
        """
        Handle a bin-out event.

        :param event: the bin-out event.
        """

    def _understock(self, delta: int,
                    part: Part,
                    amount: int) -> Understock:
        """
        Enqueue an understock event.

        :param delta: the time delta from now
        :param part: the part to enter the warehouse
        :param amount: the amount of the part
        :return: the event
        """
        self.__priority = p = self.__priority + 1
        res: Final[Understock] = Understock(
            self.__end_of_job(self.__time, delta, True), p, part, amount)
        heappush(self.__queue, res)
        return res

    def _handle_understock(self, event: Understock) -> None:
        """
        Handle an understock event.

        :param event: the understock event.
        """

    def _rule_triggered(self, delta: int,
                        rule: Rule,
                        part: Part,
                        amount: int) -> RuleTriggeredEvent:
        """
        Enqueue a rule-triggered event.

        :param delta: the time delta from now
        :param rule: the rule that was triggered
        :param part: the part to enter the warehouse
        :param amount: the amount of the part
        :return: the event
        """
        self.__priority = p = self.__priority + 1
        res: Final[RuleTriggeredEvent] = RuleTriggeredEvent(
            self.__end_of_job(self.__time, delta, True), p, rule, part, amount)
        heappush(self.__queue, res)
        return res

    def _handle_rule_triggered(self, event: RuleTriggeredEvent) -> None:
        """
        Handle that a rule was triggered.

        :param event: the rule trigger event
        """

    def _handle_checkpoint(self, event: CheckpointEvent) -> None:
        """
        Handle that an amount of a given product has reached a checkpoint.

        :param event: the event
        """

    def _handle_initizalization_complete(
            self, event: InitializationComplete) -> None:
        """
        Handle the event denoting the completion of the initialization.

        :param event: the event
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

        event: Event
        queue: Final[list[Event]] = self.__queue
        start_time: int = EARLIEST_START
        if list.__len__(queue) <= 0:
            event = StartEvent(EARLIEST_START, 0)
            heappush(queue, event)
        else:
            event = queue[0]
            start_time = event.time
            if event.__class__ is not StartEvent:
                heappush(queue, StartEvent(start_time, event.priority - 1))

        needs_init: bool = True
        for event in queue:
            if isinstance(event, InitializationComplete):
                needs_init = False
                break
            if event.time > start_time:
                break

        router: Final = self._create_event_router()
        quitter = _QUIT
        end_event: Event | None = None
        self.__time = time = EARLIEST_START
        end_time: int = LATEST_END
        while queue:
            event = queue[0]
            time = event.time
            eid: int = id(event.__class__)

            if needs_init and ((time > start_time) or (eid == quitter)):
                event = InitializationComplete(start_time, event.priority - 1)
                needs_init = False
                time = start_time
                eid = id(event.__class__)
            else:
                heappop(queue)
            self.__time = time

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
            end_event = EndEvent(time, self.__priority + 1)
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
            id(RuleTriggeredEvent):  # type: ignore
            self._handle_rule_triggered,  # type: ignore
            id(CheckpointEvent):  # type: ignore
            self._handle_checkpoint,  # type: ignore
            id(InitializationComplete):  # type: ignore
            self._handle_initizalization_complete,  # type: ignore
            id(MinMaxRuleCheckEvent):
            self._handle_minmax_check,  # type: ignore
            id(JitRuleCheckEvent): self._handle_jit_check,  # type: ignore
        }.__getitem__


#: the end event
_QUIT: Final[int] = id(EndEvent)
