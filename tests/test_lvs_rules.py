"""Smoke tests for the gflvs LVS rules (skipped when gflvs is not installed)."""

from __future__ import annotations

from typing import Any

import pytest

gflvs = pytest.importorskip("gflvs")

import gdstk  # noqa: E402
from gflvs.gflvs_refactor import ElectricalDeviceExtractionPolicy  # noqa: E402
from gflvs.gflvs_schema import LvsRunMode  # noqa: E402

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


def test_template_layers_in_pdk() -> None:
    pdk_layers = {(int(layer.layer), int(layer.datatype)) for layer in LAYER}
    used = rules.template_layers(rules.DEVICE_TEMPLATES) | set(rules.LAYER_CONNECTIVITY)
    assert used <= pdk_layers


def test_terminals_use_markers() -> None:
    for t in rules.DEVICE_TEMPLATES:
        if t.device_name in rules.NO_MARKER_TEMPLATES:
            continue
        for term in t.device_terminal_template:
            leaves = set(rules._leaf_layers(term.layer_composed_op))
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
        m.setattr(rules, "HIERARCHICAL_RUN", True)
        assert rules.build_lvs_config().run_mode == LvsRunMode.LVS_RUN_MODE_HIERARCHICAL


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
    ("cmim", {}, "cmim", 2, {"width": 6.0, "length": 6.0}),
    (
        "cmim",
        {"width": 8.0, "length": 5.0},
        "cmim",
        2,
        {"width": 8.0, "length": 5.0},
    ),
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
    gds = tmp_path / f"{pcell}.gds"
    component = getattr(cells, pcell)(**kwargs)
    component.write_gds(gds)
    # by name: kfactory also writes a $$$CONTEXT_INFO$$$ top cell
    top = next(c for c in gdstk.read_gds(str(gds)).cells if c.name == component.name)
    cfg = rules.DEFAULT_LVS_CONFIG
    results = ElectricalDeviceExtractionPolicy().execute(
        top, rules.DEVICE_TEMPLATES, cfg.electrical_device_extraction_config
    )
    devices = [r.unwrap() for r in results]
    assert [d.class_name for d in devices] == [device]
    assert len(devices[0].terminals) == n_terminals
    got = {p.name: p.value for p in devices[0].parameters}
    for name, value in params.items():
        assert got[name] == pytest.approx(value, rel=1e-3), name
