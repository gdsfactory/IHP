"""Description: Test netlists for all cells in the PDK."""

from __future__ import annotations

import pathlib

import gdsfactory as gf
import jsondiff
import kfactory as kf
import numpy as np
import pytest
from gdsfactory.difftest import difftest
from pytest_regressions.data_regression import DataRegressionFixture
from pytest_regressions.ndarrays_regression import NDArraysRegressionFixture

from ihp import PDK
from ihp.models.to_vlsir import to_proto, to_spice, validate_vlsir_metadata


@pytest.fixture(autouse=True)
def activate_pdk() -> None:
    """Activate PDK."""
    PDK.activate()


cells = PDK.cells
skip_test = {
    "wire_corner",
    "die",
    "pack_doe",
    "pack_doe_grid",
    "import_gds",
    "nmos_hv",  # reference GDS not found
    "pmos_hv",  # reference GDS not found
    "rfpmos",  # reference GDS not found
    "rfnmos",  # reference GDS not found
    "subckt",  # requires mocking with model and ports
    "svaricap",
    "SVaricap",
    "guard_ring",  # Requires bbox or path argument
    "via_stack_with_pads",  # GDS geometry mismatch - pre-existing issue
}


cell_names = cells.keys() - skip_test
cell_names = [name for name in cell_names if not name.startswith("_")]
dirpath = pathlib.Path(__file__).absolute().with_suffix(".gds").parent / "gds_ref"
dirpath.mkdir(exist_ok=True, parents=True)


def get_minimal_netlist(comp: gf.Component):
    """Get minimal netlist from a component."""
    net = comp.get_netlist()

    def _get_instance(inst):
        return {
            "component": inst["component"],
            "settings": inst["settings"],
        }

    return {"instances": {i: _get_instance(c) for i, c in net["instances"].items()}}


def instances_without_info(net):
    """Get instances without info."""
    return {
        k: {
            "component": v.get("component", ""),
            "settings": v.get("settings", {}),
        }
        for k, v in net.get("instances", {}).items()
    }


@pytest.mark.parametrize("name", cell_names)
def test_cell_in_pdk(name):
    """Test that cell is in the PDK."""
    c1 = gf.Component()
    c1.add_ref(gf.get_component(name))
    net1 = get_minimal_netlist(c1)

    c2 = gf.read.from_yaml(net1)
    net2 = get_minimal_netlist(c2)

    instances1 = instances_without_info(net1)
    instances2 = instances_without_info(net2)
    assert instances1 == instances2


@pytest.mark.parametrize("component_name", cell_names)
def test_gds(component_name: str) -> None:
    """Avoid regressions in GDS geometry shapes and layers."""
    component = cells[component_name]()
    difftest(component, test_name=component_name, dirpath=dirpath)


@pytest.mark.parametrize("component_name", cell_names)
def test_settings(component_name: str, data_regression: DataRegressionFixture) -> None:
    """Avoid regressions when exporting settings."""
    component = cells[component_name]()
    data_regression.check(component.to_dict())


skip_test_models = {}


models = PDK.models
model_names = sorted(
    [
        name
        for name in set(models.keys()) - set(skip_test_models)
        if not name.startswith("_")
    ]
)


@pytest.mark.parametrize("model_name", model_names)
def test_models_with_wavelength_sweep(
    model_name: str, ndarrays_regression: NDArraysRegressionFixture
) -> None:
    """Test models with different wavelengths to avoid regressions in frequency response."""
    # Test at different wavelengths
    wl = [1.53, 1.55, 1.57]
    try:
        model = models[model_name]
        s_params = model(wl=wl)
    except TypeError:
        pytest.skip(f"{model_name} does not accept a wl argument")

    # Convert s_params dictionary to arrays for regression testing
    # s_params is a dict with tuple keys (port pairs) and JAX array values
    arrays_to_check = {}
    for key, value in sorted(s_params.items()):
        # Convert tuple key to string for regression test compatibility
        key_str = f"s_{key[0]}_{key[1]}"
        # Convert JAX arrays to numpy and separate real/imag parts

        value_np = np.array(value)
        arrays_to_check[f"{key_str}_real"] = np.real(value_np)
        arrays_to_check[f"{key_str}_imag"] = np.imag(value_np)

    ndarrays_regression.check(
        arrays_to_check,
        default_tolerance={"atol": 1e-2, "rtol": 1e-2},
    )


@pytest.mark.parametrize("component_name", cell_names)
def test_vlsir_to_proto(component_name: str) -> None:
    """Test to_proto for cells with vlsir metadata."""
    component = cells[component_name]()

    if "vlsir" not in component.info:
        pytest.skip(f"{component_name} does not have vlsir metadata")

    pkg = to_proto(component, domain="ihp.sg13g2")

    # Verify we got a valid package with one external module
    assert len(pkg.ext_modules) == 1
    ext_mod = pkg.ext_modules[0]

    # Verify the external module has the expected model name
    vlsir_info = component.info["vlsir"]
    assert ext_mod.name.name == vlsir_info["model"]

    # Verify ports match port_order
    port_names = [p.signal for p in ext_mod.ports]
    assert port_names == vlsir_info["port_order"]


@pytest.mark.parametrize("component_name", cell_names)
def test_vlsir_to_spice(component_name: str) -> None:
    """Test to_spice for cells with vlsir metadata."""
    component = cells[component_name]()

    if "vlsir" not in component.info:
        pytest.skip(f"{component_name} does not have vlsir metadata")

    netlist = to_spice(component, domain="ihp.sg13g2", fmt="spice")

    # Verify we got a non-empty netlist string
    assert isinstance(netlist, str)
    assert len(netlist) > 0


class TestVlsirValidationErrors:
    """Test error handling for invalid vlsir metadata."""

    def test_missing_vlsir_metadata(self) -> None:
        """Test that missing vlsir metadata raises ValueError."""
        c = gf.Component()
        c.add_port(name="p", center=(0, 0), width=0.1, orientation=180, layer=(1, 0))

        with pytest.raises(ValueError, match="missing required 'vlsir' metadata"):
            validate_vlsir_metadata(c)

    def test_missing_model_field(self) -> None:
        """Test that missing 'model' field raises ValueError."""
        c = gf.Component()
        c.add_port(name="p", center=(0, 0), width=0.1, orientation=180, layer=(1, 0))
        c.info["vlsir"] = {
            "spice_type": "RESISTOR",
            "port_order": ["p"],
        }

        with pytest.raises(ValueError, match="missing required fields.*model"):
            validate_vlsir_metadata(c)

    def test_missing_spice_type_field(self) -> None:
        """Test that missing 'spice_type' field raises ValueError."""
        c = gf.Component()
        c.add_port(name="p", center=(0, 0), width=0.1, orientation=180, layer=(1, 0))
        c.info["vlsir"] = {
            "model": "rpoly",
            "port_order": ["p"],
        }

        with pytest.raises(ValueError, match="missing required fields.*spice_type"):
            validate_vlsir_metadata(c)

    def test_missing_port_order_field(self) -> None:
        """Test that missing 'port_order' field raises ValueError."""
        c = gf.Component()
        c.add_port(name="p", center=(0, 0), width=0.1, orientation=180, layer=(1, 0))
        c.info["vlsir"] = {
            "model": "rpoly",
            "spice_type": "RESISTOR",
        }

        with pytest.raises(ValueError, match="missing required fields.*port_order"):
            validate_vlsir_metadata(c)

    def test_unsupported_spice_type(self) -> None:
        """Test that unsupported spice_type raises ValueError."""
        c = gf.Component()
        c.add_port(name="p", center=(0, 0), width=0.1, orientation=180, layer=(1, 0))
        c.info["vlsir"] = {
            "model": "rpoly",
            "spice_type": "INVALID_TYPE",
            "port_order": ["p"],
        }

        with pytest.raises(ValueError, match="unknown spice_type 'INVALID_TYPE'"):
            validate_vlsir_metadata(c)

    def test_port_order_not_on_component(self) -> None:
        """Test that port_order with non-existent ports raises ValueError."""
        c = gf.Component()
        c.add_port(name="p", center=(0, 0), width=0.1, orientation=180, layer=(1, 0))
        c.info["vlsir"] = {
            "model": "rpoly",
            "spice_type": "RESISTOR",
            "port_order": ["p", "n"],  # 'n' does not exist
        }

        with pytest.raises(ValueError, match="port_order contains ports not found"):
            validate_vlsir_metadata(c)

    def test_empty_port_order(self) -> None:
        """Test that empty port_order raises ValueError."""
        c = gf.Component()
        c.add_port(name="p", center=(0, 0), width=0.1, orientation=180, layer=(1, 0))
        c.info["vlsir"] = {
            "model": "rpoly",
            "spice_type": "RESISTOR",
            "port_order": [],
        }

        with pytest.raises(ValueError, match="port_order must be a non-empty list"):
            validate_vlsir_metadata(c)

    def test_port_map_valid(self) -> None:
        """Test that valid port_map passes validation."""
        c = gf.Component()
        c.add_port(name="D", center=(0, 0), width=0.1, orientation=180, layer=(1, 0))
        c.add_port(name="G", center=(1, 0), width=0.1, orientation=0, layer=(1, 0))
        c.add_port(name="S", center=(2, 0), width=0.1, orientation=0, layer=(1, 0))
        c.info["vlsir"] = {
            "model": "nmos",
            "spice_type": "MOS",
            "port_order": ["d", "g", "s", "b"],  # VLSIR/SPICE port names
            "port_map": {"D": "d", "G": "g", "S": "s"},  # Component -> VLSIR mapping
        }

        # Should not raise
        result = validate_vlsir_metadata(c)
        assert result["port_map"] == {"D": "d", "G": "g", "S": "s"}

    def test_port_map_invalid_component_port(self) -> None:
        """Test that port_map with non-existent component port raises ValueError."""
        c = gf.Component()
        c.add_port(name="D", center=(0, 0), width=0.1, orientation=180, layer=(1, 0))
        c.info["vlsir"] = {
            "model": "nmos",
            "spice_type": "MOS",
            "port_order": ["d", "g"],
            "port_map": {"D": "d", "X": "g"},  # 'X' doesn't exist on component
        }

        with pytest.raises(
            ValueError, match="port_map contains component ports not found.*X"
        ):
            validate_vlsir_metadata(c)

    def test_port_map_not_dict(self) -> None:
        """Test that non-dict port_map raises ValueError."""
        c = gf.Component()
        c.add_port(name="p", center=(0, 0), width=0.1, orientation=180, layer=(1, 0))
        c.info["vlsir"] = {
            "model": "rpoly",
            "spice_type": "RESISTOR",
            "port_order": ["p"],
            "port_map": ["p"],  # Should be a dict
        }

        with pytest.raises(ValueError, match="port_map must be a dict"):
            validate_vlsir_metadata(c)


@pytest.mark.parametrize("component_name", cell_names)
def test_optical_port_positions(component_name: str) -> None:
    """Ensure that optical ports are positioned correctly."""
    component = cells[component_name]()
    if isinstance(component, gf.ComponentAllAngle):
        new_component = gf.Component()
        kf.VInstance(component).insert_into_flat(new_component, levels=0)
        new_component.add_ports(component.ports)
        component = new_component
    for port in component.ports:
        if port.port_type == "optical":
            port_layer = port.layer
            port_width = port.width
            port_position = port.center
            port_angle = port.orientation
            cs_region = kf.kdb.Region(component.begin_shapes_rec(port_layer))
            optical_edges = cs_region.edges()

            tolerance = 0.001
            poly = kf.kdb.DBox(-tolerance, -tolerance, tolerance, tolerance)
            dbu_in_um = port.kcl.to_um(1)
            port_marker = (
                kf.kdb.DPolygon(poly).transformed(port.dcplx_trans).to_itype(dbu_in_um)
            )
            port_marker_region = kf.kdb.Region(port_marker)

            interacting_edges = optical_edges.interacting(port_marker_region)
            if interacting_edges.is_empty():
                raise AssertionError(
                    f"No optical edge found for port {port.name} at position {port_position} with width {port_width} and angle {port_angle}."
                )
            port_edge = next(iter(interacting_edges.each()))
            edge_length = port_edge.length() * 0.001
            if not np.isclose(edge_length, port_width, atol=1e-3):
                raise AssertionError(
                    f"Port {port.name} has width {port_width}, but the optical edge length is {edge_length}."
                )


if __name__ == "__main__":
    component_type = "coupler_symmetric"
    c = cells[component_type]()
    n = c.get_netlist()
    n.pop("connections", None)
    print(n)
    c2 = gf.read.from_yaml(n)
    n2 = c2.get_netlist()
    d = jsondiff.diff(n, n2)
    assert len(d) == 0, d
