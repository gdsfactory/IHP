"""RF material provenance, nominal sheet resistance, and layer bindings."""

import pytest
from pdk_schema import MaterialCard, Permittivity, ScalarValue

import ihp
from ihp.material_cards import (
    BEOL_COMPOSITION_URL,
    EM_REVISION,
    IHP_REVISION,
    MATERIAL_CARDS,
)


@pytest.mark.parametrize(
    ("layer", "sheet_resistance"),
    [
        ("metal1", 0.110),
        ("metal2", 0.088),
        ("metal3", 0.088),
        ("metal4", 0.088),
        ("metal5", 0.088),
        ("topmetal1", 0.018),
        ("topmetal2", 0.011),
    ],
)
def test_metal_sheet_resistance_matches_process_spec(layer, sheet_resistance):
    level = ihp.PDK.layer_stack.layers[layer]
    regime = MATERIAL_CARDS[level.material].rf
    assert regime is not None
    assert isinstance(regime.conductivity, ScalarValue)
    resistance = 1 / (regime.conductivity.value * level.thickness * 1e-6)
    # Published EM values are rounded; compare with spec §§2.13 and 2.16.
    assert resistance == pytest.approx(sheet_resistance, rel=0.002)


def test_beol_and_contact_layers_use_distinct_rf_cards():
    layers = ihp.PDK.layer_stack.layers
    expected = {
        "cont",
        "metal1",
        "metal2",
        "metal3",
        "metal4",
        "metal5",
        "via1",
        "via2",
        "via3",
        "via4",
        "topvia1",
        "topvia2",
        "topmetal1",
        "topmetal2",
        "vmim",
        "mim",
    }
    for name in expected:
        card = MATERIAL_CARDS[layers[name].material]
        assert card.info["source_material"].lower() == name
        assert card.rf is not None
    assert len({layers[name].material for name in expected}) == len(expected)
    assert layers["mim"].info["layer_type"] == "conductor"


def test_pdk_cards_round_trip_with_pinned_provenance():
    assert ihp.PDK.material_cards is MATERIAL_CARDS
    for name, card in MATERIAL_CARDS.items():
        assert card.name == name
        assert MaterialCard.model_validate_json(card.model_dump_json()) == card
        assert card.optical is None
        assert card.rf is not None
        provenance = card.rf.provenance
        assert EM_REVISION in provenance.data_url
        assert IHP_REVISION in provenance.url


def test_physical_identity_is_separate_from_effective_rf_properties():
    layers = ihp.PDK.layer_stack.layers
    metal = MATERIAL_CARDS[layers["metal1"].material]
    via = MATERIAL_CARDS[layers["via1"].material]
    assert metal.name.startswith("alcu_")
    assert metal.info["composition"] == "Ti/TiN/AlCu/Ti/TiN"
    assert via.name.startswith("tungsten_")
    assert via.info["composition"] == "W with Ti/TiN liners"
    for card in (metal, via):
        assert card.info["composition"] in card.info["display_name"]
        assert card.info["composition_source_url"] == BEOL_COMPOSITION_URL
        assert card.rf.provenance.data_url != BEOL_COMPOSITION_URL


@pytest.mark.parametrize("layer", ["cont", "vmim", "mim"])
def test_unverified_composition_is_not_assigned_a_bulk_material(layer):
    card = MATERIAL_CARDS[ihp.PDK.layer_stack.layers[layer].material]
    assert card.info["composition"] is None
    assert card.info["composition_source_url"] is None
    assert "composition unverified" in card.info["display_name"]
    assert card.rf.conductivity.value > 0


def test_substrate_resistivity_units():
    regime = MATERIAL_CARDS["silicon"].rf
    assert regime is not None
    assert isinstance(regime.permittivity, Permittivity)
    sigma = regime.permittivity.conductivity
    assert isinstance(sigma, ScalarValue)
    assert sigma.unit == "S/m"
    # Process spec RSBLK = 50 ohm cm = 0.5 ohm m.
    assert 1 / sigma.value == pytest.approx(0.5)
