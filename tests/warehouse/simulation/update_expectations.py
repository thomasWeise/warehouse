"""Update the expectations."""

from typing import Final

from pycommons.io.path import Path, directory_path

from warehouse.instance.event import Event
from warehouse.instance.instance import FILE_PARTS, Instance
from warehouse.simulation.simulation import Simulation


def update_expectation(use_dir: str = Path(
        __file__).up(4).resolve_inside(
        "examples/instances/warehouse/small_warehouse")) -> None:
    """
    Update the warehouse simulation expectations.

    :param use_dir: The directory to load the simulation from.
    """
    use_path: Final[Path] = directory_path(use_dir)
    assert use_path.exists()
    assert use_path.is_dir()

    instance: Final[Instance] = Instance.from_directory(use_path)
    assert isinstance(instance, Instance)

    simulation_1: Final[Simulation] = Simulation(instance)
    csv_result_1: Final[tuple[str, ...]] = tuple(Event.to_csv(
        simulation_1.run()))
    assert isinstance(csv_result_1, tuple)
    for line in csv_result_1:
        assert isinstance(line, str)

    expected_file: Final[Path] = use_path.resolve_inside(
        "expected_output.csv")

    with expected_file.open_for_write() as f:
        for line in csv_result_1:
            if line.startswith("#"):
                continue
            f.write(f"{line}\n")


def update_expectations(use_dir: str = Path(
        __file__).up(4).resolve_inside(
        "examples/instances/warehouse")) -> None:
    """
    Update all expectations recursively.

    :param use_dir: the base directory
    """
    use_dir = directory_path(use_dir)
    assert use_dir.exists()
    assert use_dir.is_dir()

    if use_dir.resolve_inside(FILE_PARTS).exists():
        update_expectation(use_dir=use_dir)
    else:
        for sub_dir in use_dir.list_dir(files=False, directories=True):
            update_expectations(use_dir=sub_dir)


if __name__ == "__main__":
    update_expectations(use_dir=Path(__file__).up(4).resolve_inside(
        "examples/instances"))
