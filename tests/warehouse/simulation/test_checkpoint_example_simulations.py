"""Test the checkpoints part of the simulation."""

from pycommons.io.path import Path

from tests.warehouse.simulation.run_simulation import run_and_test_simulation


def test_checkpoints_simulation() -> None:
    """Test all the checkpoints example simulations."""
    root = Path(__file__).up(4).resolve_inside(
        "examples/instances/checkpoints")
    assert root.exists()
    assert root.is_dir()

    for sub_dir in root.list_dir(files=False, directories=True):
        run_and_test_simulation(sub_dir)
