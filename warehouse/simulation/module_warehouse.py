"""
The warehouse simulation.

In this class, we implement the functionality needed by the local warehouse.
This only concerns the movement of part units inside the warehouse, the
putting of units of part into the warehouse, and the taking of units of
part out of the warehouse.
This is completely separate from any other logic, such as the re-ordering of
part, the consumption of part at the assembly line, or anything else.
"""

from collections import Counter
from typing import Final, Generator

from warehouse.event.bins import BinIn, BinOut
from warehouse.event.storage import (
    OverstockIn,
    OverstockOut,
    Understock,
    WarehouseDelivers,
    WarehouseIn,
    WarehouseOut,
)
from warehouse.instance.bin_type import BinType
from warehouse.instance.event import Event
from warehouse.instance.instance import Instance
from warehouse.instance.part import Part


class WarehouseModule:
    """The warehouse part of the simulation."""

    def __init__(self, instance: Instance) -> None:
        """
        Create the simulation.

        :param instance: the scenario/instance to simulate
        """
        #: the parts per bin type.
        self.__mat_bin: Final[tuple[tuple[int, ...], ...]] = tuple(
            tuple(part.key for part in instance.parts if
                  part.bin_type is bt) for bt in instance.bin_types)
        #: the parts
        self.__parts: Final[tuple[Part, ...]] = instance.parts

        #: the amount of parts currently in overstock
        self.__in_overstock: Final[list[int]] = [0] * instance.n_parts
        #: the amount of parts which were understocked
        self.__in_understock: Final[list[int]] = [0] * instance.n_parts
        #: the empty bins of the given types
        self.__empty_bins: Final[list[int]] = [0] * instance.n_bin_types
        #: the amount of parts that are currently in the bins
        self.__in_bin: Final[tuple[Counter[int], ...]] = tuple(
            Counter(dict.fromkeys(mb, 0)) for mb in self.__mat_bin)

        #: the bin types
        self.__bin_types: Final[tuple[BinType, ...]] = instance.bin_types

    def _start(self) -> None:
        """Begin the simulation."""
        in_overstock: Final[list[int]] = self.__in_overstock
        in_understock: Final[list[int]] = self.__in_understock
        empty_bins: Final[list[int]] = self.__empty_bins
        bin_types: Final[tuple[BinType, ...]] = self.__bin_types

        for i in range(list.__len__(in_overstock)):
            in_overstock[i] = 0
            in_understock[i] = 0

        for i, st in enumerate(self.__in_bin):
            for k in self.__mat_bin[i]:
                st[k] = 0
            empty_bins[i] = bin_types[i].amount

    def _warehouse_in(self, event: WarehouseIn) -> Generator[
            Event, None, None]:
        """
        Store part into the warehouse.

        :param event: the event with the information about the part
            to be stored
        :return: the event stream
        """
        part: Final[Part] = event.part
        mat_key: Final[int] = part.key
        bin_type: Final[BinType] = part.bin_type
        bin_key: Final[int] = bin_type.key
        amount: int = event.amount
        empty_bins: Final[list[int]] = self.__empty_bins
        time: Final[int] = event.time

        # First, we check if there is a prior pending request for the
        # parts. If yes, we directly satisfy it without putting the
        # material in any stock.
        use: int = min(self.__in_understock[mat_key], amount)
        if use > 0:
            yield WarehouseDelivers(time, part, use)
            amount -= use
            if amount <= 0:
                return

        # Now we check whether we can put the parts into empty bins.
        use = min(empty_bins[bin_key], amount)
        if use > 0:
            empty_bins[bin_key] -= use
            self.__in_bin[bin_key][mat_key] += use
            yield BinIn(time, part, use)
            amount -= use
            if amount <= 0:
                return

        # Finally, all remaining parts go into the overstock.
        self.__in_overstock[mat_key] += amount
        yield OverstockIn(time, part, amount)

    def _warehouse_out(self, event: WarehouseOut) -> Generator[
            Event, None, None]:
        """
        Remove part from the warehouse.

        :param event: the event
        """
        part: Final[Part] = event.part
        mat_key: Final[int] = part.key
        bin_type: Final[BinType] = part.bin_type
        bin_key: Final[int] = bin_type.key
        amount: int = event.amount
        time: Final[int] = event.time

        in_bin: Final[Counter[int]] = self.__in_bin[bin_key]
        in_overstock: Final[list[int]] = self.__in_overstock

        # Check how much part we can actually deliver.
        use: int = in_bin[mat_key] + in_overstock[mat_key]
        if use < amount:
            # We cannot fulfill this request, so we are in an understock
            # situation.
            # We remember the request, though, so as soon as parts come in,
            # we can directly ship them to satisfy the understock requests
            # first.
            under: int = amount - use
            self.__in_understock[mat_key] += under
            yield Understock(time, part, under)
            if use <= 0:
                return

            # Make a modified copy of the original event
            amount = use

        e_deliver: Final[WarehouseDelivers] = WarehouseDelivers(
            time, part, amount)

        empty_bins: Final[list[int]] = self.__empty_bins
        bin_type_empty = empty_bins[bin_key]

        while amount > 0:
            use = min(in_bin[mat_key], amount)
            if use > 0:
                # We have part in the bin and can ship it.
                # This means that we take the part out of the bin.
                # This creates new empty bins
                amount -= use
                in_bin[mat_key] -= use
                bin_type_empty += use
                empty_bins[bin_key] = bin_type_empty
                yield BinOut(time, part, use)
                continue

            # If we get here, we do not have our parts in the bin.
            # It holds that mat_in_bin == 0
            # Since we know that we have enough parts, they must be in the
            # overstock.
            if bin_type_empty > 0:
                use = min(bin_type_empty, amount, in_overstock[mat_key])
                if use <= 0:
                    raise ValueError(
                        f"Illegal state: We definitely got {amount} units of "
                        f"part {part!r} in the combined stock of bins "
                        "and overstock, but the bins are empty and overstock "
                        f"has only {in_overstock[mat_key]} items left, while"
                        f" there now are {bin_type_empty} empty bins of type "
                        f"{bin_type!r}.")

                in_overstock[mat_key] -= use
                yield OverstockOut(time, part, use)

                bin_type_empty -= use
                empty_bins[bin_key] = bin_type_empty
                in_bin[mat_key] += use
                yield BinIn(time, part, use)

                # In the next iteration, we can take the parts out of the bin
                # again.
                continue

            # Here we face a strange situation: We do have more parts to
            # ship.
            # This part is in the overstock.
            # In order to ship it, we need to move it into the bins.
            # However, we cannot do that, because all bins are full.
            # This must mean that some *other* part occupies the bins.
            # So we first must transfer this part to the overstock.
            # Then we can move our part from the overstock into the bin,
            # just to take it out again right away...
            other_mat, other_amount = in_bin.most_common(1)[0]
            use = min(amount, other_amount)
            if use <= 0:
                raise ValueError(
                    f"Illegal state: We definitely got {amount} units of "
                    f"part {part!r} left in the combined "
                    "stock of bins and overstock, there are no empty bins, "
                    "there are no units of the part in the bins, but "
                    f"there are also at most no={other_amount} units of "
                    f"other part in the bins of type {bin_type!r}. "
                    "So how can the bins be full?")

            use_part = self.__parts[other_mat]
            in_bin[other_mat] -= use
            bin_type_empty += use
            empty_bins[bin_key] = bin_type_empty
            yield BinOut(time, use_part, use)

            in_overstock[other_mat] += use
            yield OverstockIn(time, use_part, use)

        # When we get here, we have extracted all the required part and
        # can now ship it out of the warehouse.
        yield e_deliver

        # Some bins became empty, so let's fill them.
        if bin_type_empty > 0:
            for other_mat in self.__mat_bin[bin_key]:
                use = min(bin_type_empty, in_overstock[other_mat])
                if use > 0:
                    use_part = self.__parts[other_mat]
                    yield OverstockOut(time, use_part, use)

                    bin_type_empty -= use
                    empty_bins[bin_key] = bin_type_empty
                    in_bin[other_mat] += use
                    in_overstock[other_mat] -= use
                    yield BinIn(time, use_part, use)

                    if bin_type_empty <= 0:
                        break
