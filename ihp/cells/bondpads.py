"""Bondpad components for IHP PDK."""

import math
from typing import Literal

import gdsfactory as gf
from gdsfactory import Component
from gdsfactory.typings import LayerSpec
from kfactory.schematic import DSchematic

from ..config import PATH
from .._common import _add_pins
_XS = "metal1_routing"


def regular_octagon_points(diameter: float):
    """Create a regular octagon"""
    side = diameter / (1 + math.sqrt(2))
    R = side / (2 * math.sin(math.pi / 8))
    start_angle = math.pi / 8
    return [
        (
            R * math.cos(start_angle + i * math.pi / 4),
            R * math.sin(start_angle + i * math.pi / 4),
        )
        for i in range(8)
    ]


def bondpad_schematic(
    shape: Literal["octagon", "square", "circle"] = "octagon",
    diameter: float = 80.0,
) -> DSchematic:
    _shape_map = {"octagon": 0, "square": 1, "circle": 2}
    s = DSchematic()
    s.info["symbol"] = "pad"
    s.info["ports"] = [{"name": "PAD", "side": "top", "type": "electric"}]
    s.info["models"] = [
        {
            "language": "spice",
            "implementation": "NgSpice",
            "name": "bondpad",
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/sg13g2_bondpad.lib",
            "sections": [],
            "port_order": ["PAD"],
            "params": {
                "size": "diameter * 1e-6",
                "shape": str(_shape_map[shape]),
                "padtype": "0",
            },
        },
        {
            "language": "spectre",
            "implementation": "VACASK",
            "name": "bondpad",
            "spice_type": "SUBCKT",
            "library": "ihp/models/vacask/models/sg13g2_bondpad.lib",
            "sections": [],
            "port_order": ["PAD"],
            "params": {
                "size": "diameter * 1e-6",
                "shape": str(_shape_map[shape]),
                "padtype": "0",
            },
        },
    ]
    s.create_port(name="PAD", cross_section=_XS, x=0, y=1, orientation=90)
    return s


@gf.cell(schematic_function=bondpad_schematic, tags=["IHP", "bondpad"])
def bondpad(
    shape: Literal["octagon", "square", "circle"] = "octagon",
    diameter: float = 80.0,
    layer_top_metal: LayerSpec = "TopMetal2drawing",
    layer_top_metal_pin: LayerSpec = "TopMetal2pin",
    layer_passiv: LayerSpec = "Passivpillar",
    layer_dfpad: LayerSpec = "dfpaddrawing",
    bbox_offsets: tuple[float, ...] | None = (-2.1, 0),
    flip_chip: bool = False,
) -> gf.Component:
    """Create a bondpad for wire bonding or flip-chip connection.

    Args:
        shape: Shape of the top-metal bondpad ("octagon", "square", or "circle").
        diameter: Interpreted as across-flats for octagons / squares, and diameter for circles.
        layer_top_metal: Top metal layer.
        layer_passiv: Passivation-opening layer.
        layer_dfpad: Deep-fill or density-fill support layer.
        bbox_offsets: Per-layer expansion distances in micrometers, applied to the passivation and dfpad layers.
        flip_chip: If True, suppress passivation opening for flip-chip bumps.

    Returns:
        Component containing the complete bondpad stack.
    """

    c = gf.Component()
    d = float(diameter)

    # Add top metal layer
    if shape == "square":
        c.add_ref(
            gf.components.rectangle(size=(d, d), layer=layer_top_metal, centered=True)
        )

    elif shape == "octagon":
        pts = regular_octagon_points(d)
        c.add_polygon(points=pts, layer=layer_top_metal)

    elif shape == "circle":
        c.add_ref(gf.components.circle(radius=d / 2, layer=layer_top_metal))

    else:
        raise ValueError(f"Unknown shape: {shape}")

    # Add additional layers
    if flip_chip:
        # Skip passivation opening for flip-chip
        bbox_layers = (layer_dfpad,)
        bbox_offsets = (bbox_offsets or ())[1:]
    else:
        bbox_layers = (layer_passiv, layer_dfpad)

    for layer, offset in zip(bbox_layers, bbox_offsets or ()):
        new_d = d + float(offset * 2)

        if shape == "square":
            c.add_ref(
                gf.components.rectangle(size=(new_d, new_d), layer=layer, centered=True)
            )
        elif shape == "circle":
            c.add_ref(gf.components.circle(radius=new_d / 2, layer=layer))
        elif shape == "octagon":
            c.add_polygon(points=regular_octagon_points(new_d), layer=layer)

    # Add port
    c.add_port(
        name="pad",
        center=(0, 0),
        width=d,
        orientation=0,
        layer=layer_top_metal_pin,
        port_type="electrical",
    )

    # Add metadata
    c.info["shape"] = shape
    c.info["diameter"] = diameter
    c.info["top_metal"] = layer_top_metal

    _add_pins(c)
    return c


@gf.cell(tags=["IHP", "bondpad", "array"])
def bondpad_array(
    n_pads: int = 4,
    pad_pitch: float = 100.0,
    pad_diameter: float = 80.0,
    shape: Literal["octagon", "square", "circle"] = "octagon",
    layer_top_metal: LayerSpec = "TopMetal2drawing",
    layer_top_metal_pin: LayerSpec = "TopMetal2pin",
    layer_passiv: LayerSpec = "Passivpillar",
    layer_dfpad: LayerSpec = "dfpaddrawing",
    bbox_offsets: tuple[float, ...] | None = (-2.1, 0),
) -> Component:
    """Create an array of bondpads.

    Args:
        n_pads: Number of bondpads.
        pad_pitch: Pitch between bondpad centers in micrometers.
        pad_diameter: Diameter of each bondpad in micrometers.
        shape: Shape of the bondpads.
        layer_top_metal: Top metal layer for the bondpad.
        layer_passiv: Passivation layer.
        layer_dfpad: Deep fill pad layer.
        bbox_offsets: Offsets for each additional layer.

    Returns:
        Component with bondpad array.
    """
    c = Component()

    for i in range(n_pads):
        pad = bondpad(
            shape=shape,
            diameter=pad_diameter,
            layer_top_metal=layer_top_metal,
            layer_top_metal_pin=layer_top_metal_pin,
            layer_passiv=layer_passiv,
            layer_dfpad=layer_dfpad,
            bbox_offsets=bbox_offsets,
        )
        pad_ref = c.add_ref(pad)
        pad_ref.movex(i * pad_pitch)

        # Add port for each pad
        c.add_port(
            name=f"pad_{i + 1}",
            center=(i * pad_pitch, 0),
            width=pad_diameter,
            orientation=0,
            layer=pad.ports["pad"].layer,
            port_type="electrical",
        )

    c.info["n_pads"] = n_pads
    c.info["pad_pitch"] = pad_pitch
    c.info["pad_diameter"] = pad_diameter

    # TODO: Bondpad array VLSIR Metadata

    _add_pins(c)
    return c


@gf.cell(tags=["IHP", "bondpad"])
def CuPillarPad() -> gf.Component:
    """Returns CuPillarPad copper pillar pad (imported from GDS)."""
    c = gf.import_gds(PATH.gds / "CuPillarPad.gds")
    width = 45
    c.add_port(
        name="e1", center=(0, 0), width=width, orientation=180, layer="TopMetal2drawing"
    )
    c.add_port(
        name="e2", center=(0, 0), width=width, orientation=0, layer="TopMetal2drawing"
    )
    c.add_port(
        name="e3", center=(0, 0), width=width, orientation=90, layer="TopMetal2drawing"
    )
    c.add_port(
        name="e4", center=(0, 0), width=width, orientation=270, layer="TopMetal2drawing"
    )
    return c
