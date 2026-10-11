"""Test the warehouse scenario/instance."""


from pycommons.io.path import Path
from pycommons.io.temp import temp_dir

from tests.utils import assert_same
from tests.warehouse.event.test_events import create_default_events
from tests.warehouse.instance.test_bin_types import create_default_bin_types
from tests.warehouse.instance.test_materials import create_default_materials
from warehouse.instance.element import context
from warehouse.instance.instance import Instance


def create_default_instance() -> Instance:
    """
    Create the default events for testing.

    :return: the sequence of events for testing
    """
    with context():
        return Instance(create_default_bin_types(),
                        create_default_materials(),
                        create_default_events())


def test_default_instance() -> None:
    """Test the default instance."""
    instance_1 = create_default_instance()
    instance_2 = create_default_instance()

    assert instance_1 is not instance_2
    assert_same(instance_1, instance_2)


def test_csv() -> None:
    """Test the conversion to and from csv files."""
    with temp_dir() as td:
        instance_1 = create_default_instance()
        instance_2 = Instance.from_directory(instance_1.to_directory(td))

    assert instance_1 is not instance_2
    assert_same(instance_1, instance_2)


def create_test_resource() -> None:
    """Create the test resource."""
    test_dir = Path(__file__).up().resolve_inside("warehouse_instance")
    create_default_instance().to_directory(test_dir)


# create the csv resource
create_test_resource()
