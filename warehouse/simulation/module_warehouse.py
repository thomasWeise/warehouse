"""
The warehouse simulation.

In this class, we implement the functionality needed by the local warehouse.
This only concerns the movement of material units inside the warehouse, the
putting of units of material into the warehouse, and the taking of units of
material out of the warehouse.
This is completely separate from any other logic, such as the re-ordering of
material, the consumption of material at the assembly line, or anything else.
"""

from collections import Counter
from typing import Final, Generator

from warehouse.event.bins import BinIn, BinOut
from warehouse.event.storage import (
    InsufficientMaterial,
    OverstockIn,
    OverstockOut,
    WarehouseDelivers,
    WarehouseIn,
    WarehouseOut,
)
from warehouse.instance.bin_type import BinType
from warehouse.instance.event import Event
from warehouse.instance.instance import Instance
from warehouse.instance.material import Material


class WarehouseModule:
    """The warehouse part of the simulation."""

    def __init__(self, instance: Instance) -> None:
        """
        Create the simulation.

        :param instance: the scenario/instance to simulate
        """
        #: the materials per bin type.
        self.__mat_bin: Final[tuple[tuple[int, ...], ...]] = tuple(
            tuple(material.key for material in instance.materials if
                  material.bin_type is bt) for bt in instance.bin_types)
        #: the materials
        self.__materials: Final[tuple[Material, ...]] = instance.materials

        #: the amount of materials currently in overstock
        self.__in_overstock: Final[list[int]] = [0] * instance.n_materials
        #: the empty bins of the given types
        self.__empty_bins: Final[list[int]] = [0] * instance.n_bin_types
        #: the amount of materials that are currently in the bins
        self.__in_bin: Final[tuple[Counter[int], ...]] = tuple(
            Counter(dict.fromkeys(mb, 0)) for mb in self.__mat_bin)

        #: the bin types
        self.__bin_types: Final[tuple[BinType, ...]] = instance.bin_types

    def _start(self) -> None:
        """Begin the simulation."""
        in_overstock: Final[list[int]] = self.__in_overstock
        empty_bins: Final[list[int]] = self.__empty_bins
        bin_types: Final[tuple[BinType, ...]] = self.__bin_types

        for i in range(list.__len__(in_overstock)):
            in_overstock[i] = 0

        for i, st in enumerate(self.__in_bin):
            for k in self.__mat_bin[i]:
                st[k] = 0
            empty_bins[i] = bin_types[i].amount

    def _warehouse_in(self, event: WarehouseIn) -> Generator[
            Event, None, None]:
        """
        Store material into the warehouse.

        :param event: the event with the information about the material
            to be stored
        :return: the event stream
        """
        material: Final[Material] = event.material
        mat_key: Final[int] = material.key
        bin_type: Final[BinType] = material.bin_type
        bin_key: Final[int] = bin_type.key
        amount: int = event.amount
        empty_bins: Final[list[int]] = self.__empty_bins
        time: Final[int] = event.time

        use: int = min(empty_bins[bin_key], amount)
        if use > 0:
            empty_bins[bin_key] -= use
            self.__in_bin[bin_key][mat_key] += use
            yield BinIn(time, material, use, bin_type)
            amount -= use
            if amount <= 0:
                return

        self.__in_overstock[mat_key] += amount
        yield OverstockIn(time, material, amount)

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
        time: Final[int] = event.time

        in_bin: Final[Counter[int]] = self.__in_bin[bin_key]
        in_overstock: Final[list[int]] = self.__in_overstock

        # Check how much material we can actually deliver.
        use: int = in_bin[mat_key] + in_overstock[mat_key]
        if use < amount:
            # We cannot fulfill this request.
            yield InsufficientMaterial(time, material, amount - use)

            if use <= 0:
                return

            # Make a modified copy of the original event
            amount = use

        e_deliver: Final[WarehouseDelivers] = WarehouseDelivers(
            time, material, amount)

        empty_bins: Final[list[int]] = self.__empty_bins
        bin_type_empty = empty_bins[bin_key]

        while amount > 0:
            use = min(in_bin[mat_key], amount)
            if use > 0:
                # We have material in the bin and can ship it.
                # This means that we take the material out of the bin.
                # This creates new empty bins
                amount -= use
                in_bin[mat_key] -= use
                bin_type_empty += use
                empty_bins[bin_key] = bin_type_empty
                yield BinOut(time, material, use, bin_type)
                continue

            # If we get here, we do not have our material in the bin.
            # It holds that mat_in_bin == 0
            # Since we know that we have enough material, it must be in the
            # overstock.
            if bin_type_empty > 0:
                use = min(bin_type_empty, in_overstock[mat_key])
                if use <= 0:
                    raise ValueError(
                        f"Illegal state: We definitely got {amount} units of "
                        f"material {material!r} in the combined stock of bins "
                        "and overstock, but the bins are empty and overstock "
                        f"has only {in_overstock[mat_key]} items left, while"
                        f" there now are {bin_type_empty} empty bins of type "
                        f"{bin_type!r}.")

                in_overstock[mat_key] -= use
                yield OverstockOut(time, material, use)

                bin_type_empty -= use
                empty_bins[bin_key] = bin_type_empty
                in_bin[mat_key] += use
                yield BinIn(time, material, use, bin_type)

                # In the next iteration, we can take the material out of
                # the bin again.
                continue

            # Here we face a strange situation: We do have more material to
            # ship.
            # This material is in the overstock.
            # In order to ship it, we need to move it into the bins.
            # However, we cannot do that, because all bins are full.
            # This must mean that some *other* material occupies the bins.
            # So we first must transfer this material to the overstock.
            # Then we can move our material from the overstock into the bin,
            # just to take it out again right away...
            other_mat, other_amount = in_bin.most_common(1)[0]
            use = min(amount, other_amount)
            if use <= 0:
                raise ValueError(
                    f"Illegal state: We definitely got {amount} units of "
                    f"material {material!r} left in the combined "
                    "stock of bins and overstock, there are no empty bins, "
                    "there are no units of the material in the bins, but "
                    f"there are also at most no={other_amount} units of "
                    f"other material in the bins of type {bin_type!r}. "
                    "So how can the bins be full?")

            use_material = self.__materials[other_mat]
            in_bin[other_mat] -= use
            bin_type_empty += use
            empty_bins[bin_key] = bin_type_empty
            yield BinOut(time, use_material, use, bin_type)

            in_overstock[other_mat] += use
            yield OverstockIn(time, use_material, use)

        # When we get here, we have extracted all the required material and
        # can now ship it out of the warehouse.
        yield e_deliver

        # Some bins became empty, so let's fill them.
        if bin_type_empty > 0:
            for other_mat in self.__mat_bin[bin_key]:
                use = min(bin_type_empty, in_overstock[other_mat])
                if use > 0:
                    use_material = self.__materials[other_mat]
                    yield OverstockOut(time, use_material, use)

                    bin_type_empty -= use
                    empty_bins[bin_key] = bin_type_empty
                    in_bin[other_mat] += use
                    in_overstock[other_mat] -= use
                    yield BinIn(time, use_material, use, bin_type)

                    if bin_type_empty <= 0:
                        break
