"""Manual script: DC operating point of vacasktest.nyancir via the vacask simulator.

NOT a pytest test and NOT collected in CI (pytest testpaths = ["tests"]). It is a
manual end-to-end check of VACASK *selection through the Mosaic netlister*.

BLOCKED by a Mosaic netlister bug: ``nyancad.netlist._select_model_entry`` filters
model entries to ``language == "spice"`` BEFORE matching ``implementation``, so the
correctly-labeled ``language="spectre"`` VACASK entry is dropped and a
``sim="vacask"`` run wrongly falls back to the ngspice lib. Until that is fixed,
``inspice_netlist(..., sim="vacask")`` cannot select the VACASK entry shipped by
this PR.

Tracking issue: https://github.com/NyanCAD/Mosaic/issues/201

For a selector-independent proof that the shipped VACASK models compile and solve,
see tests/test_vacask_models.py::test_converted_lib_compiles_and_solves_via_vacask.
"""

import asyncio
import json

import numpy as np
from InSpice import Simulator
from nyancad.netlist import inspice_netlist


async def main():
    with open("vacasktest.nyancir") as f:
        schem_data = json.load(f)

    schem = {"models": {}, "vacasktest": schem_data}

    circuit = await inspice_netlist("vacasktest", schem, sim="vacask")
    print("=== Circuit (SPICE) ===")
    print(circuit)

    simulator = Simulator.factory(simulator="vacask")
    simulation = simulator.simulation(circuit)
    simulation.operating_point()

    print("=== Spectre Netlist ===")
    print(str(simulation))

    print("=== Running simulation ===")
    analysis = simulator.run(simulation)

    print("=== Results ===")
    for node in analysis.nodes.keys():
        print(f"  {node} = {np.array(analysis[node]).item():.6f} V")
    for branch in analysis.branches.keys():
        print(f"  {branch} = {np.array(analysis[branch]).item():.6e} A")


asyncio.run(main())
