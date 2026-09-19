"""Integration test for IHP SG13G2 gflvs LVS config."""

from __future__ import annotations

import pytest

gflvs = pytest.importorskip("gflvs")

from ihp.lvs import DEFAULT_LVS_CONFIG  # noqa: E402


def test_lvs_config_importable() -> None:
    assert DEFAULT_LVS_CONFIG is not None


def test_gds_table_nonempty() -> None:
    from ihp.lvs.lvs import GDS_TABLE

    assert len(GDS_TABLE) > 0


def test_device_templates_contain_npn() -> None:
    from ihp.lvs.lvs import DEVICE_TEMPLATES

    names = [t.device_name for t in DEVICE_TEMPLATES]
    assert "npn13G2" in names


def test_lna_lvs_smoke() -> None:
    """Smoke: build NPN-based amplifier schematic + empty layout, run LVS."""
    import gdsfactory as gf
    from gflvs.gflvs_schema.circuit import TerminalReference
    from gflvs.schematic import (
        build_circuit,
        build_connection,
        build_external_module,
        build_module,
        build_module_reference,
        build_terminal,
    )

    from ihp.lvs import run_lvs_ihp

    npn = build_external_module("npn13G2", terminals=[
        build_terminal("C"), build_terminal("B"), build_terminal("E"),
    ])
    res = build_external_module("rhigh", terminals=[build_terminal("P1"), build_terminal("P2")])
    top = build_module(
        name="lna_stage",
        module_references=[build_module_reference("q1", "npn13G2"), build_module_reference("r1", "rhigh")],
        connections=[
            build_connection(
                "bias_net",
                source=TerminalReference(instance_name="q1", terminal_name="B"),
                target=TerminalReference(instance_name="r1", terminal_name="P2"),
            ),
        ],
    )
    circuit = build_circuit("lna_stage", top_module="lna_stage", modules=[top], ext_modules=[npn, res])
    layout = gf.Component("lna_stage")
    result = run_lvs_ihp(layout, circuit)
    assert result is not None
