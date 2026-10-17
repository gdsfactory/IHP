"""Check the generated diagrams against physical PDK metadata."""

import importlib.util
from pathlib import Path

import gdsfactory as gf

from ihp import PDK

generator_path = Path(__file__).parents[1] / ".github" / "write_layer_stack.py"
module_spec = importlib.util.spec_from_file_location(
    "write_layer_stack", generator_path
)
generator = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(generator)


def test_physical_gds_layers_and_cross_section_widths():
    """Layer enums must resolve to mask layer/datatype pairs, including vias."""
    PDK.activate()
    layers = generator._extract_layers(PDK.layer_stack)
    by_name = {layer["name"]: layer for layer in layers}
    assert by_name["metal1"]["layer_pair"] == (8, 0)
    assert by_name["pwell"]["layer_pair"] == (46, 0)
    assert by_name["topvia1"]["type"] == "via"
    assert by_name["heatres"]["type"] == "conductor"
    cross_sections = generator._extract_cross_sections(PDK, layers)
    metal1 = next(
        section for section in cross_sections if section["name"] == "metal1_routing"
    )
    assert len(metal1["layers"]) == 1
    assert metal1["layers"][0]["gds"] == "8/0"
    assert metal1["layers"][0]["width"] == PDK.get_cross_section("metal1_routing").width


def test_layer_datatypes_are_distinct():
    """Layers sharing a mask number must keep their separate datatype identity."""
    PDK.activate()
    layer_stack = gf.technology.LayerStack(
        layers={
            "drawing": gf.technology.LayerLevel(layer=(8, 0), thickness=1, zmin=0),
            "pin": gf.technology.LayerLevel(layer=(8, 2), thickness=1, zmin=1),
        }
    )
    layers = generator._extract_layers(layer_stack)
    assert [layer["gds"] for layer in layers] == ["8/0", "8/2"]


def test_json_cannot_end_its_script_element():
    """PDK strings stay data even when they contain HTML/script syntax."""
    payload = {"name": '</script><img src=x onerror="alert(1)">'}
    embedded = generator._embed_data(payload)
    assert "<" not in embedded
    import json

    assert json.loads(embedded) == payload


def test_shared_assets_are_emitted_once_for_multiple_bands():
    PDK.activate()
    page = generator.render_page([("one", PDK), ("two", PDK)])
    assert page.count("<style>") == 1
    assert page.count("<script>") == 1
    assert page.count('class="layer-stack-viz"') == 2
