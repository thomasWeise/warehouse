"""
The warehouse simulation.

In this class, we implement the functionality needed by the local warehouse.
This only concerns the movement of material units inside the warehouse, the
putting of units of material into the warehouse, and the taking of units of
material out of the warehouse.
This is completely separate from any other logic, such as the re-ordering of
material, the consumption of material at the assembly line, or anything else.
"""

from array import array
from typing import Final, Generator

from pycommons.types import type_error

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
        if not isinstance(instance, Instance):
            raise type_error(instance, "instance", Instance)

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

    def _start(self) -> None:
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
