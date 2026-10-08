"""Opt-in acceptance through GF+ metadata and real OSDI binaries.

Set IHP_CIRCULAX_OSDI_MODULES to compatible PSP, resistor, capacitor and
inductor binaries. This does not verify automatic binary provisioning.
"""

import os

import numpy as np
import pytest

import ihp

circulax = pytest.importorskip("circulax")
electronic = pytest.importorskip("circulax.components.electronic")
photonic = pytest.importorskip("circulax.components.photonic")
metadata = pytest.importorskip("gdsfactoryplus.factory_metadata")
pytest.importorskip("bosdi")
pytestmark = pytest.mark.skipif(
    not os.environ.get("IHP_CIRCULAX_OSDI_MODULES"),
    reason="requires explicit ABI-compatible native binaries",
)


@pytest.mark.parametrize("mixed_optical", [False, True])
def test_metadata_mos_instances_share_native_batch_with_distinct_units(mixed_optical):
    """Instance dimensions reach one native batch in SI units. @tags circulax-simulation"""
    ihp.PDK.activate()
    model = metadata.resolve_factory_model("nmos", "circulax")
    assert model is not None
    netlist = {
        "instances": {
            "M1": {"component": "nmos", "settings": {"width": 2.0, "length": 0.13}},
            "M2": {"component": "nmos", "settings": {"width": 4.0, "length": 0.13}},
            "Vd": {"component": "source", "settings": {"V": 1.0}},
            "Vg": {"component": "source", "settings": {"V": 0.7}},
            "GND": {"component": "ground"},
        },
        "connections": {
            "M1,D": ["M2,D", "Vd,p1"],
            "M1,G": ["M2,G", "Vg,p1"],
            "GND,p1": ["M1,S", "M2,S", "M1,B", "M2,B", "Vd,p2", "Vg,p2"],
        },
        "ports": {"out": "M1,D"},
    }
    models = {"nmos": model, "source": electronic.VoltageSource}
    if mixed_optical:
        netlist["instances"].update(
            {
                "laser": {"component": "laser"},
                "wg": {"component": "waveguide"},
                "load": {"component": "load", "settings": {"R": 1.0}},
            }
        )
        netlist["connections"]["laser,p1"] = "wg,p1"
        netlist["connections"]["wg,p2"] = "load,p1"
        netlist["connections"]["GND,p1"].extend(["laser,p2", "load,p2"])
        netlist["ports"]["optical_out"] = "wg,p2"
        models.update(
            {
                "laser": photonic.OpticalSource,
                "waveguide": photonic.OpticalWaveguide,
                "load": electronic.Resistor,
            }
        )
    circuit = circulax.compile_circuit(
        netlist,
        models,
        is_complex=mixed_optical,
        backend="dense",
    )
    groups = [group for group in circuit.groups.values() if hasattr(group, "model_id")]
    assert len(groups) == 1
    group = groups[0]
    descriptor = circuit.source_models[group.name]
    columns = {name.lower(): index for index, name in enumerate(descriptor.param_names)}
    assert group.params.shape[0] == 2
    rows = [group.index_map["M1~device0"], group.index_map["M2~device0"]]
    np.testing.assert_allclose(
        np.asarray(group.params)[rows, columns["w"]], [2e-6, 4e-6]
    )
    np.testing.assert_allclose(
        np.asarray(group.params)[rows, columns["l"]], [0.13e-6] * 2
    )
    assert np.isfinite(np.asarray(circuit.dc())).all()


def test_metadata_composites_preserve_all_native_leaves_and_solve():
    """Two RF capacitors retain their 24 internal native devices. @tags circulax-simulation"""
    ihp.PDK.activate()
    model = metadata.resolve_factory_model("rfcmim", "circulax")
    assert model is not None
    netlist = {
        "instances": {
            "C1": {"component": "rfcmim", "settings": {"width": 10.0, "length": 10.0}},
            "C2": {"component": "rfcmim", "settings": {"width": 20.0, "length": 10.0}},
            "V": {"component": "source", "settings": {"V": 1.0}},
            "GND": {"component": "ground"},
        },
        "connections": {
            "V,p1": ["C1,PLUS", "C2,PLUS"],
            "GND,p1": ["C1,MINUS", "C2,MINUS", "C1,BN", "C2,BN", "V,p2"],
        },
        "ports": {"out": "C1,PLUS"},
    }
    circuit = circulax.compile_circuit(
        netlist,
        {"rfcmim": model, "source": electronic.VoltageSource},
        is_complex=False,
        backend="dense",
    )
    groups = [group for group in circuit.groups.values() if hasattr(group, "model_id")]
    assert sum(group.params.shape[0] for group in groups) == 24
    assert len(circuit.source_netlist.instances) == 26
    assert np.isfinite(np.asarray(circuit.dc())).all()
