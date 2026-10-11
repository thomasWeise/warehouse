"""Test the warehouse part of the simulation."""

from tests.warehouse.instance.test_warehouse_instance import (
    create_default_instance,
)
from warehouse.event.storage import WarehouseIn, WarehouseOut
from warehouse.event.time import EndEvent, StartEvent
from warehouse.instance.event import Event
from warehouse.instance.instance import Instance
from warehouse.simulation.simulation import Simulation


def test_warehouse_simulation() -> None:
    """Test the warehouse simulation."""
    instance = create_default_instance()
    permitted = {StartEvent, EndEvent, WarehouseOut, WarehouseIn}
    instance = Instance(
        instance.bin_types, instance.materials,
        (e for e in instance.events if e.__class__ in permitted))

    simulation = Simulation(instance)
    e = None
    first = True
    last = False
    for e in simulation.simulate():
        assert not last
        if first:
            assert isinstance(e, StartEvent)
            first = False
        else:
            assert not isinstance(e, StartEvent)
        assert isinstance(e, Event)
        last = isinstance(e, EndEvent)
    assert last
    assert isinstance(e, EndEvent)
