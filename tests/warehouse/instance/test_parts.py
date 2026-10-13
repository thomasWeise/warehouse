"""Test the warehouse events."""

from tests.utils import assert_same
from tests.warehouse.instance.test_bin_types import create_default_bin_types
from warehouse.instance.element import context
from warehouse.instance.part import Part


def create_default_parts() -> tuple[Part, ...]:
    """
    Create the default parts for testing.

    :return: the sequence of default parts
    """
    with context():
        return (Part(None, "trousers", "random_small"),
                Part(None, "skirt", "random_small"),
                Part(None, "suitcase", "random_large"),
                Part(None, "shoe", "shoe_bin"),
                Part(None, "sock", "sock_bin"),
                Part(None, "boot", "random_small"))


def test_default_parts() -> None:
    """Test the default parts."""
    keys: set[int] = set()
    names: set[str] = set()

    with context():
        create_default_bin_types()
        mats_1 = create_default_parts()
    for part in mats_1:
        assert isinstance(part, Part)
        assert part.key not in keys
        keys.add(part.key)
        assert part.name not in names
        names.add(part.name)

    assert set.__len__(keys) == set.__len__(names)

    with context():
        create_default_bin_types()
        mats_2 = create_default_parts()
    assert tuple.__len__(mats_2) == tuple.__len__(mats_1)

    for part in mats_2:
        assert isinstance(part, Part)
        keys.remove(part.key)
        names.remove(part.name)

    assert set.__len__(keys) == set.__len__(names)
    assert set.__len__(keys) == 0

    for i in range(tuple.__len__(mats_1)):
        assert mats_1[i] is not mats_2[i]
        assert_same(mats_1[i], mats_2[i])


def test_csv() -> None:
    """Test the csv conversion."""
    with context():
        create_default_bin_types()
        mats_1 = create_default_parts()

    with context():
        create_default_bin_types()
        mats_2 = tuple(Part.from_csv(Part.to_csv(mats_1)))
    assert_same(mats_1, mats_2)
