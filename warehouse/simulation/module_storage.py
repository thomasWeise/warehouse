"""
The warehouse storage simulation.

In this class, we implement the functionality needed by the local warehouse.
This only concerns the movement of part units inside the warehouse, the
putting of units of part into the warehouse, and the taking of units of
part out of the warehouse.
This is completely separate from any other logic, such as the re-ordering of
part, the consumption of part at the assembly line, or anything else.
"""

from collections import Counter
from typing import Final

from warehouse.event.bins import BinIn, BinOut
from warehouse.event.storage import (
    OverstockIn,
    OverstockOut,
    Understock,
    WarehouseDelivers,
    WarehouseDemand,
    WarehouseIn,
)
from warehouse.instance.bin_type import BinType
from warehouse.instance.instance import Instance
from warehouse.instance.part import Part
from warehouse.simulation.base import BaseModule


class StorageModule(BaseModule):
    """The storage part of the simulation."""

    def __init__(self, instance: Instance) -> None:
        """
        Create the storage part of the simulation.

        :param instance: the scenario/instance to simulate
        """
        super().__init__(instance)
        #: the parts per bin type.
        self.__mat_bin: Final[tuple[tuple[int, ...], ...]] = tuple(
            tuple(part.key for part in instance.parts if
                  part.bin_type is bt) for bt in instance.bin_types)
        #: the parts
        self.__parts: Final[tuple[Part, ...]] = instance.parts

        n_parts: Final[int] = tuple.__len__(instance.parts)
        n_bin_types: Final[int] = tuple.__len__(instance.bin_types)

        #: the amount of parts currently in overstock
        self.__in_overstock: Final[list[int]] = [0] * n_parts
        #: the overstock queue
        self.__overstock_queue: Final[tuple[list[list[int]], ...]] = tuple(
            [] for _ in range(n_bin_types))
        #: the amount of parts which were understocked
        self.__in_understock: Final[list[int]] = [0] * n_parts
        #: the empty bins of the given types
        self.__empty_bins: Final[list[int]] = [0] * n_bin_types
        #: the amount of parts that are currently in the bins
        self.__in_bin: Final[tuple[Counter[int], ...]] = tuple(
            Counter(dict.fromkeys(mb, 0)) for mb in self.__mat_bin)

        #: the bin types
        self.__bin_types: Final[tuple[BinType, ...]] = instance.bin_types

    def _start(self) -> None:
        """Begin the simulation."""
        super()._start()
        in_overstock: Final[list[int]] = self.__in_overstock
        in_understock: Final[list[int]] = self.__in_understock
        empty_bins: Final[list[int]] = self.__empty_bins
        bin_types: Final[tuple[BinType, ...]] = self.__bin_types
        over_queue: Final[tuple[list[list[int]], ...]] = (
            self.__overstock_queue)

        for i in range(list.__len__(in_overstock)):
            in_overstock[i] = 0
            in_understock[i] = 0

        for i, st in enumerate(self.__in_bin):
            for k in self.__mat_bin[i]:
                st[k] = 0
            empty_bins[i] = bin_types[i].amount
            over_queue[i].clear()

    def _handle_warehouse_in(self, event: WarehouseIn) -> None:
        """
        Store part into the warehouse.

        :param event: the event with the information about the part
            to be stored
        :return: the event stream
        """
        part: Final[Part] = event.part
        part_key: Final[int] = part.key
        bin_type: Final[BinType] = part.bin_type
        bin_key: Final[int] = bin_type.key
        amount: int = event.amount
        empty_bins: Final[list[int]] = self.__empty_bins
        time: Final[int] = event.time

        # First, we check if there is a prior pending request for the
        # parts. If yes, we directly satisfy it without putting the
        # material in any stock.
        use: int = min(self.__in_understock[part_key], amount)
        if use > 0:
            self.enqueue(WarehouseDelivers(time, self._priority(), part, use))
            self.__in_understock[part_key] -= use
            amount -= use
            if amount <= 0:
                return

        # Now we check whether we can put the parts into empty bins.
        use = min(empty_bins[bin_key], amount)
        if use > 0:
            empty_bins[bin_key] -= use
            self.__in_bin[bin_key][part_key] += use
            self.enqueue(BinIn(time, self._priority(), part, use))
            amount -= use
            if amount <= 0:
                return

        # Finally, all remaining parts go into the overstock.
        self.__in_overstock[part_key] += amount
        self.__overstock_queue[bin_key].append([part_key, amount])
        self.enqueue(OverstockIn(time, self._priority(), part, amount))

    def _handle_warehouse_demand(self, event: WarehouseDemand) -> None:
        """
        Remove part from the warehouse.

        :param event: the event
        """
        part: Final[Part] = event.part
        part_key: Final[int] = part.key
        bin_type: Final[BinType] = part.bin_type
        bin_key: Final[int] = bin_type.key
        amount: int = event.amount
        time: Final[int] = event.time

        in_bin: Final[Counter[int]] = self.__in_bin[bin_key]
        in_overstock: Final[list[int]] = self.__in_overstock

        # Check how much part we can actually deliver.
        use: int = in_bin[part_key] + in_overstock[part_key]
        if use < amount:
            # We cannot fulfill this request, so we are in an understock
            # situation.
            # We remember the request, though, so as soon as parts come in,
            # we can directly ship them to satisfy the understock requests
            # first.
            under: int = amount - use
            self.__in_understock[part_key] += under
            self.enqueue(Understock(time, self._priority(), part, under))
            if use <= 0:
                return

            # Make a modified copy of the original event
            amount = use

        deliver_amount: Final[int] = amount
        empty_bins: Final[list[int]] = self.__empty_bins
        bin_type_empty = empty_bins[bin_key]

        if amount > 0:
            use = min(in_bin[part_key], amount)
            if use > 0:
                # We have part in the bin and can ship it.
                # This means that we take the part out of the bin.
                # This creates new empty bins
                amount -= use
                in_bin[part_key] -= use
                bin_type_empty += use
                empty_bins[bin_key] = bin_type_empty
                self.enqueue(BinOut(time, self._priority(), part, use))

            use = min(in_overstock[part_key], amount)
            if use > 0:
                # Now take from overstock
                amount -= use
                in_overstock[part_key] -= use
                _over_unqueue(self.__overstock_queue[bin_key], part_key, use)
                self.enqueue(OverstockOut(time, self._priority(), part, use))

        if amount > 0:
            raise ValueError("Huh?")

        # When we get here, we have extracted all the required part and
        # can now ship it out of the warehouse.
        self.enqueue(WarehouseDelivers(
            time, self._priority(), part, deliver_amount))

        # Some bins became empty, so let's fill them.
        if bin_type_empty > 0:
            over_queue: list[list[int]] = self.__overstock_queue[bin_key]
            while over_queue:
                other_part, other_amount = over_queue[0]
                use = min(bin_type_empty, other_amount)
                use_part = self.__parts[other_part]
                _over_unqueue(over_queue, other_part, use)
                self.enqueue(OverstockOut(
                    time, self._priority(), use_part, use))

                bin_type_empty -= use
                empty_bins[bin_key] = bin_type_empty
                in_bin[other_part] += use
                in_overstock[other_part] -= use
                self.enqueue(BinIn(time, self._priority(), use_part, use))

                if bin_type_empty <= 0:
                    break

    def available_units(self, part: Part) -> int:
        """
        Get the amount of units currently available in the warehouse.

        :param part: the part
        :return: the units
        """
        part_key: Final[int] = part.key
        return (self.__in_bin[part.bin_type.key][part_key]
                + self.__in_overstock[part_key]
                - self.__in_understock[part_key])


def _over_unqueue(over_lst: list[list[int]],
                  part_key: int, amount: int) -> None:
    """
    Remove the given amount of material from the overstock queue.

    :param over_lst: the overstock queue
    :param part_key: the material key
    :param amount: the amount of material to remove
    """
    total: int = list.__len__(over_lst)
    i: int = 0
    while (i < total) and (amount > 0):
        current: list[int] = over_lst[i]
        if current[0] != part_key:
            i += 1
            continue
        got: int = current[1]
        remove: int = min(got, amount)
        got -= remove
        if got <= 0:
            del over_lst[i]
            total -= 1
        else:
            current[1] = got
        amount -= remove
    if amount > 0:
        raise ValueError(f"There are {amount} units of part"
                         f" {part_key} unaccounted for in overstock.")
