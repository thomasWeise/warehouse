"""The warehouse simulation."""


from pycommons.types import type_error

from warehouse.instance.instance import Instance
from warehouse.simulation.module_storage import StorageModule


class Simulation(StorageModule):
    """A warehouse simulation."""

    def __init__(self, instance: Instance) -> None:
        """
        Create the simulation.

        :param instance: the scenario/instance to simulate
        """
        if not isinstance(instance, Instance):
            raise type_error(instance, "instance", Instance)
        super().__init__(instance)
