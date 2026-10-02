"""Via stack components for IHP PDK."""

import gdsfactory as gf
from gdsfactory import Component
from gdsfactory.typings import LayerSpec

# Via design rules (in micrometers)
VIA_RULES = {
    "Cont": {
        "size": 0.16,
        "spacing": 0.18,
        "enclosure": 0.06,
    },
    "Via1": {
        "size": 0.26,
        "spacing": 0.36,
        "enclosure": 0.06,
    },
    "Via2": {
        "size": 0.26,
        "spacing": 0.36,
        "enclosure": 0.06,
    },
    "Via3": {
        "size": 0.26,
        "spacing": 0.36,
        "enclosure": 0.06,
    },
    "Via4": {
        "size": 0.26,
        "spacing": 0.36,
        "enclosure": 0.06,
    },
    "Vmim": {
        "size": 0.42,
        "spacing": 0.47,
        "enclosure": 0.42,
    },
    "TopVia1": {
        "size": 0.42,
        "spacing": 0.42,
        "enclosure": 0.3,
    },
    "TopVia2": {
        "size": 0.9,
        "spacing": 1.06,
        "enclosure": 0.5,
    },
}


def get_via_name(bottom_metal: str, top_metal: str) -> str | None:
    """Get the via layer name between two metal layers.

    Args:
        bottom_metal: Bottom metal layer name.
        top_metal: Top metal layer name.

    Returns:
        Via layer name or None if not adjacent.
    """
    via_mapping = {
        ("Activ", "Metal1"): "Cont",
        ("GatPoly", "Metal1"): "Cont",
        ("Metal1", "Metal2"): "Via1",
        ("Metal2", "Metal3"): "Via2",
        ("Metal3", "Metal4"): "Via3",
        ("Metal4", "Metal5"): "Via4",
        ("MIM", "TopMetal1"): "Vmim",
        ("Metal5", "TopMetal1"): "TopVia1",
        ("TopMetal1", "TopMetal2"): "TopVia2",
    }

    if (bottom_metal, top_metal) in via_mapping:
        return via_mapping[(bottom_metal, top_metal)]
    return None


@gf.cell(tags=["IHP", "via", "array"])
def via_array(
    via_type: str = "Via1",
    columns: int = 2,
    rows: int = 2,
    via_size: float | None = None,
    via_spacing: float | None = None,
    via_enclosure: float | None = None,
    layer_cont: LayerSpec = "Contdrawing",
    layer_via1: LayerSpec = "Via1drawing",
    layer_via2: LayerSpec = "Via2drawing",
    layer_via3: LayerSpec = "Via3drawing",
    layer_via4: LayerSpec = "Via4drawing",
    layer_vmim: LayerSpec = "Vmimdrawing",
    layer_topvia1: LayerSpec = "TopVia1drawing",
    layer_topvia2: LayerSpec = "TopVia2drawing",
) -> Component:
    """Create an array of vias.

    Args:
        via_type: Type of via (Via1, Via2, Via3, Via4, TopVia1, TopVia2).
        columns: Number of via columns.
        rows: Number of via rows.
        via_size: Via size in micrometers (uses default if None).
        via_spacing: Via spacing in micrometers (uses default if None).
        via_enclosure: Metal enclosure in micrometers (uses default if None).
        layer_via1: Via1 layer.
        layer_via2: Via2 layer.
        layer_via3: Via3 layer.
        layer_via4: Via4 layer.
        layer_topvia1: TopVia1 layer.
        layer_topvia2: TopVia2 layer.

    Returns:
        Component with via array.
    """
    c = Component()

    # Map via type to layer parameter
    via_layer_map = {
        "Cont": layer_cont,
        "Via1": layer_via1,
        "Via2": layer_via2,
        "Via3": layer_via3,
        "Via4": layer_via4,
        "Vmim": layer_vmim,
        "TopVia1": layer_topvia1,
        "TopVia2": layer_topvia2,
    }

    # Get via parameters
    if via_type not in via_layer_map:
        raise ValueError(f"Unknown via type: {via_type}")

    via_layer = via_layer_map[via_type]
    rules = VIA_RULES[via_type]

    # Use provided values or defaults
    size = via_size if via_size is not None else rules["size"]
    spacing = via_spacing if via_spacing is not None else rules["spacing"]
    enclosure = via_enclosure if via_enclosure is not None else rules["enclosure"]

    # Create via array
    for col in range(columns):
        for row in range(rows):
            x = col * spacing
            y = row * spacing

            via = gf.components.rectangle(
                size=(size, size),
                layer=via_layer,
            )
            via_ref = c.add_ref(via)
            via_ref.move((x, y))

    # Calculate total dimensions
    array_width = size if columns == 1 else (columns - 1) * spacing + size
    array_height = size if rows == 1 else (rows - 1) * spacing + size

    # Add metadata
    c.info["via_type"] = via_type
    c.info["columns"] = columns
    c.info["rows"] = rows
    c.info["array_width"] = array_width
    c.info["array_height"] = array_height
    c.info["enclosure_width"] = array_width + 2 * enclosure
    c.info["enclosure_height"] = array_height + 2 * enclosure

    return c


@gf.cell(tags=["IHP", "via", "stack"])
def via_stack(
    size: tuple[float, float] = (10.0, 10.0),
    layers: tuple[str, ...] | None = None,
    layer_offsets: tuple[float, ...] | None = None,
    vias: tuple[str | None, ...] | None = None,
    layer_to_port_orientations: dict[str, list[int]] | None = None,
    correct_size: bool = False,
    slot_horizontal: bool = False,
    slot_vertical: bool = False,
    port_orientations: tuple[int, ...] | None = (180, 90, 0, -90),
    *,
    bottom_layer: str = "Metal1",
    top_layer: str = "Metal2",
    vn_columns: int = 2,
    vn_rows: int = 2,
    vt1_columns: int = 1,
    vt1_rows: int = 1,
    vt2_columns: int = 1,
    vt2_rows: int = 1,
    layer_activ: LayerSpec = "Activdrawing",
    layer_gatpoly: LayerSpec = "GatPolydrawing",
    layer_metal1: LayerSpec = "Metal1drawing",
    layer_metal2: LayerSpec = "Metal2drawing",
    layer_metal3: LayerSpec = "Metal3drawing",
    layer_metal4: LayerSpec = "Metal4drawing",
    layer_metal5: LayerSpec = "Metal5drawing",
    layer_topmetal1: LayerSpec = "TopMetal1drawing",
    layer_topmetal2: LayerSpec = "TopMetal2drawing",
    layer_activ_pin: LayerSpec = "Activpin",
    layer_gatpoly_pin: LayerSpec = "GatPolypin",
    layer_metal1_pin: LayerSpec = "Metal1pin",
    layer_metal2_pin: LayerSpec = "Metal2pin",
    layer_metal3_pin: LayerSpec = "Metal3pin",
    layer_metal4_pin: LayerSpec = "Metal4pin",
    layer_metal5_pin: LayerSpec = "Metal5pin",
    layer_topmetal1_pin: LayerSpec = "TopMetal1pin",
    layer_topmetal2_pin: LayerSpec = "TopMetal2pin",
    layer_cont: LayerSpec = "Contdrawing",
    layer_via1: LayerSpec = "Via1drawing",
    layer_via2: LayerSpec = "Via2drawing",
    layer_via3: LayerSpec = "Via3drawing",
    layer_via4: LayerSpec = "Via4drawing",
    layer_topvia1: LayerSpec = "TopVia1drawing",
    layer_topvia2: LayerSpec = "TopVia2drawing",
) -> Component:
    """Create a via stack connecting multiple metal layers.

    Primary arguments (size, layers, layer_offsets, vias,
    layer_to_port_orientations, correct_size, slot_horizontal,
    slot_vertical, port_orientations) match the shape of
    gdsfactory.components.vias.via_stack. IHP's own bottom_layer/top_layer/
    vn_*/vt*_* convenience arguments come after as keyword-only extras and
    are the recommended way to call this function, since IHP's via
    geometry is fully determined by foundry design rules (see VIA_RULES)
    rather than by an explicit list of via components.

    bottom_layer can be Activ, GatPoly, or any metal (Metal1-TopMetal2).
    Activ and GatPoly connect to Metal1 through Cont; they are independent
    paths and must not appear together in the same stack.

    Args:
        size: Size of the metal stack (width, height) in micrometers.
        layers: Optional gdsfactory-style layer list. Only the first and
            last entries are used (as bottom_layer/top_layer) -- IHP
            derives every intermediate layer and via automatically from
            VIA_RULES, unlike the generic via_stack which requires every
            layer to be listed explicitly.
        layer_offsets: Not supported. Raises NotImplementedError if set.
        vias: Not supported -- IHP infers the via type from each pair of
            adjacent layers. Raises NotImplementedError if set.
        layer_to_port_orientations: Not supported. Raises
            NotImplementedError if set.
        correct_size: Not supported -- IHP does not auto-grow `size` to
            fit a via. Raises NotImplementedError if True.
        slot_horizontal: Not supported. Raises NotImplementedError if True.
        slot_vertical: Not supported. Raises NotImplementedError if True.
        port_orientations: Ignored by IHP's port scheme (always emits
            N/S/E/W ports on bottom_layer and top_layer); kept for
            signature compatibility only.
        bottom_layer: Bottom layer name (Activ, GatPoly, or Metal1-TopMetal2).
        top_layer: Top metal layer name (Metal1-TopMetal2).
        vn_columns: Number of columns for normal vias (Cont, Via1-Via4).
        vn_rows: Number of rows for normal vias.
        vt1_columns: Number of columns for TopVia1.
        vt1_rows: Number of rows for TopVia1.
        vt2_columns: Number of columns for TopVia2.
        vt2_rows: Number of rows for TopVia2.

    Returns:
        Component with via stack.
    """
    if layers is not None:
        if len(layers) < 2:
            raise ValueError(f"layers must contain at least 2 entries, got {layers!r}")
        if bottom_layer != "Metal1" or top_layer != "Metal2":
            raise ValueError(
                "Cannot specify both 'layers' and non-default 'bottom_layer'/'top_layer'."
            )
        bottom_layer = layers[0]
        top_layer = layers[-1]

    _unsupported = {
        "layer_offsets": layer_offsets,
        "vias": vias,
        "layer_to_port_orientations": layer_to_port_orientations,
        "correct_size": correct_size,
        "slot_horizontal": slot_horizontal,
        "slot_vertical": slot_vertical,
    }
    for name, value in _unsupported.items():
        default = False if isinstance(value, bool) else None
        if value != default:
            raise NotImplementedError(
                f"{name}={value!r} is not supported by IHP's via_stack: via "
                "geometry is fully determined by foundry design rules "
                "(VIA_RULES). Use vn_columns/vn_rows/vt1_*/vt2_* instead."
            )

    if port_orientations is not None and tuple(port_orientations) != (180, 90, 0, -90):
        raise NotImplementedError(
            f"port_orientations={port_orientations!r} is not supported by IHP's via_stack. "
            "Only the default (180, 90, 0, -90) is supported."
        )

    c = Component()

    # BEOL metal stack (Metal1 and above)
    _beol_order = [
        "Metal1",
        "Metal2",
        "Metal3",
        "Metal4",
        "Metal5",
        "TopMetal1",
        "TopMetal2",
    ]

    # Sub-Metal1 layers that connect to Metal1 via Cont
    _sub_metal1 = {"Activ", "GatPoly"}

    # Map layer names to layer parameters
    layer_map = {
        "Activ": layer_activ,
        "GatPoly": layer_gatpoly,
        "Metal1": layer_metal1,
        "Metal2": layer_metal2,
        "Metal3": layer_metal3,
        "Metal4": layer_metal4,
        "Metal5": layer_metal5,
        "TopMetal1": layer_topmetal1,
        "TopMetal2": layer_topmetal2,
    }

    pin_layer_map = {
        "Activ": layer_activ_pin,
        "GatPoly": layer_gatpoly_pin,
        "Metal1": layer_metal1_pin,
        "Metal2": layer_metal2_pin,
        "Metal3": layer_metal3_pin,
        "Metal4": layer_metal4_pin,
        "Metal5": layer_metal5_pin,
        "TopMetal1": layer_topmetal1_pin,
        "TopMetal2": layer_topmetal2_pin,
    }

    # Normalize layer names (case-insensitive match against known names)
    _all_names = {n.lower(): n for n in _beol_order + list(_sub_metal1)}
    bottom_port_label = bottom_layer
    top_port_label = top_layer
    bottom_layer = _all_names.get(bottom_layer.lower(), bottom_layer)
    top_layer = _all_names.get(top_layer.lower(), top_layer)

    # Build effective layer order based on bottom_layer
    if bottom_layer in _sub_metal1:
        # Activ or GatPoly -> Cont -> Metal1 -> ... -> top_layer
        if top_layer in _sub_metal1:
            raise ValueError(
                f"Cannot stack between two sub-Metal1 layers: "
                f"{bottom_layer} -> {top_layer}"
            )
        if top_layer not in _beol_order:
            raise ValueError(f"Invalid top layer: {top_layer}")
        top_idx = _beol_order.index(top_layer)
        layer_order = [bottom_layer] + _beol_order[: top_idx + 1]
    else:
        if bottom_layer not in _beol_order:
            raise ValueError(f"Invalid bottom layer: {bottom_layer}")
        if top_layer not in _beol_order:
            raise ValueError(f"Invalid top layer: {top_layer}")
        bottom_idx = _beol_order.index(bottom_layer)
        top_idx = _beol_order.index(top_layer)
        if bottom_idx > top_idx:
            raise ValueError(
                f"Bottom layer must be below top layer: {bottom_layer} -> {top_layer}"
            )
        layer_order = _beol_order[bottom_idx : top_idx + 1]

    width, height = size

    # Add conductor layers
    for name in layer_order:
        metal = gf.components.rectangle(
            size=(width, height),
            layer=layer_map[name],
            centered=True,
        )
        c.add_ref(metal)

    # Add vias between adjacent layers
    for i in range(len(layer_order) - 1):
        bot = layer_order[i]
        top = layer_order[i + 1]
        via_name = get_via_name(bot, top)

        if via_name is None:
            continue

        rules = VIA_RULES[via_name]
        via_size = rules["size"]
        via_spacing = rules["spacing"]
        via_enclosure = rules["enclosure"]

        # Determine number of vias based on type
        if via_name == "TopVia1":
            columns = vt1_columns
            rows = vt1_rows
        elif via_name == "TopVia2":
            columns = vt2_columns
            rows = vt2_rows
        else:
            columns = vn_columns
            rows = vn_rows

        # Calculate maximum number of vias that fit
        max_columns = int((width - 2 * via_enclosure - via_size) / via_spacing) + 1
        max_rows = int((height - 2 * via_enclosure - via_size) / via_spacing) + 1

        # Use minimum of requested and maximum
        actual_columns = min(columns, max_columns)
        actual_rows = min(rows, max_rows)

        if actual_columns > 0 and actual_rows > 0:
            via_array_comp = via_array(
                via_type=via_name,
                columns=actual_columns,
                rows=actual_rows,
                via_size=via_size,
                via_spacing=via_spacing,
                via_enclosure=via_enclosure,
                layer_cont=layer_cont,
                layer_via1=layer_via1,
                layer_via2=layer_via2,
                layer_via3=layer_via3,
                layer_via4=layer_via4,
                layer_topvia1=layer_topvia1,
                layer_topvia2=layer_topvia2,
            )

            # Center the via array
            array_width = via_array_comp.info["array_width"]
            array_height = via_array_comp.info["array_height"]

            via_ref = c.add_ref(via_array_comp)
            via_ref.move((-array_width / 2, -array_height / 2))

    # Add directional ports per layer (N/S/E/W at bbox edges)
    hx = width / 2
    hy = height / 2
    _port_specs = {
        "N": ((0, hy), 90, width),
        "S": ((0, -hy), 270, width),
        "E": ((hx, 0), 0, height),
        "W": ((-hx, 0), 180, height),
    }
    _port_layers = [(bottom_layer, bottom_port_label)]
    if top_layer != bottom_layer or top_port_label != bottom_port_label:
        _port_layers.append((top_layer, top_port_label))
    for layer_name, port_label in _port_layers:
        pin_layer = pin_layer_map[layer_name]
        for direction, (center, orientation, port_width) in _port_specs.items():
            c.add_port(
                name=f"{port_label}_{direction}",
                center=center,
                width=port_width,
                orientation=orientation,
                layer=pin_layer,
                port_type="electrical",
            )

    # Add metadata
    c.info["bottom_layer"] = bottom_layer
    c.info["top_layer"] = top_layer
    c.info["width"] = width
    c.info["height"] = height
    c.info["n_layers"] = len(layer_order)

    return c


@gf.cell(tags=["IHP", "via", "stack"])
def via_stack_with_pads(
    bottom_layer: str = "Metal1",
    top_layer: str = "TopMetal2",
    size: tuple[float, float] = (10.0, 10.0),
    pad_size: tuple[float, float] = (20.0, 20.0),
    pad_spacing: float = 50.0,
    layer_activ: LayerSpec = "Activdrawing",
    layer_gatpoly: LayerSpec = "GatPolydrawing",
    layer_metal1: LayerSpec = "Metal1drawing",
    layer_metal2: LayerSpec = "Metal2drawing",
    layer_metal3: LayerSpec = "Metal3drawing",
    layer_metal4: LayerSpec = "Metal4drawing",
    layer_metal5: LayerSpec = "Metal5drawing",
    layer_topmetal1: LayerSpec = "TopMetal1drawing",
    layer_topmetal2: LayerSpec = "TopMetal2drawing",
    layer_activ_pin: LayerSpec = "Activpin",
    layer_gatpoly_pin: LayerSpec = "GatPolypin",
    layer_metal1_pin: LayerSpec = "Metal1pin",
    layer_metal2_pin: LayerSpec = "Metal2pin",
    layer_metal3_pin: LayerSpec = "Metal3pin",
    layer_metal4_pin: LayerSpec = "Metal4pin",
    layer_metal5_pin: LayerSpec = "Metal5pin",
    layer_topmetal1_pin: LayerSpec = "TopMetal1pin",
    layer_topmetal2_pin: LayerSpec = "TopMetal2pin",
    layer_cont: LayerSpec = "Contdrawing",
    layer_via1: LayerSpec = "Via1drawing",
    layer_via2: LayerSpec = "Via2drawing",
    layer_via3: LayerSpec = "Via3drawing",
    layer_via4: LayerSpec = "Via4drawing",
    layer_topvia1: LayerSpec = "TopVia1drawing",
    layer_topvia2: LayerSpec = "TopVia2drawing",
) -> Component:
    """Create a via stack with test pads.

    Args:
        bottom_layer: Bottom layer name (Activ, GatPoly, or Metal1-TopMetal2).
        top_layer: Top metal layer name (Metal1-TopMetal2).
        size: Size of the via stack (width, height) in micrometers.
        pad_size: Size of the test pads (width, height) in micrometers.
        pad_spacing: Spacing between pads in micrometers.

    Returns:
        Component with via stack and test pads.
    """
    c = Component()

    # Map layer names to layer parameters
    layer_map = {
        "Activ": layer_activ,
        "GatPoly": layer_gatpoly,
        "Metal1": layer_metal1,
        "Metal2": layer_metal2,
        "Metal3": layer_metal3,
        "Metal4": layer_metal4,
        "Metal5": layer_metal5,
        "TopMetal1": layer_topmetal1,
        "TopMetal2": layer_topmetal2,
    }

    pin_layer_map = {
        "Activ": layer_activ_pin,
        "GatPoly": layer_gatpoly_pin,
        "Metal1": layer_metal1_pin,
        "Metal2": layer_metal2_pin,
        "Metal3": layer_metal3_pin,
        "Metal4": layer_metal4_pin,
        "Metal5": layer_metal5_pin,
        "TopMetal1": layer_topmetal1_pin,
        "TopMetal2": layer_topmetal2_pin,
    }

    # Create via stack
    stack = via_stack(
        bottom_layer=bottom_layer,
        top_layer=top_layer,
        size=size,
        layer_activ=layer_activ,
        layer_gatpoly=layer_gatpoly,
        layer_metal1=layer_metal1,
        layer_metal2=layer_metal2,
        layer_metal3=layer_metal3,
        layer_metal4=layer_metal4,
        layer_metal5=layer_metal5,
        layer_topmetal1=layer_topmetal1,
        layer_topmetal2=layer_topmetal2,
        layer_activ_pin=layer_activ_pin,
        layer_gatpoly_pin=layer_gatpoly_pin,
        layer_metal1_pin=layer_metal1_pin,
        layer_metal2_pin=layer_metal2_pin,
        layer_metal3_pin=layer_metal3_pin,
        layer_metal4_pin=layer_metal4_pin,
        layer_metal5_pin=layer_metal5_pin,
        layer_topmetal1_pin=layer_topmetal1_pin,
        layer_topmetal2_pin=layer_topmetal2_pin,
        layer_cont=layer_cont,
        layer_via1=layer_via1,
        layer_via2=layer_via2,
        layer_via3=layer_via3,
        layer_via4=layer_via4,
        layer_topvia1=layer_topvia1,
        layer_topvia2=layer_topvia2,
    )
    c.add_ref(stack)

    # Add bottom pad
    bottom_pad = gf.components.rectangle(
        size=pad_size,
        layer=layer_map[bottom_layer],
        centered=True,
    )
    bottom_pad_ref = c.add_ref(bottom_pad)
    bottom_pad_ref.movex(-pad_spacing / 2)

    # Add top pad
    top_pad = gf.components.rectangle(
        size=pad_size,
        layer=layer_map[top_layer],
        centered=True,
    )
    top_pad_ref = c.add_ref(top_pad)
    top_pad_ref.movex(pad_spacing / 2)

    # Connect pads to stack
    bottom_trace = gf.components.rectangle(
        size=(pad_spacing / 2 - size[0] / 2, 2.0),
        layer=layer_map[bottom_layer],
    )
    bottom_trace_ref = c.add_ref(bottom_trace)
    bottom_trace_ref.move((-pad_spacing / 2, -1.0))

    top_trace = gf.components.rectangle(
        size=(pad_spacing / 2 - size[0] / 2, 2.0),
        layer=layer_map[top_layer],
    )
    top_trace_ref = c.add_ref(top_trace)
    top_trace_ref.move((size[0] / 2, -1.0))

    # Add ports
    c.add_port(
        name="pad1",
        center=(-pad_spacing / 2, 0),
        width=pad_size[1],
        orientation=180,
        layer=pin_layer_map[bottom_layer],
        port_type="electrical",
    )

    c.add_port(
        name="pad2",
        center=(pad_spacing / 2, 0),
        width=pad_size[1],
        orientation=0,
        layer=pin_layer_map[top_layer],
        port_type="electrical",
    )

    return c
