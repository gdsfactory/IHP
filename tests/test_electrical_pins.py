"""Tests for logical electrical pins registered on IHP PCells."""

from __future__ import annotations

import pytest

import ihp.cells as cells

# Cells with fixed port names: assert the exact pin set.
EXPECTED_PIN_NAMES: dict[str, set[str]] = {
    # BJT transistors
    "npn13G2": {"C", "B", "E"},
    "npn13G2L": {"C", "B", "E"},
    "npn13G2V": {"C", "B", "E"},
    "pnpMPA": {"TIE", "PLUS", "MINUS"},
    # FET transistors (double-call fixed; pins come from _mos_core)
    "nmos": {"S", "D", "G"},
    "pmos": {"S", "D", "G"},
    "nmos_hv": {"S", "D", "G"},
    "pmos_hv": {"S", "D", "G"},
    # RF transistors (TIE present at default guard_ring="Yes")
    "rfnmos": {"S", "D", "G", "TIE"},
    "rfpmos": {"S", "D", "G", "TIE"},
    "rfnmos_hv": {"S", "D", "G", "TIE"},
    "rfpmos_hv": {"S", "D", "G", "TIE"},
    # Capacitors
    "cmom": {"PLUS", "MINUS"},
    "cmim": {"PLUS", "MINUS"},
    "rfcmim": {"PLUS", "MINUS", "TIE_LOW"},
    # Resistors
    "rsil": {"P1", "P2"},
    "rppd": {"P1", "P2"},
    "rhigh": {"P1", "P2"},
    # Bondpads (fixed single pad)
    "bondpad": {"pad"},
    # Via stacks
    "via_stack_with_pads": {"pad1", "pad2"},
    # Passives
    "svaricap": {"G", "B"},
    "esd_nmos": {"PAD", "GND"},
    "ptap1": {"TAP"},
    "ntap1": {"TAP"},
    # RF devices (singleton ports)
    "branch_line_coupler": {"e1", "e2", "e3", "e4"},
    "wilkinson_power_divider": {"e1", "e2", "e3"},
    "quarter_wave_transformer": {"e1", "e2"},
    "coupled_line_bandpass_filter": {"e1", "e2"},
    "hairpin_coupled_line_bandpass_filter": {"e1", "e2"},
    # RF devices (grouped ports — ports sharing a conductor polygon)
    "directional_coupler": {"e1", "e3"},
    # Waveguides (tline primitives: e1+e2 share signal conductor → one pin "e1")
    "tline": {"e1"},
    "tline_bend_circular": {"e1"},
    "tline_bend_euler": {"e1"},
    "tline_bend_s": {"e1"},
    "tline_corner": {"e1"},
    "coupler_tline": {"e1", "e3"},
}

# Cells with dynamic port names (depend on parameters) — only assert non-empty.
DYNAMIC_CELL_NAMES = [
    "bondpad_array",
    "via_stack",
    "inductor2",
    # stdcells omitted (slow GDS import); tested separately if needed
]


@pytest.mark.parametrize("cell_name,expected", EXPECTED_PIN_NAMES.items())
def test_pin_names(cell_name, expected):
    """Cell must expose exactly the expected set of logical pin names."""
    c = getattr(cells, cell_name)()
    assert {p.name for p in c.pins} == expected, (
        f"{cell_name}: got {sorted(p.name for p in c.pins)}, "
        f"expected {sorted(expected)}"
    )


@pytest.mark.parametrize("cell_name", DYNAMIC_CELL_NAMES)
def test_dynamic_cell_has_pins(cell_name):
    """Dynamic-port cells must register at least one logical pin."""
    c = getattr(cells, cell_name)()
    assert len(c.pins) > 0, f"{cell_name} has no logical pins."


@pytest.mark.parametrize(
    "cell_name",
    list(EXPECTED_PIN_NAMES) + DYNAMIC_CELL_NAMES,
)
def test_port_type_is_electrical(cell_name):
    """Each PCell must have at least one port with port_type='electrical'."""
    c = getattr(cells, cell_name)()
    electrical = [p for p in c.ports if p.port_type == "electrical"]
    assert len(electrical) > 0, f"{cell_name} has no electrical ports."
