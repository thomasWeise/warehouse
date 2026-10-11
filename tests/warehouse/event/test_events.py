"""Test the warehouse events."""

from typing import Final

from pycommons.io.path import Path, write_lines

from tests.utils import assert_same
from tests.warehouse.instance.test_bin_types import create_default_bin_types
from tests.warehouse.instance.test_materials import create_default_materials
from warehouse.event.bins import BinIn, BinOut
from warehouse.event.storage import (
    OverstockIn,
    WarehouseIn,
    WarehouseOut,
)
from warehouse.event.time import EndEvent, StartEvent
from warehouse.instance.element import context
from warehouse.instance.event import Event
from warehouse.instance.time import str_to_time


def create_default_events() -> tuple[Event, ...]:
    """
    Create the default events for testing.

    :return: the sequence of events for testing
    """
    start: Final[int] = str_to_time("2026-01-01T09:00+08")
    end: Final[int] = str_to_time("2026-12-31T17:00+08")
    delta: Final[int] = ((end - start) // 256)
    time: Final[list[int]] = [start]

    def __next() -> int:
        """Get the next time."""
        ret = time[0] + delta
        time[0] = ret
        return ret

    with context():
        return (StartEvent(__next()),
                WarehouseIn(__next(), "skirt", 233),
                BinIn(__next(), "skirt", 233, "random_small"),
                WarehouseIn(__next(), "trousers", 1500),
                BinIn(__next(), "trousers", 709, "random_small"),
                OverstockIn(__next(), "trousers", 791),
                BinOut(__next(), "trousers", 709, "random_small"),
                BinIn(__next(), "trousers", 709, "random_small"),
                BinOut(__next(), "trousers", 709, "random_small"),
                WarehouseOut(__next(), "trousers", 1418),
                BinIn(__next(), "trousers", 82, "random_small"),
                BinOut(__next(), "skirt", 200, "random_small"),
                WarehouseOut(__next(), "skirt", 200),
                BinOut(__next(), "skirt", 33, "random_small"),
                WarehouseOut(__next(), "skirt", 33),
                EndEvent(__next()))


def test_default_events() -> None:
    """Test the default events."""
    with context():
        create_default_bin_types()
        create_default_materials()
        events_1 = create_default_events()
    for event in events_1:
        assert isinstance(event, Event)
        event_2 = event.copy()
        assert event_2 is not event
        assert_same(event_2, event)
        assert event_2 == event
        assert not (event_2 != event)  # noqa

    with context():
        create_default_bin_types()
        create_default_materials()
        events_2 = create_default_events()
    for event in events_2:
        assert isinstance(event, Event)
        event_2 = event.copy()
        assert event_2 is not event
        assert_same(event_2, event)
        assert event_2 == event
        assert not (event_2 != event)  # noqa

    assert tuple.__len__(events_2) == tuple.__len__(events_1)

    for i in range(tuple.__len__(events_1)):
        assert events_1[i] is not events_2[i]
        assert_same(events_1[i], events_2[i])
        assert events_1[i] == events_2[i]
        assert not (events_1[i] != events_2[i])  # noqa


def test_csv() -> None:
    """Test the conversion to and from csv."""
    with context():
        create_default_bin_types()
        create_default_materials()

        events_1 = create_default_events()
        text_1 = list(Event.to_csv(events_1))
        events_2 = tuple(Event.from_csv(text_1))

    assert events_1 == events_2
    for index, event_1 in enumerate(events_1):
        assert_same(event_1, events_2[index])

    text_2 = list(Event.to_csv(events_2))
    assert text_1 == text_2


def create_test_csv_resource() -> None:
    """Create the test resource."""
    test_path = Path(__file__).up().resolve_inside("events.csv")
    with context():
        create_default_bin_types()
        create_default_materials()
        events = create_default_events()
        with test_path.open_for_write() as stream:
            write_lines(Event.to_csv(events), stream)


# create the csv resource
create_test_csv_resource()
