"""Verify all physical layout cells use drawing layers and port_type='electrical'.

Every add_port() call in physical layout cells must:
1. Use a drawing layer (datatype == 0) instead of a pin sublayer (datatype == 2)
2. Include port_type="electrical"

The gold standard for this pattern is bjt_transistors.py.
"""

from __future__ import annotations

import klayout.db as kdb
import pytest

from ihp import PDK
from ihp.cells import bjt_transistors as bjt_mod
from ihp.cells import bondpads as bondpads_mod
from ihp.cells import capacitors as capacitors_mod
from ihp.cells import fet_transistors as fet_mod
from ihp.cells import inductors as inductors_mod
from ihp.cells import passives as passives_mod
from ihp.cells import resistors as resistors_mod
from ihp.cells import rf_transistors as rf_mod
from ihp.cells import via_stacks as via_mod


@pytest.fixture(autouse=True)
def activate_pdk():
    PDK.activate()


CELLS_TO_TEST = [
    # FET transistors
    ("nmos", fet_mod.nmos, {}),
    ("pmos", fet_mod.pmos, {}),
    ("nmos_hv", fet_mod.nmos_hv, {}),
    ("pmos_hv", fet_mod.pmos_hv, {}),
    # RF transistors
    ("rfnmos", rf_mod.rfnmos, {}),
    ("rfpmos", rf_mod.rfpmos, {}),
    ("rfnmos_hv", rf_mod.rfnmos_hv, {}),
    ("rfpmos_hv", rf_mod.rfpmos_hv, {}),
    # Inductors
    ("inductor2_1turn", inductors_mod.inductor2, {"turns": 1}),
    ("inductor2_2turn", inductors_mod.inductor2, {"turns": 2}),
    # Resistors
    ("rsil", resistors_mod.rsil, {}),
    ("rppd", resistors_mod.rppd, {}),
    ("rhigh", resistors_mod.rhigh, {}),
    # Passives
    ("svaricap", passives_mod.svaricap, {}),
    ("esd_nmos", passives_mod.esd_nmos, {}),
    ("ptap1", passives_mod.ptap1, {}),
    ("ntap1", passives_mod.ntap1, {}),
    # Capacitors
    ("cmom", capacitors_mod.cmom, {}),
    ("cmim", capacitors_mod.cmim, {}),
    ("rfcmim", capacitors_mod.rfcmim, {}),
    # BJT transistors
    ("npn13G2", bjt_mod.npn13G2, {}),
    ("pnpMPA", bjt_mod.pnpMPA, {}),
    # Bondpads
    ("bondpad", bondpads_mod.bondpad, {}),
    ("bondpad_array", bondpads_mod.bondpad_array, {}),
    # Via stacks
    ("via_stack", via_mod.via_stack, {}),
    ("via_stack_with_pads", via_mod.via_stack_with_pads, {}),
]


def _resolve_layer(comp, port) -> tuple[int, int]:
    """Resolve port layer index to (layer_number, datatype) tuple."""
    layer_idx = port.layer
    info = comp.kcl.layout.get_info(layer_idx)
    return (info.layer, info.datatype)


@pytest.mark.parametrize(
    "name,factory,kwargs",
    CELLS_TO_TEST,
    ids=[t[0] for t in CELLS_TO_TEST],
)
def test_port_type_is_electrical(name, factory, kwargs):
    """Every port on a physical cell must have port_type='electrical'."""
    comp = factory(**kwargs)
    assert len(comp.ports) > 0, f"{name} has no ports"
    for port in comp.ports:
        assert port.port_type == "electrical", (
            f"{name}.ports['{port.name}'] has port_type='{port.port_type}', "
            f"expected 'electrical'"
        )


@pytest.mark.parametrize(
    "name,factory,kwargs",
    CELLS_TO_TEST,
    ids=[t[0] for t in CELLS_TO_TEST],
)
def test_port_layer_is_drawing(name, factory, kwargs):
    """Every port layer must be a drawing layer (datatype == 0), not pin (2)."""
    comp = factory(**kwargs)
    assert len(comp.ports) > 0, f"{name} has no ports"
    for port in comp.ports:
        layer_num, datatype = _resolve_layer(comp, port)
        assert datatype == 0, (
            f"{name}.ports['{port.name}'] layer=({layer_num}, {datatype}), "
            f"expected datatype=0 (drawing layer)"
        )


@pytest.mark.parametrize(
    "name,factory,kwargs",
    CELLS_TO_TEST,
    ids=[t[0] for t in CELLS_TO_TEST],
)
def test_port_overlaps_drawing(name, factory, kwargs):
    """Each port must overlap drawing geometry on the same layer."""
    comp = factory(**kwargs)
    assert len(comp.ports) > 0, f"{name} has no ports"
    kcell = comp._kf_cell if hasattr(comp, "_kf_cell") else comp
    layout = kcell.layout()

    for port in comp.ports:
        layer_num, datatype = _resolve_layer(comp, port)
        draw_li = layout.find_layer(layer_num, datatype)
        assert draw_li is not None, (
            f"{name}.ports['{port.name}'] layer ({layer_num}, {datatype}) "
            f"not found in layout"
        )

        draw_region = kdb.Region(kcell.begin_shapes_rec(draw_li))
        dbu = layout.dbu
        x, y = port.center
        x_dbu = int(round(x / dbu))
        y_dbu = int(round(y / dbu))
        probe = kdb.Region(kdb.Box(x_dbu - 10, y_dbu - 10, x_dbu + 10, y_dbu + 10))
        overlap = draw_region & probe
        assert not overlap.is_empty(), (
            f"{name}.ports['{port.name}'] at ({x}, {y}) on layer "
            f"({layer_num}, {datatype}) does not overlap drawing geometry"
        )
