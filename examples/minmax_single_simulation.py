"""Test the simulation."""

from pycommons.io.console import logger
from pycommons.io.path import Path, write_lines

from warehouse.instance.event import Event
from warehouse.instance.instance import Instance
from warehouse.simulation.simulation import Simulation

use_dir = Path(__file__).up(1).resolve_inside(
    "instances/minmax/02_multi_min")
logger(f"All data comes from and goes into directory {use_dir!r}.")

logger("First loading the scenario.")
instance = Instance.from_directory(use_dir)

logger(f"We got a scenario with {len(instance.parts)} parts, "
       f"{len(instance.bin_types)} bin types, and {len(instance.events)} "
       f"predefined events.")

out_file = use_dir.resolve_inside("output.csv")
logger(f"Now we begin the simulation, writing its output to {out_file!r}.")

simulation = Simulation(instance)
with out_file.open_for_write() as stream:
    write_lines(Event.to_csv(simulation.run()), stream)

logger("The simulation is completed.")
