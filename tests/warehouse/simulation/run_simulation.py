"""Test the warehouse part of the simulation."""

from typing import Final

from pycommons.io.path import Path, directory_path

from warehouse.event.time import EndEvent, StartEvent
from warehouse.instance.element import context
from warehouse.instance.event import Event
from warehouse.instance.instance import Instance
from warehouse.simulation.simulation import Simulation


def run_and_test_simulation(use_dir: str = Path(
        __file__).up(4).resolve_inside(
        "examples/instances/warehouse/small_warehouse")) -> None:
    """
    Test the warehouse simulation.

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
    assert expected_file.exists()
    assert expected_file.is_file()

    with expected_file.open_for_read() as f:
        expected_csv: Final[tuple[str, ...]] = tuple(filter(
            lambda s: not str.startswith(s, "#"), map(str.rstrip, f)))
    assert expected_csv == tuple(filter(
        lambda s: not str.startswith(s, "#"), csv_result_1))

    with context():
        Instance.from_directory(use_path)
        with expected_file.open_for_read() as f:
            expected_events: Final[tuple[Event, ...]] = tuple(
                Event.from_csv(f))

    time: int = -1
    first_event: Event | None = None
    last_event: Event | None = None
    for event in expected_events:
        assert isinstance(event, Event)
        new_time = event.time
        assert new_time >= time
        if first_event is None:
            first_event = event
            assert isinstance(first_event, StartEvent)
        else:
            assert not isinstance(event, StartEvent)
        assert not isinstance(last_event, EndEvent)
        last_event = event

    assert first_event is not None
    assert isinstance(first_event, StartEvent)
    assert isinstance(last_event, EndEvent)

    simulation_2: Final[Simulation] = Simulation(instance)
    assert expected_events == tuple(simulation_2.run())
