"""Resistor components for IHP PDK."""

import gdsfactory as gf
from gdsfactory import Component
from gdsfactory.typings import LayerSpec
from kfactory.schematic import DSchematic

from ihp.tech import TECH as _TECH

_XS = "metal1_routing"


def add_rect(
    component,
    size: tuple[float, float],
    layer: LayerSpec,
    origin: tuple[float, float],
    centered: bool = False,
):
    """Create rectangle, add ref to component and move to origin, return ref."""
    rect = gf.components.rectangle(size=size, layer=layer, centered=centered)
    ref = component.add_ref(rect)
    ref.move(origin)
    return ref


def rsil_schematic(
    dy: float = 0.5,
    dx: float = 0.5,
    resistance: float | None = None,
) -> DSchematic:
    s = DSchematic()
    s.info["symbol"] = "resistor"
    s.info["ports"] = [
        {"name": "P1", "side": "top", "type": "electric"},
        {"name": "P2", "side": "bottom", "type": "electric"},
        {"name": "BN", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "implementation": "NgSpice",
            "name": "rsil",
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerRES.lib",
            "sections": ["res_typ", "res_bcs", "res_wcs"],
            "port_order": ["P1", "P2", "BN"],
            "params": {"w": "dx * 1e-6", "l": "dy * 1e-6", "m": "1"},
        },
        {
            "language": "spectre",
            "implementation": "VACASK",
            "name": "rsil",
            "spice_type": "SUBCKT",
            "library": "ihp/models/vacask/models/cornerRES.lib",
            "sections": ["res_typ", "res_bcs", "res_wcs"],
            "port_order": ["P1", "P2", "BN"],
            "params": {"w": "dx * 1e-6", "l": "dy * 1e-6", "m": "1"},
        },
    ]
    s.create_port(name="P1", cross_section=_XS, x=0, y=1, orientation=90)
    s.create_port(name="P2", cross_section=_XS, x=0, y=-1, orientation=270)
    s.create_port(name="BN", cross_section=_XS, x=1, y=0, orientation=0)
    return s


@gf.cell(schematic_function=rsil_schematic, tags=["IHP", "resistor", "silicided"])
def rsil(
    dy: float = 0.5,
    dx: float = 0.5,
    resistance: float | None = None,
    model: str = "rsil",
    layer_poly: LayerSpec = "PolyResdrawing",
    layer_heat: LayerSpec = "HeatResdrawing",
    layer_gate: LayerSpec = "GatPolydrawing",
    layer_contact: LayerSpec = "Contdrawing",
    layer_metal1: LayerSpec = "Metal1drawing",
    layer_metal1_pin: LayerSpec = "Metal1pin",
    layer_res_mark: LayerSpec = "RESdrawing",
    layer_block: LayerSpec = "EXTBlockdrawing",
) -> Component:
    """Create a vertical silicided polysilicon resistor (i.e. with dy as its length)

    Args:
        dy: length of the resistor in micrometers.
        dx: width of the resistor in micrometers.
        resistance: Target resistance in ohms (optional).
        model: Device model name.
        layer_poly: Polysilicon layer.
        layer_heat: Thermal resistor marker.
        layer_gate: Gate polysilicon layer.
        layer_contact: Contact layer.
        layer_metal1: Metal1 layer.
        layer_metal1_pin: Metal1 pin layer.
        layer_res_mark: Resistor marker layer.
        layer_block: Blocking layer.

    Returns:
        Component with silicided poly resistor layout.

    Raises:
        ValueError: If dx (width) or dy (length) is outside allowed range.
    """
    if dx < _TECH.rsil_min_width or dx > _TECH.rsil_max_width:
        raise ValueError(
            f"rsil dx={dx} out of range [{_TECH.rsil_min_width}, {_TECH.rsil_max_width}]"
        )
    if dy < _TECH.rsil_min_length or dy > _TECH.rsil_max_length:
        raise ValueError(
            f"rsil dy={dy} out of range [{_TECH.rsil_min_length}, {_TECH.rsil_max_length}]"
        )

    c = Component()

    # Constants
    RSIL_MIN_DY = 0.4
    RSIL_MIN_DX = 0.4
    GRID = 0.005

    SHEET_RESISTANCE = 7.0
    GAT_DY = 0.35

    # Geometry
    METAL_PAD_DY = 0.26
    GAT_METAL_MARGIN = 0.02
    METAL_CONTACT_MARGIN = 0.05
    BLOCK_MARGIN = 0.18

    # Snap to grid
    dy = max(dy, RSIL_MIN_DY)
    dx = max(dx, RSIL_MIN_DX)
    dy = round(dy / GRID) * GRID
    dx = round(dx / GRID) * GRID

    # Resistance calculation
    if resistance is None:
        n_squares = dy / dx
        resistance = n_squares * SHEET_RESISTANCE
    else:
        n_squares = dy / dx

    # Compute geometry
    # Resistor body bottom-left at (0,0)
    body_origin = (0.0, 0.0)

    # Pad sizes
    metal_pad_dx = dx - 2 * GAT_METAL_MARGIN
    metal_pad_dy = METAL_PAD_DY

    # Pad coordinates
    metal_pad_left_x = GAT_METAL_MARGIN
    metal_pad_upper_y = dy + GAT_DY - metal_pad_dy - GAT_METAL_MARGIN
    metal_pad_lower_y = -GAT_DY + GAT_METAL_MARGIN

    # Contacts inside pads
    contact_dx = metal_pad_dx - 2 * METAL_CONTACT_MARGIN
    contact_dy = metal_pad_dy - 2 * METAL_CONTACT_MARGIN
    contact_x = metal_pad_left_x + METAL_CONTACT_MARGIN
    contact_upper_y = metal_pad_upper_y + METAL_CONTACT_MARGIN
    contact_lower_y = metal_pad_lower_y + METAL_CONTACT_MARGIN

    # blocking rectangle size & origin
    block_dx = dx + 2 * BLOCK_MARGIN
    block_dy = dy + 2 * (GAT_DY + BLOCK_MARGIN)
    block_origin = ((dx - block_dx) / 2.0, (dy - block_dy) / 2.0)

    # Draw resistor body (polysilicon + heat + res marker)
    for ly in (layer_poly, layer_heat, layer_res_mark):
        add_rect(c, size=(dx, dy), layer=ly, origin=body_origin)

    # Gate extensions (top and bottom)
    gate_size = (dx, GAT_DY)
    add_rect(c, size=gate_size, layer=layer_gate, origin=(0.0, dy))
    add_rect(c, size=gate_size, layer=layer_gate, origin=(0.0, -GAT_DY))

    # Metal pads (pin then metal1)
    for ly in (layer_metal1_pin, layer_metal1):
        add_rect(
            c,
            size=(metal_pad_dx, metal_pad_dy),
            layer=ly,
            origin=(metal_pad_left_x, metal_pad_upper_y),
        )
        add_rect(
            c,
            size=(metal_pad_dx, metal_pad_dy),
            layer=ly,
            origin=(metal_pad_left_x, metal_pad_lower_y),
        )

    # Contacts (inside metal pads)
    add_rect(
        c,
        size=(contact_dx, contact_dy),
        layer=layer_contact,
        origin=(contact_x, contact_upper_y),
    )
    add_rect(
        c,
        size=(contact_dx, contact_dy),
        layer=layer_contact,
        origin=(contact_x, contact_lower_y),
    )

    # Blocking layer
    add_rect(c, size=(block_dx, block_dy), layer=layer_block, origin=block_origin)

    # Ports (derive from pad geometry)
    pad_center_x = metal_pad_left_x + metal_pad_dx / 2.0
    pad_upper_center_y = metal_pad_upper_y + metal_pad_dy / 2.0
    pad_lower_center_y = metal_pad_lower_y + metal_pad_dy / 2.0

    c.add_port(
        name="P1",
        center=(pad_center_x, pad_upper_center_y),
        width=metal_pad_dx,
        orientation=90,
        layer=layer_metal1_pin,
        port_type="electrical",
    )

    c.add_port(
        name="P2",
        center=(pad_center_x, pad_lower_center_y),
        width=metal_pad_dx,
        orientation=270,
        layer=layer_metal1_pin,
        port_type="electrical",
    )

    # Metadata
    c.info.update(
        {
            "model": model,
            "dy": dy,
            "dx": dx,
            "resistance": resistance,
            "sheet_resistance": SHEET_RESISTANCE,
            "n_squares": n_squares,
        }
    )

    return c


def rppd_schematic(
    dy: float = 0.5,
    dx: float = 0.5,
    resistance: float | None = None,
) -> DSchematic:
    s = DSchematic()
    s.info["symbol"] = "resistor"
    s.info["ports"] = [
        {"name": "P1", "side": "top", "type": "electric"},
        {"name": "P2", "side": "bottom", "type": "electric"},
        {"name": "BN", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "implementation": "NgSpice",
            "name": "rppd",
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerRES.lib",
            "sections": ["res_typ", "res_bcs", "res_wcs"],
            "port_order": ["P1", "P2", "BN"],
            "params": {"w": "dx * 1e-6", "l": "dy * 1e-6", "m": "1"},
        },
        {
            "language": "spectre",
            "implementation": "VACASK",
            "name": "rppd",
            "spice_type": "SUBCKT",
            "library": "ihp/models/vacask/models/cornerRES.lib",
            "sections": ["res_typ", "res_bcs", "res_wcs"],
            "port_order": ["P1", "P2", "BN"],
            "params": {"w": "dx * 1e-6", "l": "dy * 1e-6", "m": "1"},
        },
    ]
    s.create_port(name="P1", cross_section=_XS, x=0, y=1, orientation=90)
    s.create_port(name="P2", cross_section=_XS, x=0, y=-1, orientation=270)
    s.create_port(name="BN", cross_section=_XS, x=1, y=0, orientation=0)
    return s


@gf.cell(schematic_function=rppd_schematic, tags=["IHP", "resistor", "unsilicided"])
def rppd(
    dy: float = 0.5,
    dx: float = 0.5,
    resistance: float | None = None,
    model: str = "rppd",
    layer_poly: LayerSpec = "PolyResdrawing",
    layer_heat: LayerSpec = "HeatResdrawing",
    layer_gate: LayerSpec = "GatPolydrawing",
    layer_contact: LayerSpec = "Contdrawing",
    layer_metal1: LayerSpec = "Metal1drawing",
    layer_metal1_pin: LayerSpec = "Metal1pin",
    layer_pSD: LayerSpec = "pSDdrawing",
    layer_block: LayerSpec = "EXTBlockdrawing",
    layer_sal_block: LayerSpec = "SalBlockdrawing",
) -> Component:
    """Create a vertical P+ polysilicon resistor (i.e. with dy as its length).

    Args:
        dy: length of the resistor in micrometers.
        dx: width of the resistor in micrometers.
        resistance: Target resistance in ohms (optional).
        model: Device model name.
        layer_poly: Polysilicon layer.
        layer_heat: Thermal resistor marker.
        layer_gate: Gate polysilicon layer.
        layer_contact: Contact layer.
        layer_metal1: Metal1 layer.
        layer_metal1_pin: Metal1 pin layer.
        layer_pSD: PSD layer.
        layer_block: Blocking layer.
        layer_sal_block: Salicide block layer.

    Returns:
        Component with P+ resistor layout.

    Raises:
        ValueError: If dx (width) or dy (length) is outside allowed range.
    """
    if dx < _TECH.rppd_min_width or dx > _TECH.rppd_max_width:
        raise ValueError(
            f"rppd dx={dx} out of range [{_TECH.rppd_min_width}, {_TECH.rppd_max_width}]"
        )
    if dy < _TECH.rppd_min_length or dy > _TECH.rppd_max_length:
        raise ValueError(
            f"rppd dy={dy} out of range [{_TECH.rppd_min_length}, {_TECH.rppd_max_length}]"
        )

    c = Component()

    # Constants
    RPPD_MIN_DY = 0.4
    RPPD_MIN_DX = 0.5
    GRID = 0.005

    SHEET_RESISTANCE = 300.0
    GAT_DY = 0.43

    # Geometry
    METAL_PAD_DY = 0.30
    METAL_CONTACT_MARGIN_DX = 0.05
    METAL_CONTACT_MARGIN_DY = 0.07
    GAT_METAL_MARGIN_DX = 0.02
    GAT_METAL_MARGIN_DY = 0.00

    BLOCK_MARGIN = 0.18
    BLOCK2_MARGIN = 0.02

    # Snap to grid
    dy = max(dy, RPPD_MIN_DY)
    dx = max(dx, RPPD_MIN_DX)
    dy = round(dy / GRID) * GRID
    dx = round(dx / GRID) * GRID

    # Resistance calculation
    if resistance is None:
        n_squares = dy / dx
        resistance = n_squares * SHEET_RESISTANCE
    else:
        n_squares = dy / dx

    # Geometry
    body_origin = (0.0, 0.0)

    # Metal pad sizes
    metal_pad_dx = dx - 2 * GAT_METAL_MARGIN_DX
    metal_pad_dy = METAL_PAD_DY

    # Metal pad coordinates
    metal_pad_left_x = GAT_METAL_MARGIN_DX
    metal_pad_upper_y = dy + GAT_DY - metal_pad_dy - GAT_METAL_MARGIN_DY
    metal_pad_lower_y = -GAT_DY + GAT_METAL_MARGIN_DY

    # Contact sizes
    contact_dx = metal_pad_dx - 2 * METAL_CONTACT_MARGIN_DX
    contact_dy = metal_pad_dy - 2 * METAL_CONTACT_MARGIN_DY

    contact_left_x = metal_pad_left_x + METAL_CONTACT_MARGIN_DX
    contact_upper_y = metal_pad_upper_y + METAL_CONTACT_MARGIN_DY
    contact_lower_y = metal_pad_lower_y + METAL_CONTACT_MARGIN_DY

    # Blocking layers
    block_dx = dx + 2 * BLOCK_MARGIN
    block_dy = dy + 2 * (GAT_DY + BLOCK_MARGIN)
    block_origin = ((dx - block_dx) / 2.0, (dy - block_dy) / 2.0)

    block2_dx = block_dx + 2 * BLOCK2_MARGIN
    block2_dy = dy
    block2_origin = ((dx - block2_dx) / 2.0, (dy - block2_dy) / 2.0)

    # Draw resistor body
    for ly in (layer_poly, layer_heat):
        add_rect(c, size=(dx, dy), layer=ly, origin=body_origin)

    # Gate poly extensions
    gate_size = (dx, GAT_DY)
    add_rect(c, size=gate_size, layer=layer_gate, origin=(0.0, dy))
    add_rect(c, size=gate_size, layer=layer_gate, origin=(0.0, -GAT_DY))

    # Contacts
    add_rect(
        c,
        size=(contact_dx, contact_dy),
        layer=layer_contact,
        origin=(contact_left_x, contact_upper_y),
    )
    add_rect(
        c,
        size=(contact_dx, contact_dy),
        layer=layer_contact,
        origin=(contact_left_x, contact_lower_y),
    )

    # Metal pads (pin + metal1)
    for ly in (layer_metal1_pin, layer_metal1):
        add_rect(
            c,
            size=(metal_pad_dx, metal_pad_dy),
            layer=ly,
            origin=(metal_pad_left_x, metal_pad_upper_y),
        )
        add_rect(
            c,
            size=(metal_pad_dx, metal_pad_dy),
            layer=ly,
            origin=(metal_pad_left_x, metal_pad_lower_y),
        )

    # Blocking layers
    for ly in (layer_block, layer_pSD):
        add_rect(c, size=(block_dx, block_dy), layer=ly, origin=block_origin)

    for ly in (layer_block, layer_sal_block):
        add_rect(c, size=(block2_dx, block2_dy), layer=ly, origin=block2_origin)

    # Ports
    metal_pad_center_x = metal_pad_left_x + metal_pad_dx / 2.0
    metal_pad_upper_center_y = metal_pad_upper_y + metal_pad_dy / 2.0
    metal_pad_lower_center_y = metal_pad_lower_y + metal_pad_dy / 2.0

    c.add_port(
        name="P1",
        center=(metal_pad_center_x, metal_pad_upper_center_y),
        width=metal_pad_dx,
        orientation=90,
        layer=layer_metal1_pin,
        port_type="electrical",
    )

    c.add_port(
        name="P2",
        center=(metal_pad_center_x, metal_pad_lower_center_y),
        width=metal_pad_dx,
        orientation=270,
        layer=layer_metal1_pin,
        port_type="electrical",
    )

    # Metadata
    c.info.update(
        {
            "model": model,
            "dy": dy,
            "dx": dx,
            "resistance": resistance,
            "sheet_resistance": SHEET_RESISTANCE,
            "n_squares": n_squares,
        }
    )

    return c


def rhigh_schematic(
    dy: float = 0.96,
    dx: float = 0.5,
    resistance: float | None = None,
) -> DSchematic:
    s = DSchematic()
    s.info["symbol"] = "resistor"
    s.info["ports"] = [
        {"name": "P1", "side": "top", "type": "electric"},
        {"name": "P2", "side": "bottom", "type": "electric"},
        {"name": "BN", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "implementation": "NgSpice",
            "name": "rhigh",
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerRES.lib",
            "sections": ["res_typ", "res_bcs", "res_wcs"],
            "port_order": ["P1", "P2", "BN"],
            "params": {"w": "dx * 1e-6", "l": "dy * 1e-6", "m": "1"},
        },
        {
            "language": "spectre",
            "implementation": "VACASK",
            "name": "rhigh",
            "spice_type": "SUBCKT",
            "library": "ihp/models/vacask/models/cornerRES.lib",
            "sections": ["res_typ", "res_bcs", "res_wcs"],
            "port_order": ["P1", "P2", "BN"],
            "params": {"w": "dx * 1e-6", "l": "dy * 1e-6", "m": "1"},
        },
    ]
    s.create_port(name="P1", cross_section=_XS, x=0, y=1, orientation=90)
    s.create_port(name="P2", cross_section=_XS, x=0, y=-1, orientation=270)
    s.create_port(name="BN", cross_section=_XS, x=1, y=0, orientation=0)
    return s


@gf.cell(schematic_function=rhigh_schematic, tags=["IHP", "resistor", "high-r"])
def rhigh(
    dy: float = 0.96,
    dx: float = 0.5,
    resistance: float | None = None,
    model: str = "rhigh",
    layer_poly: LayerSpec = "PolyResdrawing",
    layer_heat: LayerSpec = "HeatResdrawing",
    layer_gate: LayerSpec = "GatPolydrawing",
    layer_contact: LayerSpec = "Contdrawing",
    layer_metal1: LayerSpec = "Metal1drawing",
    layer_metal1_pin: LayerSpec = "Metal1pin",
    layer_pSD: LayerSpec = "pSDdrawing",
    layer_nSD: LayerSpec = "nSDdrawing",
    layer_block: LayerSpec = "EXTBlockdrawing",
    layer_sal_block: LayerSpec = "SalBlockdrawing",
) -> Component:
    """Create a vertical high-resistance polysilicon resistor (i.e. with dy as its length).

    Args:
        dy: length of the resistor in micrometers.
        dx: width of the resistor in micrometers.
        resistance: Target resistance in ohms (optional).
        model: Device model name.
        layer_poly: Polysilicon layer.
        layer_heat: Thermal resistor marker.
        layer_gate: Gate polysilicon layer.
        layer_contact: Contact layer.
        layer_metal1: Metal1 layer.
        layer_metal1_pin: Metal1 pin layer.
        layer_pSD: PSD layer.
        layer_nSD: NSD layer
        layer_block: Blocking layer.
        layer_sal_block: Salicide block layer.

    Returns:
        Component with high-resistance poly resistor layout.

    Raises:
        ValueError: If dx (width) or dy (length) is outside allowed range.
    """
    if dx < _TECH.rhigh_min_width or dx > _TECH.rhigh_max_width:
        raise ValueError(
            f"rhigh dx={dx} out of range [{_TECH.rhigh_min_width}, {_TECH.rhigh_max_width}]"
        )
    if dy < _TECH.rhigh_min_length or dy > _TECH.rhigh_max_length:
        raise ValueError(
            f"rhigh dy={dy} out of range [{_TECH.rhigh_min_length}, {_TECH.rhigh_max_length}]"
        )

    c = Component()

    # Constants
    RHIGH_MIN_DY = 0.4
    RHIGH_MIN_DX = 0.5
    GRID = 0.005

    SHEET_RESISTANCE = 300.0
    GAT_DY = 0.43

    # Fundamental geometry constants
    METAL_PAD_DY = 0.26
    METAL_CONTACT_MARGIN = 0.05
    GAT_METAL_MARGIN = 0.02

    BLOCK1_MARGIN = 0.18
    BLOCK2_MARGIN = 0.02

    # Snap to grid
    dy = max(dy, RHIGH_MIN_DY)
    dx = max(dx, RHIGH_MIN_DX)
    dy = round(dy / GRID) * GRID
    dx = round(dx / GRID) * GRID

    # Resistance calculation
    if resistance is None:
        n_squares = dy / dx
        resistance = n_squares * SHEET_RESISTANCE
    else:
        n_squares = dy / dx

    # Compute geometry
    body_origin = (0.0, 0.0)

    # Metal pad sizes
    metal_pad_dx = dx - 2 * GAT_METAL_MARGIN
    metal_pad_dy = METAL_PAD_DY

    # Metal pad positions
    metal_pad_left_x = GAT_METAL_MARGIN
    metal_pad_upper_y = dy + GAT_DY - metal_pad_dy - GAT_METAL_MARGIN
    metal_pad_lower_y = -GAT_DY + GAT_METAL_MARGIN

    # Contacts inside metal pads
    contact_dx = metal_pad_dx - 2 * METAL_CONTACT_MARGIN
    contact_dy = metal_pad_dy - 2 * METAL_CONTACT_MARGIN

    contact_left_x = metal_pad_left_x + METAL_CONTACT_MARGIN
    contact_upper_y = metal_pad_upper_y + METAL_CONTACT_MARGIN
    contact_lower_y = metal_pad_lower_y + METAL_CONTACT_MARGIN

    # Blocking layer geometry
    block1_dx = dx + 2 * BLOCK1_MARGIN
    block1_dy = dy + 2 * (GAT_DY + BLOCK1_MARGIN)
    block1_origin = ((dx - block1_dx) / 2, (dy - block1_dy) / 2)

    block2_dx = block1_dx + 2 * BLOCK2_MARGIN
    block2_dy = dy
    block2_origin = ((dx - block2_dx) / 2, (dy - block2_dy) / 2)

    # Draw resistor body (poly + heat)
    for ly in (layer_poly, layer_heat):
        add_rect(c, size=(dx, dy), layer=ly, origin=body_origin)

    # Gate extensions
    gate_size = (dx, GAT_DY)
    add_rect(c, gate_size, layer_gate, origin=(0.0, dy))
    add_rect(c, gate_size, layer_gate, origin=(0.0, -GAT_DY))

    # Contacts
    add_rect(
        c,
        (contact_dx, contact_dy),
        layer_contact,
        origin=(contact_left_x, contact_upper_y),
    )
    add_rect(
        c,
        (contact_dx, contact_dy),
        layer_contact,
        origin=(contact_left_x, contact_lower_y),
    )

    # Metal pads
    for ly in (layer_metal1_pin, layer_metal1):
        add_rect(
            c,
            (metal_pad_dx, metal_pad_dy),
            ly,
            origin=(metal_pad_left_x, metal_pad_upper_y),
        )
        add_rect(
            c,
            (metal_pad_dx, metal_pad_dy),
            ly,
            origin=(metal_pad_left_x, metal_pad_lower_y),
        )

    # Blocking 1
    for ly in (layer_block, layer_pSD, layer_nSD):
        add_rect(c, (block1_dx, block1_dy), ly, origin=block1_origin)

    # Blocking 2
    for ly in (layer_block, layer_sal_block):
        add_rect(c, (block2_dx, block2_dy), ly, origin=block2_origin)

    # Ports
    metal_pad_center_x = metal_pad_left_x + metal_pad_dx / 2.0
    metal_pad_upper_center_y = metal_pad_upper_y + metal_pad_dy / 2.0
    metal_pad_lower_center_y = metal_pad_lower_y + metal_pad_dy / 2.0

    c.add_port(
        name="P1",
        center=(metal_pad_center_x, metal_pad_upper_center_y),
        width=metal_pad_dx,
        orientation=90,
        layer=layer_metal1_pin,
        port_type="electrical",
    )

    c.add_port(
        name="P2",
        center=(metal_pad_center_x, metal_pad_lower_center_y),
        width=metal_pad_dx,
        orientation=270,
        layer=layer_metal1_pin,
        port_type="electrical",
    )

    # Metadata
    c.info.update(
        {
            "model": model,
            "dy": dy,
            "dx": dx,
            "resistance": resistance,
            "sheet_resistance": SHEET_RESISTANCE,
            "n_squares": n_squares,
        }
    )

    return c
