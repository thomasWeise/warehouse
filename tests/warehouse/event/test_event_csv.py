"""Test the warehouse events."""

from pycommons.io.path import Path

from tests.utils import assert_same
from tests.warehouse.instance.test_bin_types import create_default_bin_types
from tests.warehouse.instance.test_materials import create_default_materials
from warehouse.instance.element import context
from warehouse.instance.event import Event


def test_csv_loading() -> None:
    """Test loading data from the test resource."""
    test_csv = Path(__file__).up().resolve_inside("events.csv")
    with context():
        create_default_bin_types()
        create_default_materials()
        with test_csv.open_for_read() as stream:
            events_1 = tuple(Event.from_csv(stream))

    # now we are done loading, we can import the other stuff
    from importlib import import_module  # noqa  # pylint: disable=C0415
    module = import_module("tests.warehouse.event.test_events")
    create_default_events = module.create_default_events

    with context():
        create_default_bin_types()
        create_default_materials()
        events_2 = create_default_events()

    assert_same(events_1, events_2)
