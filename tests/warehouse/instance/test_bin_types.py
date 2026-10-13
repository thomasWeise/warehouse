"""Create and test the default bin types."""

from tests.utils import assert_same
from warehouse.instance.bin_type import BinType
from warehouse.instance.element import context


def create_default_bin_types() -> tuple[BinType, ...]:
    """
    Create the default bin types for testing.

    :return: the sequence of default bin types
    """
    with context():
        return (BinType(None, "random_small", 1024, True),
                BinType(None, "random_large", 512, True),
                BinType(None, "hat_bins", 256, False),
                BinType(None, "shoe_bin", 128, False),
                BinType(None, "sock_bin", 64, False))


def test_default_bin_types() -> None:
    """Test the default bin types."""
    keys: set[int] = set()
    names: set[str] = set()

    bin_types_1 = create_default_bin_types()

    for bin_type in bin_types_1:
        assert isinstance(bin_type, BinType)
        assert bin_type.key not in keys
        keys.add(bin_type.key)
        assert bin_type.name not in names
        names.add(bin_type.name)

    assert set.__len__(keys) == set.__len__(names)

    bin_types_2 = create_default_bin_types()
    assert tuple.__len__(bin_types_2) == tuple.__len__(bin_types_1)

    for bin_type in bin_types_2:
        assert isinstance(bin_type, BinType)
        keys.remove(bin_type.key)
        names.remove(bin_type.name)

    assert set.__len__(keys) == set.__len__(names)
    assert set.__len__(keys) == 0

    for i in range(tuple.__len__(bin_types_1)):
        assert bin_types_1[i] is not bin_types_2[i]
        assert_same(bin_types_1[i], bin_types_2[i])


def test_csv() -> None:
    """Test the csv conversion."""
    bins_1 = create_default_bin_types()
    bins_2 = tuple(BinType.from_csv(BinType.to_csv(bins_1)))
    assert_same(bins_1, bins_2)
