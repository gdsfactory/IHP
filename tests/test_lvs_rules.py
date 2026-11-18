"""Smoke tests for the gflvs LVS rules (skipped when gflvs is not installed)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest

gflvs = pytest.importorskip("gflvs")

import gdstk  # noqa: E402
from gflvs.gflvs_refactor import ElectricalDeviceExtractionPolicy  # noqa: E402
from gflvs.gflvs_schema import LayerBooleanOperation, LvsRunMode  # noqa: E402

from ihp import cells  # noqa: E402
from ihp.lvs import rules  # noqa: E402
from ihp.tech import LAYER  # noqa: E402

GROUP_FLAGS = {
    "ENABLE_MOSFET_TEMPLATES": "MOSFET_TEMPLATES",
    "ENABLE_RF_MOSFET_TEMPLATES": "RF_MOSFET_TEMPLATES",
    "ENABLE_BJT_TEMPLATES": "BJT_TEMPLATES",
    "ENABLE_RESISTOR_TEMPLATES": "RESISTOR_TEMPLATES",
    "ENABLE_CAPACITOR_TEMPLATES": "CAPACITOR_TEMPLATES",
    "ENABLE_VARACTOR_TEMPLATES": "VARACTOR_TEMPLATES",
    "ENABLE_ESD_TEMPLATES": "ESD_TEMPLATES",
    "ENABLE_INDUCTOR_TEMPLATES": "INDUCTOR_TEMPLATES",
    "ENABLE_PAD_TEMPLATES": "PAD_TEMPLATES",
    "ENABLE_DIODE_TEMPLATES": "DIODE_TEMPLATES",
}


def test_default_config_builds() -> None:
    assert isinstance(rules.DEFAULT_LVS_CONFIG, gflvs.LvsConfig)


def test_connectivity_symmetric() -> None:
    connectivity = rules.LAYER_CONNECTIVITY
    assert all(a in connectivity[b] for a, bs in connectivity.items() for b in bs)


# every template, including groups that are off by default (RF MOS)
ALL_TEMPLATES = [t for _, group in rules._groups() for t in group]


def test_template_layers_in_pdk() -> None:
    pdk_layers = {(int(layer.layer), int(layer.datatype)) for layer in cast(Any, LAYER)}
    used = rules.template_layers(ALL_TEMPLATES) | set(rules.LAYER_CONNECTIVITY)
    assert used <= pdk_layers


def _positive_leaves(operation: Any) -> Iterator[tuple[int, int]]:
    """Leaf layers an op requires: the right operand of a NOT (difference) is skipped."""
    is_not = (
        operation.WhichOneof("operation") == "bool_op"
        and operation.bool_op == LayerBooleanOperation.LAYER_BOOLEAN_OPERATION_NOT
    )
    for side in ("left",) if is_not else ("left", "right"):
        field = operation.WhichOneof(f"layer_{side}")
        if field is None:
            continue
        if field.startswith("layer_ref"):
            layer = getattr(operation, field).layer
            yield (layer.layer, layer.datatype)
        else:
            yield from _positive_leaves(getattr(operation, field))


def test_terminals_use_markers() -> None:
    for t in ALL_TEMPLATES:
        if t.device_name in rules.NO_MARKER_TEMPLATES:
            continue
        for term in t.device_terminal_template:
            leaves = set(_positive_leaves(term.layer_composed_op))
            assert leaves & rules.MARKER_LAYERS, f"{t.device_name}.{term.terminal_name}"


def test_flags_toggle(monkeypatch: pytest.MonkeyPatch) -> None:
    default = rules.build_lvs_config()
    assert default.netlist_tracer_config.galvanic_drawing_layers
    assert len(default.device_templates) == len(rules.DEVICE_TEMPLATES)

    with monkeypatch.context() as m:
        m.setattr(rules, "ENABLE_ELECTRICAL_TRACING", False)
        assert (
            rules.build_lvs_config().netlist_tracer_config.galvanic_drawing_layers
            == frozenset()
        )

    with monkeypatch.context() as m:
        m.setattr(rules, "ENABLE_DEVICE_EXTRACTION", False)
        assert rules.build_lvs_config().device_templates == []

    with monkeypatch.context() as m:
        m.setattr(rules, "ENABLE_PARAMETER_CHECK", False)
        cfg = rules.build_lvs_config()
        assert all(t.properties["blackbox"] == "true" for t in cfg.device_templates)
        assert all("blackbox" not in t.properties for t in rules.DEVICE_TEMPLATES)

    for flag, group in GROUP_FLAGS.items():
        with monkeypatch.context() as m:
            m.setattr(rules, flag, False)
            names = [t.device_name for t in rules.build_lvs_config().device_templates]
            removed = {t.device_name for t in getattr(rules, group)}
            assert names == [
                t.device_name
                for t in rules.DEVICE_TEMPLATES
                if t.device_name not in removed
            ], flag

    with monkeypatch.context() as m:
        m.setattr(rules, "ENABLE_RF_MOSFET_TEMPLATES", True)  # off by default
        rf_on = {t.device_name for t in rules.build_lvs_config().device_templates}
        assert {t.device_name for t in rules.RF_MOSFET_TEMPLATES} <= rf_on

    with monkeypatch.context() as m:
        m.setattr(rules, "HIERARCHICAL_RUN", True)
        assert rules.build_lvs_config().run_mode == LvsRunMode.LVS_RUN_MODE_HIERARCHICAL


def _library(component: Any, tmp_path: Any) -> gdstk.Library:
    gds = tmp_path / f"{component.name}.gds"
    component.write_gds(gds)
    library = gdstk.read_gds(str(gds))
    # kfactory also writes a $$$CONTEXT_INFO$$$ top cell
    library.remove(*[c for c in library.cells if c.name.startswith("$$$")])
    return library


def test_mos_terminals_on_traced_nets(tmp_path: Any) -> None:
    """Rule 2: S/D/G land on traced nets in a full tracer + extraction run."""
    component = cells.nmos(nf=3, width=0.6)
    cfg = rules.DEFAULT_LVS_CONFIG
    _, l2n, _ = gflvs.layout_to_netlist(
        _library(component, tmp_path),
        component.name,
        device_templates=cfg.device_templates,
        nettracer_config=cfg.netlist_tracer_config,
        electrical_device_extraction_config=cfg.electrical_device_extraction_config,
    )
    (device,) = [r for d in l2n.devices for r in d.device_references]
    nets = {t.name: t.parent_net.net_name for t in device.terminals}
    assert sorted(nets) == ["D", "G", "S"]
    assert len(set(nets.values())) == 3, nets
    # a floating terminal gets a bare Net$k with no traced shapes
    traced = {n.name for n in l2n.nets if n.connected_shapes}
    assert set(nets.values()) <= traced, nets


# one row per HIGH-confidence template, values verified in templates-ihp.md
EXTRACT_CASES: list[Any] = [
    ("nmos", {}, "nmos", 3, {"width": 0.15, "length": 0.13, "nf": 1}),
    (
        "nmos",
        {"nf": 3, "width": 0.6},
        "nmos",
        3,
        {"width": 0.6, "length": 0.13, "nf": 3},
    ),
    (
        "pmos",
        {"nf": 2, "width": 1.0},
        "pmos",
        3,
        {"width": 1.0, "length": 0.13, "nf": 2},
    ),
    ("nmos_hv", {"length": 0.6}, "nmos_hv", 3, {"width": 0.6, "length": 0.6, "nf": 1}),
    (
        "pmos_hv",
        {"nf": 2, "width": 1.0, "length": 0.6},
        "pmos_hv",
        3,
        {"width": 1.0, "length": 0.6, "nf": 2},
    ),
    (
        "npn13G2",
        {"Nx": 2},
        "npn13G2",
        3,
        {"emitter_width": 0.7, "emitter_length": 0.9, "Nx": 2},
    ),
    (
        "npn13G2L",
        {"emitter_length": 2.0},
        "npn13G2L",
        3,
        {"emitter_width": 0.07, "emitter_length": 2.0, "Nx": 1},
    ),
    (
        "npn13G2V",
        {"Nx": 3},
        "npn13G2V",
        3,
        {"emitter_width": 0.12, "emitter_length": 1.0, "Nx": 3},
    ),
    ("pnpMPA", {}, "pnpMPA", 3, {"width": 0.7, "length": 2.0}),
    (
        "pnpMPA",
        {"length": 4.0, "width": 1.2},
        "pnpMPA",
        3,
        {"width": 1.2, "length": 4.0},
    ),
    ("rsil", {"dx": 1.0, "dy": 3.0}, "rsil", 2, {"dx": 1.0, "dy": 3.0}),
    ("rppd", {"dx": 2.0, "dy": 5.0}, "rppd", 2, {"dx": 2.0, "dy": 5.0}),
    (
        "rhigh",
        {"dx": 1.5, "dy": 7.0},
        "rhigh",
        2,
        {"dx": 1.5, "dy": 7.0},
    ),
    # cmim w/l are the MIM extents, as the IHP deck measures them (w = x, l = y); the PCell
    # draws MIM 0.72 um larger than its width (y) / length (x) arguments
    ("cmim", {}, "cmim", 2, {"width": 6.72, "length": 6.72}),
    ("cmim", {"width": 8.0, "length": 5.0}, "cmim", 2, {"width": 5.72, "length": 8.72}),
]


@pytest.mark.parametrize("pcell, kwargs, device, n_terminals, params", EXTRACT_CASES)
def test_pcell_extracts(
    pcell: str,
    kwargs: dict[str, Any],
    device: str,
    n_terminals: int,
    params: dict[str, float],
    tmp_path: Any,
) -> None:
    component = getattr(cells, pcell)(**kwargs)
    top = next(
        c
        for c in _library(component, tmp_path).cells
        if isinstance(c, gdstk.Cell) and c.name == component.name
    )
    cfg = rules.DEFAULT_LVS_CONFIG
    results = ElectricalDeviceExtractionPolicy().execute(
        top, rules.DEVICE_TEMPLATES, cfg.electrical_device_extraction_config
    )
    devices = [r.unwrap() for r in results]
    assert [d.class_name for d in devices] == [device]
    assert len(devices[0].terminals) == n_terminals
    # terminal names are the PCell's logical pins, its port names where it registers none
    pins = {p.name for p in component.pins} or {p.name for p in component.ports}
    assert {t.name for t in devices[0].terminals} == pins
    got = {p.name: p.value for p in devices[0].parameters}
    for name, value in params.items():
        assert got[name] == pytest.approx(value, rel=1e-3), name


def _devices(cell: gdstk.Cell) -> list[Any]:
    results = ElectricalDeviceExtractionPolicy().execute(
        cell,
        rules.DEVICE_TEMPLATES,
        rules.DEFAULT_LVS_CONFIG.electrical_device_extraction_config,
    )
    return [r.unwrap() for r in results]


# cut from IHP-Open-PDK testcases (Apache-2.0) @ e73adb40 unit/cap_devices: they draw no MemCap/Varicap
OFFICIAL = Path(__file__).parent / "lvs_official"


@pytest.mark.parametrize(
    "gds, device",
    [("sg13_hv_svaricap_cell.gds", "svaricap"), ("cap_cmim_one.gds", "cmim")],
)
def test_official_layout_extracts(gds: str, device: str) -> None:
    (top,) = gdstk.read_gds(str(OFFICIAL / gds)).top_level()
    assert isinstance(top, gdstk.Cell)
    assert [d.class_name for d in _devices(top)] == [device]


def test_std_cell_is_plain_mos(tmp_path: Any) -> None:
    """sg13g2_inv_2 is one nmos + one pmos, never rfnmos/rfpmos (the IHP deck reads it so)."""
    component = cells.sg13g2_inv_2()
    library = _library(component, tmp_path)
    top = next(
        c
        for c in library.cells
        if isinstance(c, gdstk.Cell) and c.name == component.name
    )
    assert sorted(d.class_name for d in _devices(top)) == ["nmos", "pmos"]
