"""Test the warehouse part of the simulation."""

from typing import Final, Iterable

from pycommons.io.path import Path, directory_path

from warehouse.event.time import EndEvent, InitializationComplete, StartEvent
from warehouse.instance.element import context
from warehouse.instance.event import Event
from warehouse.instance.instance import Instance
from warehouse.simulation.simulation import Simulation


def __keep(s: str) -> bool:
    """
    Check whether a CSV string is kept or dropped.

    :param s: the string
    :return: `True` for kept strings, `False` for dropped ones.
    """
    assert isinstance(s, str)
    if str.__len__(s) <= 0:
        return False
    return s[0] != "#"


def __str_tuple(s: Iterable[str]) -> tuple[str, ...]:
    """
    Convert an iterable of strings to a tuple.

    :param s: the strings
    :return: the tuple
    """
    return tuple(filter(__keep, map(str.strip, s)))


def __strs_same(a: tuple[str, ...], b: tuple[str, ...]) -> None:
    """
    Check that two string tuples are the same.

    :param a: the first tuple
    :param b: the second tuple
    """
    assert a.__class__ is b.__class__
    assert tuple.__len__(a) == tuple.__len__(b)
    assert a is not b
    if a == b:
        return

    for i, aa in enumerate(a):
        bb = b[i]
        if aa != bb:
            raise ValueError(f"Error in line {i + 1}: {aa!r} != {bb!r}.")


def __check_events(events: Iterable[Event]) -> None:
    """
    Check a sequence of events.

    :param events: the events
    """
    assert isinstance(events, tuple)

    time: int = -1
    first_event: Event | None = None
    last_event: Event | None = None
    init_complete: Event | None = None
    for event in events:
        assert isinstance(event, Event)
        new_time = event.time
        assert new_time >= time
        if first_event is None:
            first_event = event
            assert isinstance(first_event, StartEvent)
        else:
            assert not isinstance(event, StartEvent)
        if isinstance(event, InitializationComplete):
            assert init_complete is None
            init_complete = event
            assert first_event is not None
            assert first_event is not init_complete
            assert first_event.time == init_complete.time

        assert not isinstance(last_event, EndEvent)
        last_event = event

    assert first_event is not None
    assert init_complete is not None
    assert last_event is not None
    assert isinstance(first_event, StartEvent)
    assert isinstance(init_complete, InitializationComplete)
    assert isinstance(last_event, EndEvent)


def __assert_2_events_same(a: Event, b: Event, i: int) -> None:
    """
    Check whether two events are the same.

    :param a: the first event
    :param b: the second event
    :param i: the line
    """
    assert a.__class__ is b.__class__
    assert a is not b
    if a == b:
        return
    a_prio: Final[int] = a.priority
    b_prio: Final[int] = b.priority

    object.__setattr__(a, "priority", b_prio)
    if a != b:
        object.__setattr__(a, "priority", a_prio)
        raise ValueError(f"Error in line {i + 1}: {a!r} != {b!r}.")

    object.__setattr__(a, "priority", a_prio)
    object.__setattr__(b, "priority", a_prio)
    if a != b:
        object.__setattr__(b, "priority", b_prio)
        raise ValueError(f"Error in line {i + 1}: {a!r} != {b!r}.")

    object.__setattr__(b, "priority", b_prio)


def __assert_same_events(a: tuple[Event, ...],
                         b: tuple[Event, ...]) -> None:
    """
    Check that two event sequences are the same.

    :param a: the first sequence
    :param b: the second sequence
    """
    assert a.__class__ is tuple
    assert b.__class__ is tuple
    assert tuple.__len__(a) == tuple.__len__(b)
    assert a is not b
    if a == b:
        return

    for i, aa in enumerate(a):
        __assert_2_events_same(aa, b[i], i)
        __assert_2_events_same(b[i], aa, i)

    for i, bb in enumerate(b):
        __assert_2_events_same(bb, a[i], i)
        __assert_2_events_same(a[i], bb, i)


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

    simulation_1: Simulation = Simulation(instance)
    events_1: Final[tuple[Event, ...]] = tuple(simulation_1.run())
    del simulation_1

    assert isinstance(events_1, tuple)
    __check_events(events_1)

    csv_1_raw: Final[tuple[str, ...]] = tuple(Event.to_csv(events_1))
    csv_1: Final[tuple[str, ...]] = __str_tuple(csv_1_raw)
    assert isinstance(csv_1_raw, tuple)
    for line in csv_1_raw:
        assert isinstance(line, str)

    expected_file: Final[Path] = use_path.resolve_inside(
        "expected_output.csv")
    assert expected_file.exists()
    assert expected_file.is_file()

    with expected_file.open_for_read() as f:
        csv_2_raw: Final[tuple[str, ...]] = tuple(f)
    csv_2: Final[tuple[str, ...]] = __str_tuple(csv_2_raw)
    __strs_same(csv_2, csv_1)

    with context():
        Instance.from_directory(use_path)
        events_2: Final[tuple[Event, ...]] = tuple(Event.from_csv(csv_2_raw))

    __check_events(events_2)
    __assert_same_events(events_2, events_1)

    simulation_2: Simulation = Simulation(instance)
    events_3: Final[tuple[Event, ...]] = tuple(simulation_2.run())
    del simulation_2

    __check_events(events_3)
    __assert_same_events(events_3, events_1)
    __assert_same_events(events_3, events_2)

    with context():
        Instance.from_directory(use_path)
        events_4: tuple[Event, ...] = tuple(Event.from_csv(csv_1_raw))

    __check_events(events_4)
    __assert_same_events(events_4, events_1)
    __assert_same_events(events_4, events_2)
    __assert_same_events(events_4, events_3)
