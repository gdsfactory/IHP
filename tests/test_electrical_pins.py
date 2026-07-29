"""Tests for logical electrical pins registered on IHP PCells."""

from __future__ import annotations

import pytest

import ihp.cells as cells

CELL_NAMES = [
    "npn13G2",
    "npn13G2L",
    "npn13G2V",
    "rsil",
    "rppd",
    "cmom",
    "cmim",
    "bondpad",
    "bondpad_array",
    "via_stack",
    "via_array",
    "via_stack_with_pads",
    "svaricap",
    "ptap1",
    "ntap1",
]


@pytest.mark.parametrize("cell_name", CELL_NAMES)
def test_logical_pin_registered(cell_name):
    """Each PCell should have at least one logical pin registered."""
    cell_func = getattr(cells, cell_name)
    c = cell_func()
    assert len(c.pins) > 0, (
        f"{cell_name} has no logical pins. "
        "Did you forget to call _add_pins(c) before return?"
    )


@pytest.mark.parametrize("cell_name", CELL_NAMES)
def test_port_type_is_electrical(cell_name):
    """Each PCell should have at least one port with port_type='electrical'."""
    cell_func = getattr(cells, cell_name)
    c = cell_func()
    electrical_ports = [p for p in c.ports if p.port_type == "electrical"]
    assert len(electrical_ports) > 0, f"{cell_name} has no electrical ports."
