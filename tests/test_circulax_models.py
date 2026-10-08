"""Circulax preserves native VACASK model metadata without importing its runtime."""

import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from ihp._schematic import with_circulax_models
from ihp.cells import (
    antennas,
    bjt_transistors,
    bondpads,
    capacitors,
    fet_transistors,
    passives,
    resistors,
    rf_transistors,
)


@pytest.mark.parametrize(
    "factory",
    [
        factory
        for module in (
            antennas,
            bjt_transistors,
            bondpads,
            capacitors,
            fet_transistors,
            passives,
            resistors,
            rf_transistors,
        )
        for name, factory in vars(module).items()
        if name.endswith("_schematic")
    ],
)
def test_circulax_metadata_matches_vacask(factory):
    """Verify schematic registration. @tags circulax-simulation"""
    models = factory().info["models"]
    vacask = next(model for model in models if model["implementation"] == "VACASK")
    circulax = next(model for model in models if model["implementation"] == "Circulax")
    assert circulax["language"] == "circulax"
    assert circulax["module"] == "ihp.models.circulax"
    assert circulax["qualname"] == factory.__name__.removesuffix("_schematic")
    assert circulax["port_order"] == vacask["port_order"]
    assert circulax["params"] == {}
    assert "library" not in circulax
    json.dumps(circulax)
    native = next(model for model in models if model["implementation"] == "NgSpice")
    terminals = []
    for library in (Path(__file__).parents[1] / "ihp/models/ngspice/models").glob(
        "*.lib"
    ):
        for line in library.read_text(encoding="latin-1").splitlines():
            words = line.split()
            if (
                len(words) > 1
                and words[0].lower() == ".subckt"
                and words[1] == native["name"]
            ):
                terminals.append(words[2:])
    assert terminals
    assert all(list(circulax["port_map"].values()) == nodes for nodes in terminals)


def test_model_metadata_is_not_shared_mutable_state():
    """Verify schematic registration. @tags circulax-simulation"""
    original = [
        {
            "implementation": "VACASK",
            "name": "test",
            "port_order": ["D"],
            "params": {"w": "width * 1e-6"},
        }
    ]
    result = with_circulax_models(original, qualname="test")
    result[-1]["port_order"].append("G")
    assert original[0]["params"]["w"] == "width * 1e-6"
    assert original[0]["port_order"] == ["D"]


def test_metadata_import_does_not_require_simulation_dependencies():
    """Verify schematic registration. @tags circulax-simulation"""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import ihp; from ihp.cells.fet_transistors import nmos_schematic; nmos_schematic(); assert not any(k == 'circulax' or k.startswith('circulax.') or k == 'bosdi' or k.startswith('bosdi.') for k in sys.modules)",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "factory",
    [
        fet_transistors.nmos_schematic,
        capacitors.rfcmim_schematic,
        bjt_transistors.npn13G2_schematic,
        resistors.rsil_schematic,
    ],
)
def test_registered_library_models_have_instance_binding(factory):
    """Objects retain units, defaults and native terminal aliases. @tags circulax-simulation"""
    pytest.importorskip("circulax.netlist_io")
    module = importlib.import_module("ihp.models.circulax")
    registration = next(
        entry
        for entry in factory().info["models"]
        if entry.get("language") == "circulax"
    )
    model = getattr(module, registration["qualname"])
    assert model._is_circulax_library_model
    assert not callable(model)
    assert model.port_map == registration["port_map"]
    assert model.defaults
    assert model.parameter_units
    assert getattr(module, registration["qualname"]) is model


def test_model_registration_keeps_rf_and_plain_transistor_bindings_distinct():
    """Cell mappings differ while both registrations reuse the same native cards. @tags circulax-simulation"""
    pytest.importorskip("circulax.netlist_io")
    module = importlib.import_module("ihp.models.circulax")
    assert module.nmos is not module.rfnmos
    assert module.nmos.subcircuit == module.rfnmos.subcircuit
    assert module.nmos._source[0] == module.rfnmos._source[0]
    assert module.nmos.expressions != module.rfnmos.expressions


def test_bondpad_keeps_shape_as_an_instance_parameter():
    """The shared model translates each symbol shape independently. @tags circulax-simulation"""
    pytest.importorskip("circulax.netlist_io")
    model = importlib.import_module("ihp.models.circulax").bondpad
    assert model.defaults["shape"] == "octagon"
    assert model.parameter_values["shape"] == {"octagon": 0, "square": 1, "circle": 2}
    assert model.expressions["shape"] == "shape"


def test_registered_mos_library_parses_with_current_dispatcher():
    """Registered native libraries work with NetlistParse's supported dialects. @tags circulax-simulation"""
    runtime = pytest.importorskip("circulax.netlist_io")
    model = importlib.import_module("ihp.models.circulax").nmos
    path, section, _, dialect, temperature, include_paths = model._source
    library = runtime.Library.from_file(
        path,
        section=section,
        dialect=dialect,
        temperature_c=temperature,
        include_paths=include_paths,
    )
    resolved = library.instantiate(
        model.subcircuit, settings={"w": 1e-6, "l": 0.13e-6, "ng": 1, "m": 1}
    )
    assert resolved.instances


def test_native_bondpad_placeholder_rejects_disconnected_terminal():
    """An empty library placeholder cannot silently become a physical model. @tags circulax-simulation"""
    pytest.importorskip("circulax.netlist_io")
    model = importlib.import_module("ihp.models.circulax").bondpad
    with pytest.raises(ValueError, match=r"unconnected public terminal.*PAD"):
        model.instantiate()


@pytest.mark.parametrize("name", ["cmim", "rfcmim", "esd_nmos"])
def test_registered_port_aliases_match_native_subcircuit(name):
    """Case-sensitive native nodes retain the intended public symbol aliases. @tags circulax-simulation"""
    runtime = pytest.importorskip("circulax.netlist_io")
    model = getattr(importlib.import_module("ihp.models.circulax"), name)
    path, section, _, dialect, temperature, include_paths = model._source
    library = runtime.Library.from_file(
        path,
        section=section,
        dialect=dialect,
        temperature_c=temperature,
        include_paths=include_paths,
    )
    resolved = library.instantiate(model.subcircuit)
    assert set(model.port_map.values()) == set(resolved.ports)
    if name == "rfcmim":
        assert {"PLUS", "MINUS", "bn"} == set(resolved.ports)
        assert len(resolved.instances) > 1


def test_native_svaricap_rejects_unsupported_voltage_behavior():
    """Behavioral voltage dependence cannot silently become a static model. @tags circulax-simulation"""
    runtime = pytest.importorskip("circulax.netlist_io")
    model = importlib.import_module("ihp.models.circulax").svaricap
    with pytest.raises(runtime.NetlistError, match="unsupported function 'v'"):
        model.instantiate()
