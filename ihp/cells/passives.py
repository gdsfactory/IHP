"""Passive components (varicaps, ESD, taps, seal rings) for IHP PDK."""

import gdsfactory as gf
from gdsfactory import Component
from gdsfactory.typings import LayerSpec

from typing import Literal, Union, Optional, TypeAlias, List
import numpy as np
from numpy import floor, round

from ihp import tech, cells

FloatLike: TypeAlias = Union[np.float32, np.float64, float]
Point: TypeAlias = tuple[FloatLike, FloatLike]

@gf.cell
def svaricap(
    width: float = 1.0,
    length: float = 1.0,
    nf: int = 1,
    model: str = "svaricap",
    layer_nwell: LayerSpec = "NWelldrawing",
    layer_activ: LayerSpec = "Activdrawing",
    layer_gatpoly: LayerSpec = "GatPolydrawing",
    layer_nsd: LayerSpec = "nSDdrawing",
    layer_cont: LayerSpec = "Contdrawing",
    layer_metal1: LayerSpec = "Metal1drawing",
    layer_varicap: LayerSpec = "Varicapdrawing",
) -> Component:
    """Create a MOS varicap (variable capacitor).

    Args:
        width: Width of the varicap in micrometers.
        length: Length of the varicap in micrometers.
        nf: Number of fingers.
        model: Device model name.
        layer_nwell: N-well layer.
        layer_activ: Active region layer.
        layer_gatpoly: Gate polysilicon layer.
        layer_nsd: N+ source/drain doping layer.
        layer_cont: Contact layer.
        layer_metal1: Metal1 layer.
        layer_varicap: Varicap marker layer.

    Returns:
        Component with varicap layout.
    """
    c = Component()

    # Design rules
    var_min_width = 0.5
    var_min_length = 0.5
    gate_ext = 0.18
    active_ext = 0.23
    cont_size = 0.16
    cont_enc = 0.07
    nwell_enc = 0.31

    # Validate dimensions
    width = max(width, var_min_width)
    length = max(length, var_min_length)

    # Grid snap
    grid = 0.005
    width = round(width / grid) * grid
    length = round(length / grid) * grid

    # Calculate finger dimensions
    finger_width = width / nf
    finger_pitch = finger_width + 0.5

    # N-Well
    nwell = gf.components.rectangle(
        size=(
            length + 2 * active_ext + 2 * nwell_enc,
            nf * finger_pitch + 2 * nwell_enc,
        ),
        layer=layer_nwell,
        centered=True,
    )
    c.add_ref(nwell)

    # Create varicap fingers
    for i in range(nf):
        y_offset = (i - nf / 2 + 0.5) * finger_pitch

        # Gate poly (acts as one terminal)
        gate = gf.components.rectangle(
            size=(length, finger_width + 2 * gate_ext),
            layer=layer_gatpoly,
        )
        gate_ref = c.add_ref(gate)
        gate_ref.move((-length / 2, y_offset - finger_width / 2 - gate_ext))

        # Active region (acts as other terminal)
        active = gf.components.rectangle(
            size=(length + 2 * active_ext, finger_width),
            layer=layer_activ,
        )
        active_ref = c.add_ref(active)
        active_ref.move((-length / 2 - active_ext, y_offset - finger_width / 2))

        # N+ implant for active region
        nsd = gf.components.rectangle(
            size=(length + 2 * active_ext, finger_width),
            layer=layer_nsd,
        )
        nsd_ref = c.add_ref(nsd)
        nsd_ref.move((-length / 2 - active_ext, y_offset - finger_width / 2))

        # Contacts on active regions (source/drain)
        # Left side contacts
        cont_left = gf.components.rectangle(
            size=(cont_size, cont_size),
            layer=layer_cont,
        )
        cont_left_ref = c.add_ref(cont_left)
        cont_left_ref.move(
            (-length / 2 - active_ext + cont_enc, y_offset - cont_size / 2)
        )

        # Right side contacts
        cont_right = gf.components.rectangle(
            size=(cont_size, cont_size),
            layer=layer_cont,
        )
        cont_right_ref = c.add_ref(cont_right)
        cont_right_ref.move(
            (length / 2 + active_ext - cont_enc - cont_size, y_offset - cont_size / 2)
        )

    # Metal connections
    # Gate connection (Metal1)
    gate_metal = gf.components.rectangle(
        size=(1.0, nf * finger_pitch),
        layer=layer_metal1,
    )
    gate_metal_ref = c.add_ref(gate_metal)
    gate_metal_ref.move((-length / 2 - 1.5, -nf * finger_pitch / 2))

    # Active connection (Metal1)
    active_metal = gf.components.rectangle(
        size=(1.0, nf * finger_pitch),
        layer=layer_metal1,
    )
    active_metal_ref = c.add_ref(active_metal)
    active_metal_ref.move((length / 2 + 0.5, -nf * finger_pitch / 2))

    # Varicap marker
    var_mark = gf.components.rectangle(
        size=(length + 2 * active_ext + 0.5, nf * finger_pitch + 0.5),
        layer=layer_varicap,
        centered=True,
    )
    c.add_ref(var_mark)

    # Add ports
    c.add_port(
        name="G",
        center=(-length / 2 - 1.0, 0),
        width=nf * finger_pitch,
        orientation=180,
        layer=layer_metal1,
        port_type="electrical",
    )

    c.add_port(
        name="B",
        center=(length / 2 + 1.0, 0),
        width=nf * finger_pitch,
        orientation=0,
        layer=layer_metal1,
        port_type="electrical",
    )

    # Add metadata
    c.info["model"] = model
    c.info["width"] = width
    c.info["length"] = length
    c.info["nf"] = nf
    c.info["type"] = "varicap"

    return c


@gf.cell
def esd_nmos(
    width: float = 50.0,
    length: float = 0.5,
    nf: int = 10,
    model: str = "esd_nmos",
    layer_pwell: LayerSpec = "PWelldrawing",
    layer_activ: LayerSpec = "Activdrawing",
    layer_gatpoly: LayerSpec = "GatPolydrawing",
    layer_nsd: LayerSpec = "nSDdrawing",
    layer_cont: LayerSpec = "Contdrawing",
    layer_metal1: LayerSpec = "Metal1drawing",
    layer_metal2: LayerSpec = "Metal2drawing",
    layer_esd: LayerSpec = "Recogesd",
) -> Component:
    """Create an ESD protection NMOS device.

    Args:
        width: Total width of the ESD device in micrometers.
        length: Gate length in micrometers.
        nf: Number of fingers.
        model: Device model name.
        layer_pwell: P-well layer.
        layer_activ: Active region layer.
        layer_gatpoly: Gate polysilicon layer.
        layer_nsd: N+ source/drain doping layer.
        layer_cont: Contact layer.
        layer_metal1: Metal1 layer.
        layer_metal2: Metal2 layer.
        layer_esd: ESD marker layer.

    Returns:
        Component with ESD NMOS layout.
    """
    c = Component()

    # Design rules for ESD devices
    gate_width = width / nf
    gate_length = length
    gate_ext = 0.18
    active_ext = 0.3  # Larger for ESD
    cont_size = 0.16
    cont_spacing = 0.18
    cont_enc = 0.07
    metal_enc = 0.06
    pwell_enc = 0.5

    # Grid snap
    grid = 0.005
    gate_width = round(gate_width / grid) * grid
    gate_length = round(gate_length / grid) * grid

    # P-Well for ESD NMOS
    pwell = gf.components.rectangle(
        size=(
            (gate_length + 2 * active_ext) * nf + pwell_enc * 2,
            gate_width + 2 * gate_ext + pwell_enc * 2,
        ),
        layer=layer_pwell,
        centered=True,
    )
    c.add_ref(pwell)

    # Create multi-finger ESD structure
    finger_pitch = gate_length + 2 * active_ext + 0.5

    for i in range(nf):
        x_offset = (i - nf / 2 + 0.5) * finger_pitch

        # Gate poly
        gate = gf.components.rectangle(
            size=(gate_length, gate_width + 2 * gate_ext),
            layer=layer_gatpoly,
        )
        gate_ref = c.add_ref(gate)
        gate_ref.move((x_offset - gate_length / 2, -gate_width / 2 - gate_ext))

        # Active region
        active = gf.components.rectangle(
            size=(gate_length + 2 * active_ext, gate_width),
            layer=layer_activ,
        )
        active_ref = c.add_ref(active)
        active_ref.move((x_offset - gate_length / 2 - active_ext, -gate_width / 2))

        # N+ implant
        nsd = gf.components.rectangle(
            size=(gate_length + 2 * active_ext, gate_width),
            layer=layer_nsd,
        )
        nsd_ref = c.add_ref(nsd)
        nsd_ref.move((x_offset - gate_length / 2 - active_ext, -gate_width / 2))

        # Source/Drain contacts
        n_cont_y = int((gate_width - cont_size) / cont_spacing) + 1

        for j in range(n_cont_y):
            y_pos = -gate_width / 2 + cont_enc + j * cont_spacing

            # Source contact
            cont_s = gf.components.rectangle(
                size=(cont_size, cont_size),
                layer=layer_cont,
            )
            cont_s_ref = c.add_ref(cont_s)
            cont_s_ref.move((x_offset - gate_length / 2 - active_ext + cont_enc, y_pos))

            # Drain contact
            cont_d = gf.components.rectangle(
                size=(cont_size, cont_size),
                layer=layer_cont,
            )
            cont_d_ref = c.add_ref(cont_d)
            cont_d_ref.move((x_offset + gate_length / 2 + cont_enc, y_pos))

    # Metal bus connections
    # Source bus (connected to ground)
    source_bus = gf.components.rectangle(
        size=(nf * finger_pitch, gate_width + 2 * metal_enc),
        layer=layer_metal1,
    )
    source_bus_ref = c.add_ref(source_bus)
    source_bus_ref.move((-nf * finger_pitch / 2, -gate_width / 2 - metal_enc))

    # Drain bus (connected to I/O pad)
    drain_bus = gf.components.rectangle(
        size=(nf * finger_pitch, 1.0),
        layer=layer_metal2,
    )
    drain_bus_ref = c.add_ref(drain_bus)
    drain_bus_ref.move((-nf * finger_pitch / 2, gate_width / 2 + 1.0))

    # Gate bus (can be tied to source or left floating)
    gate_bus = gf.components.rectangle(
        size=(nf * finger_pitch, 0.5),
        layer=layer_gatpoly,
    )
    gate_bus_ref = c.add_ref(gate_bus)
    gate_bus_ref.move((-nf * finger_pitch / 2, -gate_width / 2 - gate_ext - 0.5))

    # ESD marker
    esd_mark = gf.components.rectangle(
        size=(nf * finger_pitch + 1.0, gate_width + 3.0),
        layer=layer_esd,
        centered=True,
    )
    c.add_ref(esd_mark)

    # Add ports
    c.add_port(
        name="PAD",
        center=(0, gate_width / 2 + 1.5),
        width=nf * finger_pitch,
        orientation=90,
        layer=layer_metal2,
        port_type="electrical",
    )

    c.add_port(
        name="GND",
        center=(0, -gate_width / 2),
        width=nf * finger_pitch,
        orientation=270,
        layer=layer_metal1,
        port_type="electrical",
    )

    # Add metadata
    c.info["model"] = model
    c.info["width"] = width
    c.info["length"] = length
    c.info["nf"] = nf
    c.info["type"] = "esd_nmos"

    return c


@gf.cell
def ptap1(
    width: float = 1.0,
    length: float = 1.0,
    rows: int = 1,
    cols: int = 1,
    layer_activ: LayerSpec = "Activdrawing",
    layer_psd: LayerSpec = "pSDdrawing",
    layer_cont: LayerSpec = "Contdrawing",
    layer_metal1: LayerSpec = "Metal1drawing",
) -> Component:
    """Create a P+ substrate tap.

    Args:
        width: Width of the tap in micrometers.
        length: Length of the tap in micrometers.
        rows: Number of contact rows.
        cols: Number of contact columns.
        layer_activ: Active region layer.
        layer_psd: P+ source/drain doping layer.
        layer_cont: Contact layer.
        layer_metal1: Metal1 layer.

    Returns:
        Component with P+ tap layout.
    """
    c = Component()

    # Design rules
    cont_size = 0.16
    cont_spacing = 0.18
    metal_enc = 0.06
    tap_enc = 0.1

    # Grid snap
    grid = 0.005
    width = round(width / grid) * grid
    length = round(length / grid) * grid

    # P+ active region
    active = gf.components.rectangle(
        size=(length, width),
        layer=layer_activ,
        centered=True,
    )
    c.add_ref(active)

    # P+ implant
    psd = gf.components.rectangle(
        size=(length + 2 * tap_enc, width + 2 * tap_enc),
        layer=layer_psd,
        centered=True,
    )
    c.add_ref(psd)

    # Contact array
    cont_array_width = cont_size * cols + cont_spacing * (cols - 1)
    cont_array_height = cont_size * rows + cont_spacing * (rows - 1)

    for i in range(cols):
        for j in range(rows):
            x = -cont_array_width / 2 + cont_size / 2 + i * (cont_size + cont_spacing)
            y = -cont_array_height / 2 + cont_size / 2 + j * (cont_size + cont_spacing)

            cont = gf.components.rectangle(
                size=(cont_size, cont_size),
                layer=layer_cont,
                centered=True,
            )
            cont_ref = c.add_ref(cont)
            cont_ref.move((x, y))

    # Metal1 connection
    metal = gf.components.rectangle(
        size=(cont_array_width + 2 * metal_enc, cont_array_height + 2 * metal_enc),
        layer=layer_metal1,
        centered=True,
    )
    c.add_ref(metal)

    # Add port
    c.add_port(
        name="TAP",
        center=(0, 0),
        width=width,
        orientation=0,
        layer=layer_metal1,
        port_type="electrical",
    )

    # Add metadata
    c.info["type"] = "ptap"
    c.info["width"] = width
    c.info["length"] = length
    c.info["rows"] = rows
    c.info["cols"] = cols

    return c


@gf.cell
def ntap1(
    width: float = 1.0,
    length: float = 1.0,
    rows: int = 1,
    cols: int = 1,
    layer_nwell: LayerSpec = "NWelldrawing",
    layer_activ: LayerSpec = "Activdrawing",
    layer_nsd: LayerSpec = "nSDdrawing",
    layer_cont: LayerSpec = "Contdrawing",
    layer_metal1: LayerSpec = "Metal1drawing",
) -> Component:
    """Create an N+ substrate tap.

    Args:
        width: Width of the tap in micrometers.
        length: Length of the tap in micrometers.
        rows: Number of contact rows.
        cols: Number of contact columns.
        layer_nwell: N-well layer.
        layer_activ: Active region layer.
        layer_nsd: N+ source/drain doping layer.
        layer_cont: Contact layer.
        layer_metal1: Metal1 layer.

    Returns:
        Component with N+ tap layout.
    """
    c = Component()

    # Design rules
    cont_size = 0.16
    cont_spacing = 0.18
    metal_enc = 0.06
    tap_enc = 0.1
    nwell_enc = 0.31

    # Grid snap
    grid = 0.005
    width = round(width / grid) * grid
    length = round(length / grid) * grid

    # N-Well
    nwell = gf.components.rectangle(
        size=(length + 2 * nwell_enc, width + 2 * nwell_enc),
        layer=layer_nwell,
        centered=True,
    )
    c.add_ref(nwell)

    # N+ active region
    active = gf.components.rectangle(
        size=(length, width),
        layer=layer_activ,
        centered=True,
    )
    c.add_ref(active)

    # N+ implant
    nsd = gf.components.rectangle(
        size=(length + 2 * tap_enc, width + 2 * tap_enc),
        layer=layer_nsd,
        centered=True,
    )
    c.add_ref(nsd)

    # Contact array
    cont_array_width = cont_size * cols + cont_spacing * (cols - 1)
    cont_array_height = cont_size * rows + cont_spacing * (rows - 1)

    for i in range(cols):
        for j in range(rows):
            x = -cont_array_width / 2 + cont_size / 2 + i * (cont_size + cont_spacing)
            y = -cont_array_height / 2 + cont_size / 2 + j * (cont_size + cont_spacing)

            cont = gf.components.rectangle(
                size=(cont_size, cont_size),
                layer=layer_cont,
                centered=True,
            )
            cont_ref = c.add_ref(cont)
            cont_ref.move((x, y))

    # Metal1 connection
    metal = gf.components.rectangle(
        size=(cont_array_width + 2 * metal_enc, cont_array_height + 2 * metal_enc),
        layer=layer_metal1,
        centered=True,
    )
    c.add_ref(metal)

    # Add port
    c.add_port(
        name="TAP",
        center=(0, 0),
        width=width,
        orientation=0,
        layer=layer_metal1,
        port_type="electrical",
    )

    # Add metadata
    c.info["type"] = "ntap"
    c.info["width"] = width
    c.info["length"] = length
    c.info["rows"] = rows
    c.info["cols"] = cols

    return c


@gf.cell
def sealring(
    width: float = 200.0,
    height: float = 200.0,
    ring_width: float = 5.0,
    layer_metal1: LayerSpec = "Metal1drawing",
    layer_metal2: LayerSpec = "Metal2drawing",
    layer_metal3: LayerSpec = "Metal3drawing",
    layer_metal4: LayerSpec = "Metal4drawing",
    layer_metal5: LayerSpec = "Metal5drawing",
    layer_topmetal1: LayerSpec = "TopMetal1drawing",
    layer_topmetal2: LayerSpec = "TopMetal2drawing",
    layer_via1: LayerSpec = "Via1drawing",
    layer_via2: LayerSpec = "Via2drawing",
    layer_via3: LayerSpec = "Via3drawing",
    layer_via4: LayerSpec = "Via4drawing",
    layer_topvia1: LayerSpec = "TopVia1drawing",
    layer_topvia2: LayerSpec = "TopVia2drawing",
    layer_sealring: LayerSpec = "EdgeSealdrawing",
) -> Component:
    """Create a seal ring for die protection.

    Args:
        width: Inner width of the seal ring in micrometers.
        height: Inner height of the seal ring in micrometers.
        ring_width: Width of the seal ring metal in micrometers.
        layer_metal1: Metal1 layer.
        layer_metal2: Metal2 layer.
        layer_metal3: Metal3 layer.
        layer_metal4: Metal4 layer.
        layer_metal5: Metal5 layer.
        layer_topmetal1: TopMetal1 layer.
        layer_topmetal2: TopMetal2 layer.
        layer_via1: Via1 layer.
        layer_via2: Via2 layer.
        layer_via3: Via3 layer.
        layer_via4: Via4 layer.
        layer_topvia1: TopVia1 layer.
        layer_topvia2: TopVia2 layer.
        layer_sealring: Seal ring marker layer.

    Returns:
        Component with seal ring layout.
    """
    c = Component()

    # Create seal ring on all metal layers
    metal_layers = [
        layer_metal1,
        layer_metal2,
        layer_metal3,
        layer_metal4,
        layer_metal5,
        layer_topmetal1,
        layer_topmetal2,
    ]

    # Create ring on each metal layer
    for metal_layer in metal_layers:
        # Outer rectangle
        outer = gf.components.rectangle(
            size=(width + 2 * ring_width, height + 2 * ring_width),
            layer=metal_layer,
            centered=True,
        )

        # Inner rectangle (to create ring)
        inner = gf.components.rectangle(
            size=(width, height),
            layer=metal_layer,
            centered=True,
        )

        # Create ring by boolean subtraction
        ring = gf.boolean(outer, inner, "A-B", layer=metal_layer)
        c.add_ref(ring)

    # Add vias between metal layers
    via_layers = [
        layer_via1,
        layer_via2,
        layer_via3,
        layer_via4,
        layer_topvia1,
        layer_topvia2,
    ]

    # Via arrays in the ring
    via_size = 0.26
    via_spacing = 0.36

    for via_layer in via_layers:
        # Calculate number of vias along each edge
        n_vias_x = int((width + ring_width - via_size) / via_spacing)
        n_vias_y = int((height + ring_width - via_size) / via_spacing)

        # Top edge vias
        for i in range(n_vias_x):
            x = -width / 2 - ring_width / 2 + via_size / 2 + i * via_spacing
            y = height / 2 + ring_width / 2

            via = gf.components.rectangle(
                size=(via_size, via_size),
                layer=via_layer,
                centered=True,
            )
            via_ref = c.add_ref(via)
            via_ref.move((x, y))

        # Bottom edge vias
        for i in range(n_vias_x):
            x = -width / 2 - ring_width / 2 + via_size / 2 + i * via_spacing
            y = -height / 2 - ring_width / 2

            via = gf.components.rectangle(
                size=(via_size, via_size),
                layer=via_layer,
                centered=True,
            )
            via_ref = c.add_ref(via)
            via_ref.move((x, y))

        # Left edge vias
        for i in range(n_vias_y):
            x = -width / 2 - ring_width / 2
            y = -height / 2 - ring_width / 2 + via_size / 2 + i * via_spacing

            via = gf.components.rectangle(
                size=(via_size, via_size),
                layer=via_layer,
                centered=True,
            )
            via_ref = c.add_ref(via)
            via_ref.move((x, y))

        # Right edge vias
        for i in range(n_vias_y):
            x = width / 2 + ring_width / 2
            y = -height / 2 - ring_width / 2 + via_size / 2 + i * via_spacing

            via = gf.components.rectangle(
                size=(via_size, via_size),
                layer=via_layer,
                centered=True,
            )
            via_ref = c.add_ref(via)
            via_ref.move((x, y))

    # Seal ring marker
    seal_mark = gf.components.rectangle(
        size=(width + 2 * ring_width + 1.0, height + 2 * ring_width + 1.0),
        layer=layer_sealring,
        centered=True,
    )
    seal_inner = gf.components.rectangle(
        size=(width - 1.0, height - 1.0),
        layer=layer_sealring,
        centered=True,
    )
    seal_ring_mark = gf.boolean(seal_mark, seal_inner, "A-B", layer=layer_sealring)
    c.add_ref(seal_ring_mark)

    # Add metadata
    c.info["type"] = "sealring"
    c.info["width"] = width
    c.info["height"] = height
    c.info["ring_width"] = ring_width

    return c

@gf.cell
def guard_ring(
    width: float = 0.5,
    guardRingSpacing: float = 0.14,
    guardRingType: Literal["psub", 'nwell'] = "psub",
    bbox: Optional[tuple[Point, Point]] = None,
    path: Optional[List[tuple[Point, Point]]] = None,
    layer_activ: LayerSpec = "Activdrawing",
    layer_cont: LayerSpec = "Contdrawing",
    layer_metal1: LayerSpec = "Metal1drawing",
    layer_psd: LayerSpec = "pSDdrawing",
    layer_nwell: LayerSpec = "NWelldrawing",
    layer_nsd: LayerSpec = "nSDdrawing",
    **kwargs
) -> Component:
    """
    Create an N-Well (NW) and N-Plus (NP) or a P-Plus (PP) 
    guard ring around a boundary box, or, if `bbox` is not provided, 
    along a provided `path` of points.
    
    Args:
        width: Width of the guard ring group path, 
            defining the width of the Metal1 Path.
        guardRingSpacing: Spacing between the Metal1 Path and the component BBox.
        guardRingType: Literal["psub", 'nwell'] Type of Guard-Ring (NP = nwell or PP = psub).
        bbox: Encapsulated component bounding box.
        path: Path point for the group path defining the Guard Ring,
        layer_activ: Activ drawing layer.
        layer_cont: Contact Via drawing layer. 
        layer_metal1: Metal1 drawing layer.
        layer_psd: pSD / P-Plus drawing layer.
        layer_nwell: NWell drawing layer.
        layer_nsd: nSD / N-Plus drawing layer.  
    Returns:
        c - Component containing the Guard-Ring group path.
    Raises:
    """
    
    gr_drc = {
        # metals
        'm1_min_width': tech.TECH.metal1_width,
        # active regions and contact
        'cont_min_size': tech.TECH.cont_size,
        'cont_min_spacing': tech.TECH.cont_spacing,
        'cont_min_enclose_active': tech.TECH.cont_enc_active,
        'cont_min_enclose_metal': tech.TECH.cont_enc_metal,
        # TODO: add in the original tech struct
        'active_min_enclose_np': 0.14,
        'active_min_enclose_pp': 0.14,
        'np_min_enclose_nw': 0.14,
    }

    min_width = gr_drc['cont_min_size'] + \
        2*max(gr_drc['cont_min_enclose_active'], gr_drc['cont_min_enclose_metal'])
    min_width = max(min_width, gr_drc['m1_min_width'])
    assert width >= min_width, \
        f"Guard Ring width >= {min_width} to comply with Min cont enclosure and metal width"

    # define nrows and ncols of the required tap
    nrows = int(floor(width / min_width))
    c = Component()
    
    # define the path 
    if bbox is not None:
        
        path = [
            (bbox[0][0] - guardRingSpacing - width/2, bbox[1][1] + guardRingSpacing + width/2),
            (bbox[1][0] + guardRingSpacing + width/2, bbox[1][1] + guardRingSpacing + width/2),
            (bbox[1][0] + guardRingSpacing + width/2, bbox[0][1] - guardRingSpacing - width/2),
            (bbox[0][0] - guardRingSpacing - width/2, bbox[0][1] - guardRingSpacing - width/2),
            (bbox[0][0] - guardRingSpacing - width/2, bbox[1][1] + guardRingSpacing + width),
        ]
        enclosure = max(gr_drc['cont_min_enclose_active'], gr_drc['cont_min_enclose_metal'])
        cont_path = [
            (bbox[0][0] - guardRingSpacing - enclosure, bbox[1][1] + guardRingSpacing + enclosure),
            (bbox[1][0] + guardRingSpacing + enclosure, bbox[1][1] + guardRingSpacing + enclosure),
            (bbox[1][0] + guardRingSpacing + enclosure, bbox[0][1] - guardRingSpacing - enclosure),
            (bbox[0][0] - guardRingSpacing - enclosure, bbox[0][1] - guardRingSpacing - enclosure),
            (bbox[0][0] - guardRingSpacing - enclosure, bbox[1][1] + guardRingSpacing ),
        ]

    assert path is not None, "Neither path or bbox was provided."
    # place taps around path
    tap_layers = [layer_activ, layer_metal1]
    main = None
    for layer_spec in tap_layers:
        p = gf.path.extrude(gf.path.Path(path), width = width, layer=layer_spec)
        main = c.add_ref(p)
    if guardRingType == 'psub':
        sep = gr_drc['active_min_enclose_pp']
        last_point = list(path[-1])
        last_edge = (path[-1][0] -path[-2][0], path[-1][1]-path[-2][1])
        norm = np.linalg.norm(last_edge)
        dir_vec = np.array(last_edge) / norm
        # manhattan
        dir_vec[0] = round(dir_vec[0])
        dir_vec[1] = round(dir_vec[1]) 
        last_point[0] += sep*dir_vec[0]
        last_point[1] += sep*dir_vec[1]
        new_path = path.copy()
        new_path[-1] = tuple(last_point)
        p = gf.path.extrude(gf.path.Path(new_path), width = width+2*sep, layer=layer_psd)
        c.add_ref(p)
    if guardRingType == 'nwell':
        sep = gr_drc['active_min_enclose_np']
        last_point = list(path[-1])
        last_edge = (path[-1][0] -path[-2][0], path[-1][1]-path[-2][1])
        norm = np.linalg.norm(last_edge)
        dir_vec = np.array(last_edge) / norm
        # manhattan
        dir_vec[0] = round(dir_vec[0])
        dir_vec[1] = round(dir_vec[1]) 
        last_point[0] += sep*dir_vec[0]
        last_point[1] += sep*dir_vec[1]
        new_path = path.copy()
        new_path[-1] = tuple(last_point)
        p = gf.path.extrude(gf.path.Path(new_path), width = width+2*sep, layer=layer_nsd)
        
        sep += gr_drc['np_min_enclose_nw']
        last_point = list(path[-1])
        last_point[0] += sep*dir_vec[0]
        last_point[1] += sep*dir_vec[1]
        new_path = path.copy()
        new_path[-1] = tuple(last_point)
        nwl = gf.path.extrude(gf.path.Path(new_path), width = width+2*sep, layer=layer_nwell)
        c.add_ref(p)
        c.add_ref(nwl)

    cont_tap = cells.via_array(
        via_type = layer_cont.split('drawing')[0],
        via_size = gr_drc['cont_min_size'],
        via_spacing = gr_drc['cont_min_size'] + gr_drc['cont_min_spacing'],
        via_enclosure = gr_drc['cont_min_enclose_active'],
        columns = 1,
        rows = nrows
    )

    conts = gf.path.along_path(
        gf.path.Path(cont_path if bbox is not None else path), 
        cont_tap, gr_drc['cont_min_spacing'] + gr_drc['cont_min_size'],0.0)
    cont_ref = c.add_ref(conts)
    cont_ref.x = main.x 
    cont_ref.y = main.y
    c.info['model'] = f'{guardRingType}-guard-ring'
    c.info['width'] = width
    c.info['rows'] = nrows
    c.info['guardRingSpacing'] = guardRingSpacing
    
    return c

if __name__ == "__main__":
    from gdsfactory.difftest import xor

    from ihp import PDK
    from ihp.cells import fixed

    PDK.activate()

    # Test the components
    # c0 = cells.svaricap()  # original
    # c1 = svaricap()  # New
    # # c = gf.grid([c0, c1], spacing=100)
    # c = xor(c0, c1)
    # c.show()

    # c0 = cells.esd_nmos()  # original
    # c1 = esd_nmos()  # New
    # c = xor(c0, c1)
    # c.show()

    c0 = fixed.ptap1()  # original
    c1 = ptap1()  # New
    c = xor(c0, c1)
    c.show()

    # c0 = fixed.sealring()  # original
    # c1 = sealring()  # New
    # c = xor(c0, c1)
    # c.show()
