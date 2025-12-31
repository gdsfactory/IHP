"""Inductor components for IHP PDK."""

import math

import gdsfactory as gf
from gdsfactory import Component
from gdsfactory.typings import LayerSpec, LayerSpecs


def snap_to_grid(p, grid: float = 0.005):
    return round(p / grid) * grid


@gf.cell
def inductor2(
    width: float = 2.0,
    space: float = 2.1,
    diameter: float = 25.35,
    vias_width: float = 0.9,
    resistance: float = 0.5777,
    inductance: float = 33.303e-12,
    terminal_1_length: float = 30.0,
    turns: int = 1,
    layer_metal_1: LayerSpec = "TopMetal1drawing",
    layer_metal_2: LayerSpec = "TopMetal2drawing",
    layer_inductor: LayerSpec = "INDdrawing",
    layer_metal_1_pin: LayerSpec = "TopMetal2pin",
    layer_metal_2_pin: LayerSpec = "TopMetal2pin",
    layer_ind_pin: LayerSpec = "INDpin",
    layer_via: LayerSpec = "TopVia2drawing",
    layers_no_fill: LayerSpecs = (
        "Activnofill",
        "GatPolynofill",
        "Metal1nofill",
        "Metal2nofill",
        "Metal3nofill",
        "Metal4nofill",
        "Metal5nofill",
        "TopMetal1nofill",
        "TopMetal2nofill",
        "PWellblock",
        "NoRCXdrawing",
    ),
) -> Component:
    """Create a 2-turn inductor.

    Args:
        width: Width of the inductor trace in micrometers.
        space: Space between turns in micrometers.
        diameter: Inner diameter in micrometers.
        vias_width: Width of vias in micrometers (only when turns > 2)
        resistance: Resistance in ohms.
        inductance: Inductance in henries.
        terminal_1_length: Length of the shorter terminal
        turns: Number of turns (default 1 for inductor2).

    Returns:
        Component with inductor layout.
    """
    if not isinstance(turns, int) or turns < 1:
        raise ValueError("turns must be an integer >= 1")

    c = Component()

    Pin_layers_1 = [layer_metal_1_pin, layer_ind_pin]
    Pin_layers_2 = [layer_metal_2_pin, layer_ind_pin]

    w = snap_to_grid(width, grid=0.005 * 2)
    s = snap_to_grid(space)
    d = snap_to_grid(diameter, grid=0.005 * 2)

    apothem_innermost = d / 2
    vertex_angle = math.pi / 4.0  # 45°
    half_vertex_angle = vertex_angle / 2  # 22.5°

    length_short_terminal = terminal_1_length
    length_long_terminal = length_short_terminal + w + (w + s) * (turns - 1)

    octagon_center_offset_y = length_long_terminal + apothem_innermost

    # Add inductor layer
    outer_polygon_pts = []
    for i in range(8):
        r_outer = octagon_center_offset_y / math.cos(half_vertex_angle)
        angle = i * vertex_angle + half_vertex_angle

        x = snap_to_grid(r_outer * math.cos(angle))
        y = snap_to_grid(r_outer * math.sin(angle) + octagon_center_offset_y)
        outer_polygon_pts.append((x, y))
    c.add_polygon(points=outer_polygon_pts, layer=layer_inductor)

    # Add No fill layers
    for layer in layers_no_fill:
        c.add_polygon(points=outer_polygon_pts, layer=layer)

    # Handle the terminals and pins of the inductor
    if turns == 1:
        port1_single_turn = c << gf.components.rectangle(
            size=(w, length_short_terminal + w), layer=layer_metal_2
        )
        port1_single_turn.move((-w - s / 2, 0))
        c.add_port(
            name="P1",
            center=(-w / 2 - s / 2, 0),
            width=w,
            orientation=270,
            layer=layer_metal_2,
        )

        for layer in Pin_layers_2:
            pin_1_trace = c << gf.components.rectangle(size=(w, w), layer=layer)
            pin_1_trace.move((-w - s / 2, 0))

        port2_single_turn = c << gf.components.rectangle(
            size=(w, length_short_terminal + w), layer=layer_metal_2
        )
        port2_single_turn.move((s / 2, 0))
        c.add_port(
            name="P2",
            center=(w / 2 + s / 2, 0),
            width=w,
            orientation=270,
            layer=layer_metal_2,
        )

        for layer in Pin_layers_2:
            pin_2_trace = c << gf.components.rectangle(size=(w, w), layer=layer)
            pin_2_trace.move((s / 2, 0))
    else:
        port_short = c << gf.components.rectangle(
            size=(w, length_short_terminal), layer=layer_metal_2
        )
        port_short.move((-w / 2, 0))
        c.add_port(
            name="P1", center=(0, 0), width=w, orientation=270, layer=layer_metal_2
        )

        for layer in Pin_layers_2:
            pin_short_trace = c << gf.components.rectangle(size=(w, w), layer=layer)
            pin_short_trace.move((-w / 2, 0))

        port_long_1 = c << gf.components.rectangle(
            size=(w, length_long_terminal), layer=layer_metal_1
        )
        port_long_1.move((-(w + s) - w / 2, 0))
        c.add_port(
            name="P2",
            center=(-(w + s), 0),
            width=w,
            orientation=270,
            layer=layer_metal_1,
        )

        for layer in Pin_layers_1:
            pin_long1_trace = c << gf.components.rectangle(size=(w, w), layer=layer)
            pin_long1_trace.move((-(w + s) - w / 2, 0))

        port_long_2 = c << gf.components.rectangle(
            size=(w, length_long_terminal), layer=layer_metal_1
        )
        port_long_2.move(((w + s) - w / 2, 0))
        c.add_port(
            name="P3", center=(w + s, 0), width=w, orientation=270, layer=layer_metal_1
        )

        for layer in Pin_layers_1:
            pin_long1_trace = c << gf.components.rectangle(size=(w, w), layer=layer)
            pin_long1_trace.move((w + s - w / 2, 0))

    # We break down the body of inductor into 3 sections
    for k in range(turns):
        apothem = (apothem_innermost + w / 2) + (w + s) * k
        half_octagon_side = apothem * math.tan(half_vertex_angle)

        # Step 1a: We handle the left semi-octagon loops
        x = (-s / 2) if turns == 1 else (-s - w / 2)
        left_octagon_fragment = [
            (x, octagon_center_offset_y + apothem),
            (-half_octagon_side, octagon_center_offset_y + apothem),
            (-apothem, octagon_center_offset_y + half_octagon_side),
            (-apothem, octagon_center_offset_y - half_octagon_side),
            (-half_octagon_side, octagon_center_offset_y - apothem),
            (x, octagon_center_offset_y - apothem),
        ]

        left_path = gf.Path(left_octagon_fragment)
        _ = c << gf.path.extrude(left_path, layer=layer_metal_2, width=w)

        # Step 1b: We handle the right semi-octagon loops
        x = (s / 2) if turns == 1 else (s + w / 2)
        right_octagon_fragment = [
            (x, octagon_center_offset_y + apothem),
            (half_octagon_side, octagon_center_offset_y + apothem),
            (apothem, octagon_center_offset_y + half_octagon_side),
            (apothem, octagon_center_offset_y - half_octagon_side),
            (half_octagon_side, octagon_center_offset_y - apothem),
            (x, octagon_center_offset_y - apothem),
        ]

        right_path = gf.Path(right_octagon_fragment)
        _ = c << gf.path.extrude(right_path, layer=layer_metal_2, width=w)

        # Step 2: We handle the connections of the loops within TM2
        if turns == 1:
            center_fragment = [
                (-w - s / 2, octagon_center_offset_y + apothem),
                (w + s / 2, octagon_center_offset_y + apothem),
            ]
            center_path = gf.Path(center_fragment)
            _ = c << gf.path.extrude(center_path, layer=layer_metal_2, width=w)
        else:
            if k == 0:
                continue

            center_fragment = [
                (-s - w / 2, octagon_center_offset_y - apothem),
                (s + w / 2, octagon_center_offset_y - apothem),
            ]
            center_path = gf.Path(center_fragment)
            c << gf.path.extrude(center_path, layer=layer_metal_2, width=w)

            connecting_fragment_TM2 = [
                (-s - w / 2, octagon_center_offset_y + apothem - w - s),
                (-w, octagon_center_offset_y + apothem - w - s),
                (w, octagon_center_offset_y + apothem),
                (s + w / 2, octagon_center_offset_y + apothem),
            ]

            connecting_path_TM2 = gf.Path(connecting_fragment_TM2)
            c << gf.path.extrude(connecting_path_TM2, layer=layer_metal_2, width=w)

    # Step 3: We handle the cross connection of the loops using TM1 and vias
    if turns > 1:
        connecting_fragment_TM1 = [
            (-s - w / 2 - w, octagon_center_offset_y + apothem),
            (-w, octagon_center_offset_y + apothem),
            (w, octagon_center_offset_y + apothem - (w + s) * (turns - 1)),
            (s + w / 2 + w, octagon_center_offset_y + apothem - (w + s) * (turns - 1)),
        ]
        connecting_path_TM1 = gf.Path(connecting_fragment_TM1)
        c << gf.path.extrude(connecting_path_TM1, layer=layer_metal_1, width=w)

        offset_x = w / 2 - vias_width / 2
        offset_y = vias_width / 2

        via_1_trace = c << gf.components.rectangle(
            size=(vias_width, vias_width), layer=layer_via
        )
        via_1_trace.move(
            (-s - w / 2 - w + offset_x, octagon_center_offset_y + apothem - offset_y)
        )

        via_2_trace = c << gf.components.rectangle(
            size=(vias_width, vias_width), layer=layer_via
        )
        via_2_trace.move(
            (
                s + w / 2 + offset_x,
                octagon_center_offset_y + apothem - (w + s) * (turns - 1) - offset_y,
            )
        )

        via_3_trace = c << gf.components.rectangle(
            size=(vias_width, vias_width), layer=layer_via
        )
        via_3_trace.move(
            (
                -s - w / 2 - w + offset_x,
                octagon_center_offset_y - apothem + (w + s) * (turns - 1) - offset_y,
            )
        )

        via_4_trace = c << gf.components.rectangle(
            size=(vias_width, vias_width), layer=layer_via
        )
        via_4_trace.move(
            (
                s + w / 2 + offset_x,
                octagon_center_offset_y - apothem + (w + s) * (turns - 1) - offset_y,
            )
        )

    # Add metadata
    c.info["resistance"] = resistance
    c.info["inductance"] = inductance
    c.info["model"] = "inductor2"
    c.info["turns"] = turns
    c.info["width"] = width
    c.info["space"] = space
    c.info["diameter"] = diameter

    return c


@gf.cell
def inductor3(
    width: float = 2.0,
    space: float = 2.1,
    diameter: float = 25.84,
    vias_width: float = 0.9,
    resistance: float = 1.386,
    inductance: float = 221.5e-12,
    terminal_1_length: float = 30.0,
    turns: int = 2,
    layer_metal_1: LayerSpec = "TopMetal1drawing",
    layer_metal_2: LayerSpec = "TopMetal2drawing",
    layer_inductor: LayerSpec = "INDdrawing",
    layer_metal_1_pin: LayerSpec = "TopMetal2pin",
    layer_metal_2_pin: LayerSpec = "TopMetal2pin",
    layer_ind_pin: LayerSpec = "INDpin",
    layer_via: LayerSpec = "TopVia2drawing",
    layers_no_fill: LayerSpecs = (
        "Activnofill",
        "GatPolynofill",
        "Metal1nofill",
        "Metal2nofill",
        "Metal3nofill",
        "Metal4nofill",
        "Metal5nofill",
        "TopMetal1nofill",
        "TopMetal2nofill",
        "PWellblock",
        "NoRCXdrawing",
    ),
) -> Component:
    """Create a 3-turn inductor.

    Args:
        width: Width of the inductor trace in micrometers.
        space: Space between turns in micrometers.
        diameter: Inner diameter in micrometers.
        vias_width: Width of vias in micrometers (only when turns > 2)
        resistance: Resistance in ohms.
        inductance: Inductance in henries.
        terminal_1_length: Length of the shorter terminal
        turns: Number of turns (default 2 for inductor3).

    Returns:
        Component with inductor layout.
    """
    # Use inductor2 as base with different default parameters
    return inductor2(
        width=width,
        space=space,
        diameter=diameter,
        vias_width=vias_width,
        resistance=resistance,
        inductance=inductance,
        terminal_1_length=terminal_1_length,
        turns=turns,
        layer_metal_1=layer_metal_1,
        layer_metal_2=layer_metal_2,
        layer_inductor=layer_inductor,
        layer_metal_1_pin=layer_metal_1_pin,
        layer_metal_2_pin=layer_metal_2_pin,
        layer_ind_pin=layer_ind_pin,
        layer_via=layer_via,
        layers_no_fill=layers_no_fill,
    )


if __name__ == "__main__":
    from gdsfactory.difftest import xor

    from ihp import PDK
    from ihp.cells import fixed

    PDK.activate()

    # Test the components
    c0 = fixed.inductor3()  # original
    c1 = inductor3()  # New
    c = xor(c0, c1)
    c.show()

    # c0 = fixed.inductor2()  # original
    # c1 = inductor2()  # New
    # c = xor(c0, c1)
    # c.show()

    # c = inductor2(turns=100)
    # c.show()
