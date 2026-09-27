"""RF material provenance, nominal sheet resistance, and layer bindings."""

import pytest
from pdk_schema import MaterialCard, Permittivity, ScalarValue

import ihp
from ihp.material_cards import EM_REVISION, IHP_REVISION, MATERIAL_CARDS


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
        assert layers[name].material == f"sg13g2_{name}"
        assert MATERIAL_CARDS[layers[name].material].rf is not None
    assert layers["mim"].info["layer_type"] == "conductor"


def test_pdk_cards_round_trip_with_pinned_provenance():
    assert ihp.PDK.material_cards is MATERIAL_CARDS
    for card in MATERIAL_CARDS.values():
        assert MaterialCard.model_validate_json(card.model_dump_json()) == card
        assert card.optical is None
        assert card.rf is not None
        provenance = card.rf.provenance
        assert EM_REVISION in provenance.data_url
        assert IHP_REVISION in provenance.url


def test_substrate_resistivity_units():
    regime = MATERIAL_CARDS["silicon"].rf
    assert regime is not None
    assert isinstance(regime.permittivity, Permittivity)
    sigma = regime.permittivity.conductivity
    assert isinstance(sigma, ScalarValue)
    assert sigma.unit == "S/m"
    # Process spec RSBLK = 50 ohm cm = 0.5 ohm m.
    assert 1 / sigma.value == pytest.approx(0.5)
