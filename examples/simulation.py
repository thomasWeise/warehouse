"""Test the simulation."""

from pycommons.io.console import logger
from pycommons.io.path import Path, write_lines

from warehouse.instance.event import Event
from warehouse.instance.scenario import Scenario
from warehouse.simulation.simulation import Simulation

use_dir = Path(__file__).up(1).resolve_inside("scenario/small")
logger(f"All data comes from and goes into directory {use_dir!r}.")

logger("First loading the scenario.")
scenario = Scenario.from_directory(use_dir)

logger(f"We got a scenario with {scenario.n_materials} materials, "
       f"{scenario.n_bins} bins, and {scenario.n_events} predefined events.")

out_file = use_dir.resolve_inside("output.csv")
logger(f"Now we begin the simulation, writing its output to {out_file!r}.")

simulation = Simulation(scenario)
with out_file.open_for_write() as stream:
    write_lines(Event.to_csv(simulation.simulate()), stream)

logger("The simulation is completed.")
