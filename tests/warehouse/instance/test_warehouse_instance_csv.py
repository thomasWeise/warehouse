"""Test the warehouse scenario/instance."""


from pycommons.io.path import Path

from tests.utils import assert_same
from warehouse.instance.instance import Instance


def test_csv() -> None:
    """Test the conversion to and from csv files."""
    test_dir = Path(__file__).up().resolve_inside("warehouse_instance")
    instance_1 = Instance.from_directory(test_dir)

    # now we are done loading, we can import the other stuff
    from importlib import import_module  # noqa  # pylint: disable=C0415
    module = import_module("tests.warehouse.instance.test_warehouse_instance")
    create_default_instance = module.create_default_instance
    instance_2 = create_default_instance()

    assert instance_1 is not instance_2
    assert_same(instance_1, instance_2)
