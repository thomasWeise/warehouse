"""
The possible events that can be encountered during the simulation.

These include

- events related to the simulation time, such as
  :class:`~warehouse.event.time.StartEvent` and
  :class:`~warehouse.event.time.EndEvent`,
- events related to storing parts into a warehouse or retrieving them,
  as implemented in :mod:`~warehouse.event.storage`, as well as
- events related to storing parts into bins of a given type inside
   warehouse or retrieving them from such as bins, as implemented in
   :mod:`~warehouse.event.bins`.
"""
