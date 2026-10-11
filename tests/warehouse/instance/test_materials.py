"""Test the warehouse events."""

from tests.utils import assert_same
from tests.warehouse.instance.test_bin_types import create_default_bin_types
from warehouse.instance.element import context
from warehouse.instance.material import Material


def create_default_materials() -> tuple[Material, ...]:
    """
    Create the default materials for testing.

    :return: the sequence of default materials
    """
    with context():
        return (Material(None, "trousers", "random_small"),
                Material(None, "skirt", "random_small"),
                Material(None, "suitcase", "random_large"),
                Material(None, "shoe", "shoe_bin"),
                Material(None, "sock", "sock_bin"),
                Material(None, "boot", "shoe_bin"))


def test_default_materials() -> None:
    """Test the default materials."""
    keys: set[int] = set()
    names: set[str] = set()

    with context():
        create_default_bin_types()
        mats_1 = create_default_materials()
    for material in mats_1:
        assert isinstance(material, Material)
        assert material.key not in keys
        keys.add(material.key)
        assert material.name not in names
        names.add(material.name)

    assert set.__len__(keys) == set.__len__(names)

    with context():
        create_default_bin_types()
        mats_2 = create_default_materials()
    assert tuple.__len__(mats_2) == tuple.__len__(mats_1)

    for material in mats_2:
        assert isinstance(material, Material)
        keys.remove(material.key)
        names.remove(material.name)

    assert set.__len__(keys) == set.__len__(names)
    assert set.__len__(keys) == 0

    for i in range(tuple.__len__(mats_1)):
        assert mats_1[i] is not mats_2[i]
        assert_same(mats_1[i], mats_2[i])


def test_csv() -> None:
    """Test the csv conversion."""
    with context():
        create_default_bin_types()
        mats_1 = create_default_materials()

    with context():
        create_default_bin_types()
        mats_2 = tuple(Material.from_csv(Material.to_csv(mats_1)))
    assert_same(mats_1, mats_2)
