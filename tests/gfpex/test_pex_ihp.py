"""Consistency checks for the gfpex default PEX rules of IHP SG13G2."""

from __future__ import annotations

import pytest

pytest.importorskip("gfpex")

from gfpex.gfpex import StackLayerType, Techfile  # noqa: E402

from ihp.pex.rules import DEFAULT_PEX_RULES_CONFIG as CFG  # noqa: E402
from ihp.tech import LAYER  # noqa: E402

# IHP stacks reference KLayout-LVS computed layers (metal1_con, via1_drw, ...) besides the drawn layers.
NAMES = {li.name for li in CFG.layers} | {
    c.layer_info.name for c in CFG.lvs_computed_layers
}
METALS = [
    s
    for s in CFG.process_stack.layers
    if s.layer_type == StackLayerType.LAYER_TYPE_METAL
]
CONTACTS = [
    c
    for s in CFG.process_stack.layers
    for c in [
        getattr(s.metal_layer, "contact_above", None),
        getattr(s.diffusion_layer, "contact_above", None),
    ]
    if c is not None
]


def test_round_trip() -> None:
    assert isinstance(CFG, Techfile)
    assert Techfile.model_validate_json(CFG.to_json()) == CFG


def test_names_resolve() -> None:
    stack = [
        s.name
        for s in CFG.process_stack.layers
        if s.layer_type
        in (StackLayerType.LAYER_TYPE_METAL, StackLayerType.LAYER_TYPE_DIFFUSION)
    ]
    contacts = [n for c in CONTACTS for n in (c.name, c.layer_below, c.metal_above)]
    r = CFG.process_parasitics.resistance
    c = CFG.process_parasitics.capacitance
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
    assert set(stack + contacts + tables) <= NAMES


@pytest.mark.parametrize(
    ("field", "suffix"), [("drw_gds_pair", "drawing"), ("pin_gds_pair", "pin")]
)
def test_gds_pairs_match_layer(field: str, suffix: str) -> None:
    for li in CFG.layers:
        pair = getattr(li, field)
        ref = getattr(LAYER, f"{li.name}{suffix}", None)
        if pair is None or ref is None:
            continue
        assert (pair.layer, pair.datatype) == (ref.layer, ref.datatype), li.name


def test_metal_z_monotonic() -> None:
    # metal5_n_cap and metal5_cap are the two variants of Metal5 (without/with MIM) and share one z.
    zs = [s.metal_layer.z for s in METALS]
    assert zs == sorted(zs)


def test_z_lookup_covers_contacts() -> None:
    lookup = CFG.build_layer_z_lookup()
    assert all(c.name in lookup for c in CONTACTS)
