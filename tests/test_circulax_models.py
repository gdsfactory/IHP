"""Circulax preserves native VACASK model metadata without importing its runtime."""

import pytest

from ihp.cells.bjt_transistors import npn13G2_schematic
from ihp.cells.capacitors import cmim_schematic, rfcmim_schematic
from ihp.cells.fet_transistors import nmos_schematic, pmos_schematic
from ihp.cells.rf_transistors import rfnmos_schematic
from ihp.models.circulax import with_circulax_models


@pytest.mark.parametrize(
    "factory",
    [
        cmim_schematic,
        rfcmim_schematic,
        nmos_schematic,
        pmos_schematic,
        rfnmos_schematic,
        npn13G2_schematic,
    ],
)
def test_circulax_metadata_matches_vacask(factory):
    models = factory().info["models"]
    vacask = next(model for model in models if model["implementation"] == "VACASK")
    circulax = next(model for model in models if model["implementation"] == "Circulax")
    assert circulax == {**vacask, "implementation": "Circulax", "dialect": "vacask"}


def test_model_metadata_is_not_shared_mutable_state():
    original = [{"implementation": "VACASK", "params": {"w": "width * 1e-6"}}]
    result = with_circulax_models(original)
    result[-1]["params"]["w"] = "changed"
    assert original[0]["params"]["w"] == "width * 1e-6"
