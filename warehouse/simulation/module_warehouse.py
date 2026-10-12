"""
The warehouse simulation.

In this class, we implement the functionality needed by the local warehouse.
This only concerns the movement of material units inside the warehouse, the
putting of units of material into the warehouse, and the taking of units of
material out of the warehouse.
This is completely separate from any other logic, such as the re-ordering of
material, the consumption of material at the assembly line, or anything else.
"""

from typing import Final, Generator

from warehouse.event.bins import BinIn, BinOut
from warehouse.event.storage import (
    InsufficientMaterial,
    OverstockIn,
    OverstockOut,
    WarehouseIn,
    WarehouseOut,
)
from warehouse.instance.bin_type import BinType
from warehouse.instance.event import Event
from warehouse.instance.instance import Instance
from warehouse.instance.material import Material
from warehouse.instance.time import EARLIEST_START


class WarehouseModule:
    """The warehouse part of the simulation."""

    def __init__(self, instance: Instance) -> None:
        """
        Create the simulation.

        :param instance: the scenario/instance to simulate
        """
        #: the amount of materials currently in overstock
        self.__in_overstock: Final[list[int]] = [0] * instance.n_materials
        #: the empty bins of the given types
        self.__empty_bins: Final[list[int]] = [0] * instance.n_bin_types
        #: the amount of the material currently inside bins
        self.__in_bin: Final[list[int]] = [0] * instance.n_materials

        use_material: Final[Material] = instance.materials[0]
        use_bin_type: Final[BinType] = instance.bin_types[0]

        #: the shared BinIn event
        self.__e_bin_in: Final[BinIn] = BinIn(
            EARLIEST_START, use_material, 1, use_bin_type)
        #: the shared BinOut event
        self.__e_bin_out: Final[BinOut] = BinOut(
            EARLIEST_START, use_material, 1, use_bin_type)
        #: the shared overstock in event
        self.__e_overstock_in: Final[OverstockIn] = OverstockIn(
            EARLIEST_START, use_material, 1)
        #: the shared overstock out event
        self.__e_overstock_out: Final[OverstockOut] = OverstockOut(
            EARLIEST_START, use_material, 1)
        #: the shared insufficient event
        self.__e_insufficient: Final[InsufficientMaterial] = \
            InsufficientMaterial(EARLIEST_START, use_material, 1)
        #: the bins
        self.__bin_types: Final[tuple[BinType, ...]] = instance.bin_types

    def _start(self) -> None:
        """Begin the simulation."""
        in_overstock: Final[list[int]] = self.__in_overstock
        in_bin: Final[list[int]] = self.__in_bin
        empty_bins: Final[list[int]] = self.__empty_bins
        bin_types: Final[tuple[BinType, ...]] = self.__bin_types

        for i in range(list.__len__(in_overstock)):
            in_overstock[i] = 0
            in_bin[i] = 0

        for i in range(list.__len__(empty_bins)):
            empty_bins[i] = bin_types[i].amount

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
        empty_bins: Final[list[int]] = self.__empty_bins
        in_bin: Final[list[int]] = self.__in_bin

        use: int = min(empty_bins[bin_key], amount)
        if use > 0:
            e_bin_in: Final[BinIn] = self.__e_bin_in
            e_bin_in.material = material
            e_bin_in.bin_type = bin_type
            e_bin_in.amount = use
            empty_bins[bin_key] -= use
            in_bin[mat_key] += use
            yield e_bin_in
            amount -= use
            if amount <= 0:
                return

        self.__in_overstock[mat_key] += amount
        e_over_in: Final[OverstockIn] = self.__e_overstock_in
        e_over_in.material = material
        e_over_in.amount = amount
        yield e_over_in

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

        empty_bins: Final[list[int]] = self.__empty_bins
        in_bin: Final[list[int]] = self.__in_bin
        in_overstock: Final[list[int]] = self.__in_overstock

        e_bin_out: Final[BinOut] = self.__e_bin_out
        e_bin_out.material = material
        e_bin_out.bin_type = bin_type

        mat_in_overstock = in_overstock[mat_key]
        mat_in_bin = in_bin[mat_key]
        bin_type_empty = empty_bins[bin_key]

        while amount > 0:
            use = min(mat_in_bin, amount)
            if use <= 0:
                e_insuf_mat: InsufficientMaterial = self.__e_insufficient
                e_insuf_mat.material = material
                e_insuf_mat.amount = amount
                yield e_insuf_mat

                event = event.copy()
                event.amount = amount
                break

            amount -= use
            e_bin_out.amount = use
            mat_in_bin -= use
            in_bin[mat_key] = mat_in_bin
            bin_type_empty += use
            empty_bins[bin_key] = bin_type_empty
            yield e_bin_out

            if mat_in_overstock > 0:
                use = min(bin_type_empty, mat_in_overstock)
                mat_in_overstock -= use
                in_overstock[mat_key] = mat_in_overstock

                e_over_out = self.__e_overstock_out
                e_over_out.material = material
                e_over_out.amount = use
                yield e_over_out

                bin_type_empty -= use
                empty_bins[bin_key] = bin_type_empty
                mat_in_bin += use
                in_bin[mat_key] = mat_in_bin

                e_bin_in = self.__e_bin_in
                e_bin_in.material = material
                e_bin_in.bin_type = bin_type
                e_bin_in.amount = use
                yield e_bin_in

        yield event
