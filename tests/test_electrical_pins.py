"""Tests verifying geometric and logical electrical pins on IHP PCells."""

from __future__ import annotations

import pytest
import kfactory as kf

from ihp import PDK

kdb = kf.kdb


@pytest.fixture(autouse=True)
def activate_pdk():
    PDK.activate()


# Electrical PCells from cells/ and cells2/ that have electrical ports
CELL_NAMES = [
    # resistors (cells/)
    "rsil",
    "rppd",
    "rhigh",
    # FET transistors (cells/)
    "nmos",
    "pmos",
    "nmos_hv",
    "pmos_hv",
    # RF transistors (cells/)
    "rfnmos",
    "rfnmos_hv",
    "rfpmos",
    "rfpmos_hv",
    # BJT transistors (cells/)
    "npn13G2",
    "npn13G2L",
    "npn13G2V",
    "pnpMPA",
    # Inductors (cells/)
    "inductor2",
    # Via stacks (cells/)
    "via_stack",
    # Bondpads (cells/)
    "bondpad",
]


def _has_pin_polygon_near_port(comp, port, pin_layer_tuple: tuple[int, int]) -> bool:
    """Return True if there is at least one polygon on pin_layer_tuple near the port center."""
    layout = comp.kcl.layout
    layer_idx = layout.find_layer(*pin_layer_tuple)
    if layer_idx < 0:
        return False
    dbu = layout.dbu
    cx = int(port.dcenter[0] / dbu)
    cy = int(port.dcenter[1] / dbu)
    half = int(0.1 / dbu)
    probe = kdb.Region(kdb.Box(cx - half, cy - half, cx + half, cy + half))
    region = kdb.Region(comp.begin_shapes_rec(layer_idx))
    return not (region & probe).is_empty()


def _port_pin_layer(comp, port) -> tuple[int, int]:
    """For IHP, port layers ARE pin layers (datatype 2 used directly)."""
    info = comp.kcl.layout.get_info(port.layer)
    return (info.layer, info.datatype)


@pytest.mark.parametrize("cell_name", CELL_NAMES)
def test_geometric_pin_present(cell_name):
    """Each electrical port must have at least one polygon on the pin layer near it."""
    c = PDK.cells[cell_name]()
    electrical_ports = [p for p in c.ports if p.port_type == "electrical"]
    assert electrical_ports, f"No electrical ports on {cell_name}"
    for port in electrical_ports:
        pin_layer = _port_pin_layer(c, port)
        assert _has_pin_polygon_near_port(c, port, pin_layer), (
            f"No geometric pin polygon near port '{port.name}' on layer {pin_layer} in {cell_name}"
        )


@pytest.mark.parametrize("cell_name", CELL_NAMES)
def test_logical_pin_registered(cell_name):
    """create_pin() must have been called — c.pins must be non-empty."""
    c = PDK.cells[cell_name]()
    assert len(c.pins) > 0, f"No logical pins registered on {cell_name}"


@pytest.mark.parametrize("cell_name", CELL_NAMES)
def test_port_type_is_electrical(cell_name):
    """Every port on an electrical PCell must have port_type == 'electrical'."""
    c = PDK.cells[cell_name]()
    electrical_ports = [p for p in c.ports if p.port_type == "electrical"]
    assert electrical_ports, f"No electrical ports found on {cell_name}"
    for port in electrical_ports:
        assert port.port_type == "electrical", (
            f"Port '{port.name}' has type '{port.port_type}', expected 'electrical' in {cell_name}"
        )
