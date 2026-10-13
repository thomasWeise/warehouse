"""
The start and end events of the simulation.

>>> ev1 = StartEvent(time=1500000000000)
>>> ev1
StartEvent(time=1500000000000)

>>> ev2 = EndEvent(time=1750000000000)
>>> ev2
EndEvent(time=1750000000000)

>>> csv = list(Event.to_csv((ev1, ev2)))
>>> for row in csv[1:]:
...     if not str.startswith(row, "#"):
...         print(row)
2017-07-14T10:40+08;start
2025-06-15T23:06:40+08;end

>>> ev3, ev4 = list(Event.from_csv(csv))
>>> print(ev3)
StartEvent(time=1500000000000)
>>> print(ev4)
EndEvent(time=1750000000000)

>>> hash(ev3)
-4526921868353943795
"""

from warehouse.instance.event import Event


class StartEvent(Event):
    """The simulation begins."""

    @classmethod
    def eventclass_get_csv_type(cls) -> str:
        """
        Get the csv type of the event.

        :return: the csv type
        """
        return "start"

    @classmethod
    def eventclass_get_event_desc(cls) -> str | None:
        """
        Get the event description.

        :return: the event description, if any
        """
        return "the time when the simulation begins"


class EndEvent(Event):
    """The simulation ends or is aborted."""

    @classmethod
    def eventclass_get_csv_type(cls) -> str:
        """
        Get the csv type of the event.

        :return: the csv type
        """
        return "end"

    @classmethod
    def eventclass_get_event_desc(cls) -> str | None:
        """
        Get the event description.

        :return: the event description, if any
        """
        return ("the time when the simulation ends, or, alternatively, after "
                "which it should be aborted and all other events still in "
                "the queue are discarded")
