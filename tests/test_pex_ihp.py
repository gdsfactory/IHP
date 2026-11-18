"""Consistency checks for the gfpex default PEX rules of IHP SG13G2."""

from __future__ import annotations

from types import ModuleType
from typing import Any

import pytest

from ihp.tech import LAYER


@pytest.fixture(scope="module")
def gfpex() -> ModuleType:
    # The engine module, not the bare package: any directory named gfpex on sys.path would satisfy `import gfpex`.
    return pytest.importorskip("gfpex.gfpex")


@pytest.fixture(scope="module")
def cfg(gfpex: ModuleType) -> Any:
    from ihp.pex.rules import DEFAULT_PEX_RULES_CONFIG

    return DEFAULT_PEX_RULES_CONFIG


@pytest.fixture(scope="module")
def metals(gfpex: ModuleType, cfg: Any) -> list[Any]:
    return [
        s
        for s in cfg.process_stack.layers
        if s.layer_type == gfpex.StackLayerType.LAYER_TYPE_METAL
    ]


@pytest.fixture(scope="module")
def contacts(cfg: Any) -> list[Any]:
    return [
        c
        for s in cfg.process_stack.layers
        for c in [
            getattr(s.metal_layer, "contact_above", None),
            getattr(s.diffusion_layer, "contact_above", None),
        ]
        if c is not None
    ]


def test_round_trip(gfpex: ModuleType, cfg: Any) -> None:
    assert isinstance(cfg, gfpex.Techfile)
    assert gfpex.Techfile.model_validate_json(cfg.to_json()) == cfg


def test_names_resolve(gfpex: ModuleType, cfg: Any, contacts: list[Any]) -> None:
    # IHP stacks reference KLayout-LVS computed layers (metal1_con, via1_drw, ...) besides the drawn layers.
    names = {li.name for li in cfg.layers} | {
        c.layer_info.name for c in cfg.lvs_computed_layers
    }
    types = (
        gfpex.StackLayerType.LAYER_TYPE_METAL,
        gfpex.StackLayerType.LAYER_TYPE_DIFFUSION,
    )
    stack = [s.name for s in cfg.process_stack.layers if s.layer_type in types]
    contact_names = [
        n for c in contacts for n in (c.name, c.layer_below, c.metal_above)
    ]
    r = cfg.process_parasitics.resistance
    c = cfg.process_parasitics.capacitance
    tables = (
        [x.layer_name for x in r.layers]
        + [
            n
            for x in r.contacts
            for n in (x.contact_name, x.device_layer_name, x.layer_above)
        ]
        + [x.via_name for x in r.vias]
        + [x.layer_name for x in c.substrates]
        + [n for x in c.overlaps for n in (x.top_layer_name, x.bottom_layer_name)]
        + [x.layer_name for x in c.sidewalls]
        + [n for x in c.sideoverlaps for n in (x.in_layer_name, x.out_layer_name)]
    )
    assert set(stack + contact_names + tables) <= names


@pytest.mark.parametrize(
    ("field", "suffix"), [("drw_gds_pair", "drawing"), ("pin_gds_pair", "pin")]
)
def test_gds_pairs_match_layer(cfg: Any, field: str, suffix: str) -> None:
    for li in cfg.layers:
        pair = getattr(li, field)
        ref = getattr(LAYER, f"{li.name}{suffix}", None)
        if pair is None or ref is None:
            continue
        assert (pair.layer, pair.datatype) == (ref.layer, ref.datatype), li.name


def test_metal_z_monotonic(metals: list[Any]) -> None:
    # metal5_n_cap and metal5_cap are the two variants of Metal5 (without/with MIM) and share one z.
    zs = [s.metal_layer.z for s in metals]
    assert zs == sorted(zs)


def test_z_lookup_covers_contacts(cfg: Any, contacts: list[Any]) -> None:
    lookup = cfg.build_layer_z_lookup()
    assert all(c.name in lookup for c in contacts)
