"""Primitives."""

from math import exp, isfinite, log, sqrt

import gdsfactory as gf
from gdsfactory.cross_section import port_names_electrical, port_types_electrical
from gdsfactory.typings import CrossSectionSpec, LayerSpec, Size

from .. import tech


def _get_stack_geometry(
    signal_cross_section: CrossSectionSpec,
    ground_cross_section: CrossSectionSpec,
) -> tuple[float, float]:
    """Extract stack height and signal layer thickness from the active PDK.

    Args:
        signal_cross_section: Cross-section spec for the signal layer.
        ground_cross_section: Cross-section spec for the ground layer.

    Returns:
        Tuple of (stack_height, signal_layer_thickness) in um.
    """
    layers = gf.get_active_pdk().get_layer_stack().layers

    keys = list(layers.keys())
    start = keys.index(ground_cross_section.split("_")[0])
    end = keys.index(signal_cross_section.split("_")[0])

    if start < end:
        stack_height = 0
        for k in keys[start + 1 : end]:
            stack_height += layers[k].thickness

        signal_layer_thickness = layers[keys[end]].thickness

    else:
        stack_height = 0
        for k in keys[end + 1 : start]:
            stack_height += layers[k].thickness

        signal_layer_thickness = layers[keys[end]].thickness

    return stack_height, signal_layer_thickness


def _calculate_effective_dielectric_constant(
    signal_cross_section: CrossSectionSpec = "topmetal2_routing",
    ground_cross_section: CrossSectionSpec = "topmetal1_routing",
    e_r: float = 4.1,
) -> float:
    """Calculate the effective dielectric constant for a coplanar waveguide.

    Uses a common approximation that depends on the ratio of width to stack height.
    Approximation from https://wellerpcb.com/pcb-layout-design/impedance-calculation-for-embedded-microstrip-trace-type/
    Args:
        e_r: Relative permittivity of the substrate.
        signal_cross_section: Cross-section spec for the signal layer.
        ground_cross_section: Cross-section spec for the ground layer.
    Returns:
        Estimated effective dielectric constant.
    """
    if isinstance(ground_cross_section, list):
        return e_r

    h_p, t = _get_stack_geometry(signal_cross_section, ground_cross_section)

    # calculate distance from signal layer to surface
    signal_layer_name = signal_cross_section.split("_")[0]
    if signal_layer_name == "topmetal2":
        h_above = 1.5  # passivation/overcoat estimate for topmost metal
    else:
        layers = gf.get_active_pdk().get_layer_stack().layers
        keys = list(layers.keys())
        signal_idx = keys.index(signal_layer_name)
        h_above = sum(
            layers[keys[i]].thickness for i in range(signal_idx + 1, len(keys))
        )

    e_eff = e_r * (1 - exp(-1.55 * (h_p + t + h_above) / h_p))

    return e_eff


def _calculate_width_from_Z0(
    Z0: float,
    signal_cross_section: CrossSectionSpec,
    ground_cross_section: CrossSectionSpec | list[CrossSectionSpec],
    e_r: float = 4.1,
) -> float:
    """Calculate the width of a coplanar waveguide given the characteristic impedance Z0.

    Uses an approximate closed-form formula for microstrip transmission lines.
    For a single ground layer, the IPC-2141 embedded microstrip approximation is
    used.  For a stripline configuration (two ground layers), a PCBWay-style
    approximation is applied instead.

    Args:
        Z0: Target characteristic impedance (ohms).
        signal_cross_section: CrossSectionSpec for the signal layer.
        ground_cross_section: CrossSectionSpec for the ground layer.
            Lower layer must be listed first if multiple ground layers
            are provided.
        e_r: Relative permittivity of the substrate. Defaults to 4.1
            for silicon dioxide.

    Returns:
        Calculated width (um).

    Raises:
        ValueError: If the calculated width is negative.
    """
    if isinstance(ground_cross_section, list):
        h_below, t = _get_stack_geometry(signal_cross_section, ground_cross_section[0])
        h_above, t = _get_stack_geometry(signal_cross_section, ground_cross_section[1])
        # approximation from https://www.pcbway.com/pcb_prototype/impedance_calculator.html
        width = (
            1.9
            * (2 * h_above + t)
            * exp(-Z0 * sqrt(e_r) / (80.0 * (1 - h_above / (4 * h_below))))
            - t
        ) / 0.8
    else:
        stack_height, signal_layer_thickness = _get_stack_geometry(
            signal_cross_section, ground_cross_section
        )
        # approximation from https://chemandy.com/calculators/microstrip-transmission-line-calculator-ipc2141.htm

        width = (
            exp(-Z0 * sqrt(e_r + 1.41) / 87.0) * 5.98 * stack_height
            - signal_layer_thickness
        ) / 0.8

    if (not isfinite(width)) or width <= 0:
        # Fallback to a conservative, manufacturable width when the closed-form
        # approximation is out of range for the selected stack and impedance.
        width = 0.2

    width = width - width % (
        2 * tech.nm
    )  # truncate to 2 nm, gdsfactory needs even widths for ports

    return width


def _calculate_Z0_from_width(
    width: float,
    signal_cross_section: CrossSectionSpec,
    ground_cross_section: CrossSectionSpec | list[CrossSectionSpec],
    e_r: float = 4.1,
) -> float:
    """Estimate the characteristic impedance Z0 from a given signal width.

    Computes the vertical stack height between the ground and signal layers
    using the active PDK layer stack, then applies an approximate closed-form
    formula to estimate Z0.  For a single ground layer, the IPC-2141 embedded
    microstrip approximation is used.  For a stripline configuration (two
    ground layers), a PCBWay-style approximation is applied instead.

    Args:
        width: Signal line width (um).
        signal_cross_section: CrossSectionSpec for the signal layer.
        ground_cross_section: CrossSectionSpec for the ground layer.
            Lower layer must be listed first if multiple ground layers
            are provided.
        e_r: Relative permittivity of the substrate. Defaults to 4.1
            for silicon dioxide.

    Returns:
        Estimated characteristic impedance Z0 (ohms).

    Raises:
        ValueError: If the calculated Z0 is negative.
    """
    if isinstance(ground_cross_section, list):
        h_below, t = _get_stack_geometry(signal_cross_section, ground_cross_section[0])

        h_above, t = _get_stack_geometry(signal_cross_section, ground_cross_section[1])
        # approximation from https://www.pcbway.com/pcb_prototype/impedance_calculator.html
        Z0 = (
            80
            / sqrt(e_r)
            * log(1.9 * (2 * h_above + t) / (0.8 * width + t))
            * (1 - h_above / (4 * h_below))
        )

    else:
        stack_height, signal_layer_thickness = _get_stack_geometry(
            signal_cross_section, ground_cross_section
        )

        # https://chemandy.com/calculators/microstrip-transmission-line-calculator-ipc2141.htm
        Z0 = (
            87.0
            / sqrt(e_r + 1.41)
            * log(5.98 * stack_height / (0.8 * width + signal_layer_thickness))
        )

    if Z0 < 0:
        raise ValueError(
            "Calculated Z0 is negative. Check width and cross-section choices."
        )

    return Z0


def _resolve_tline_width_and_Z0(
    width: float | None,
    Z0: float | None,
    signal_cross_section: CrossSectionSpec,
    ground_cross_section: CrossSectionSpec | list[CrossSectionSpec],
) -> tuple[float, float | None]:
    """Resolve width/Z0 inputs for transmission-line helpers.

    Supports three modes:
    - width only: derive Z0 from width.
    - Z0 only: derive width from Z0.
    - neither: use signal cross-section default width and derive Z0.

    Raises:
        ValueError: If both width and Z0 are provided.
    """
    if width is not None and Z0 is not None:
        raise ValueError("Provide only one of width or Z0")

    if width is None:
        if Z0 is None:
            width = gf.get_cross_section(signal_cross_section).width
        else:
            width = _calculate_width_from_Z0(
                Z0=Z0,
                ground_cross_section=ground_cross_section,
                signal_cross_section=signal_cross_section,
            )

    if Z0 is None:
        Z0 = _calculate_Z0_from_width(
            width=width,
            ground_cross_section=ground_cross_section,
            signal_cross_section=signal_cross_section,
        )

    return width, Z0


@gf.cell(tags=["IHP", "waveguide", "straight"])
def straight(
    length: float = 10,
    cross_section: CrossSectionSpec = "strip",
    width: float | None = None,
    npoints: int = 2,
) -> gf.Component:
    """Returns a Straight waveguide.

    Args:
        length: straight length (um).
        cross_section: specification (CrossSection, string or dict).
        width: width of the waveguide. If None, it will use the width of the cross_section.
        npoints: number of points.
    """
    return gf.c.straight(
        length=length, cross_section=cross_section, width=width, npoints=npoints
    )


@gf.cell(tags=["IHP", "waveguide", "bend"])
def bend_euler(
    radius: float | None = None,
    angle: float = 90,
    p: float = 0.5,
    width: float | None = None,
    cross_section: CrossSectionSpec = "strip",
    allow_min_radius_violation: bool = False,
) -> gf.Component:
    """Regular degree euler bend.

    Args:
        radius: in um. Defaults to cross_section_radius.
        angle: total angle of the curve.
        p: Proportion of the curve that is an Euler curve.
        width: width to use. Defaults to cross_section.width.
        cross_section: specification (CrossSection, string, CrossSectionFactory dict).
        allow_min_radius_violation: if True allows radius to be smaller than cross_section radius.
    """
    return gf.c.bend_euler(
        radius=radius,
        angle=angle,
        p=p,
        width=width,
        cross_section=cross_section,
        allow_min_radius_violation=allow_min_radius_violation,
        with_arc_floorplan=True,
        npoints=None,
        layer=None,
    )


@gf.cell(tags=["IHP", "waveguide", "bend"])
def bend_s(
    size: Size = (11, 1.8),
    cross_section: CrossSectionSpec = "strip",
    width: float | None = None,
    allow_min_radius_violation: bool = False,
) -> gf.Component:
    """Return S bend with bezier curve.

    stores min_bend_radius property in self.info['min_bend_radius']
    min_bend_radius depends on height and length

    Args:
        size: in x and y direction.
        cross_section: spec.
        width: width of the waveguide. If None, it will use the width of the cross_section.
        allow_min_radius_violation: allows min radius violations.
    """
    return gf.c.bend_s(
        size=size,
        cross_section=cross_section,
        npoints=99,
        allow_min_radius_violation=allow_min_radius_violation,
        width=width,
    )


@gf.cell(tags=["IHP", "wire", "corner"])
def wire_corner(
    cross_section: CrossSectionSpec = "metal_routing", width: float | None = None
) -> gf.Component:
    """Returns 45 degrees electrical corner wire.

    Args:
        cross_section: spec.
        width: optional width. Defaults to cross_section width.
    """
    return gf.c.wire_corner(
        cross_section=cross_section,
        width=width,
        port_names=port_names_electrical,
        port_types=port_types_electrical,
        radius=None,
    )


@gf.cell(tags=["IHP", "wire", "corner"])
def wire_corner45(
    cross_section: CrossSectionSpec = "metal_routing",
    radius: float = 10,
    width: float | None = None,
    layer: LayerSpec | None = None,
    with_corner90_ports: bool = True,
) -> gf.Component:
    """Returns 90 degrees electrical corner wire.

    Args:
        cross_section: spec.
        radius: ignored.
        width: optional width. Defaults to cross_section width.
        layer: ignored.
        with_corner90_ports: if True, adds ports at 90 degrees.
    """
    return gf.c.wire_corner45(
        cross_section=cross_section,
        radius=radius,
        width=width,
        layer=layer,
        with_corner90_ports=with_corner90_ports,
    )


####################
# Metal waveguides
####################


@gf.cell(tags=["IHP", "wire", "straight"])
def straight_metal(
    length: float = 10,
    cross_section: CrossSectionSpec = "metal_routing",
    width: float | None = None,
) -> gf.Component:
    """Returns a Straight waveguide.

    Args:
        length: straight length (um).
        cross_section: specification (CrossSection, string or dict).
        width: width of the waveguide. If None, it will use the width of the cross_section.
    """
    return gf.c.straight(
        length=length, cross_section=cross_section, width=width, npoints=2
    )


@gf.cell(tags=["IHP", "wire", "bend"])
def bend_metal(
    radius: float | None = None,
    angle: float = 90,
    width: float | None = None,
    cross_section: CrossSectionSpec = "metal_routing",
) -> gf.Component:
    """Regular degree euler bend.

    Args:
        radius: None.
        angle: 90.
        width: None.
        cross_section: "metal_routing".
    """
    if radius is None:
        if width:
            xs = gf.get_cross_section(cross_section=cross_section, width=width)
        else:
            xs = gf.get_cross_section(cross_section=cross_section)
        radius = xs.radius or xs.width
    return gf.c.bend_circular(
        radius=radius,
        angle=angle,
        width=width,
        cross_section=cross_section,
        allow_min_radius_violation=True,
        npoints=None,
        layer=None,
    )


@gf.cell(tags=["IHP", "wire", "bend"])
def bend_s_metal(
    size: Size = (11, 1.8),
    cross_section: CrossSectionSpec = "metal_routing",
    width: float | None = None,
    allow_min_radius_violation: bool = True,
) -> gf.Component:
    """Return S bend with bezier curve.

    stores min_bend_radius property in self.info['min_bend_radius']
    min_bend_radius depends on height and length

    Args:
        size: in x and y direction.
        cross_section: spec.
        width: width of the waveguide. If None, it will use the width of the cross_section.
        allow_min_radius_violation: allows min radius violations.
    """
    return gf.c.bend_s(
        size=size,
        cross_section=cross_section,
        npoints=99,
        allow_min_radius_violation=allow_min_radius_violation,
        width=width,
    )


# ------------------------------------------------------


@gf.cell
def tline(
    length: float = 10,
    signal_cross_section: CrossSectionSpec = "topmetal2_routing",
    ground_cross_section: CrossSectionSpec
    | list[CrossSectionSpec] = "topmetal1_routing",
    width: float | None = None,
    Z0: float | None = None,
    npoints: int = 2,
) -> gf.Component:
    """Return a straight coplanar transmission line.

    Creates a signal straight and a wider ground straight aligned around it.
    The ground plane extends 3x the signal width beyond each end of the
    signal line and is 7x as wide.  When two ground cross-sections are
    provided the component produces a stripline (ground above and below).

    Args:
        length: Length of the signal line (um).
        signal_cross_section: Cross-section for the signal line.
        ground_cross_section: Cross-section for the ground line.
            Accepts a single spec for microstrip or a two-element list
            ``[lower, upper]`` for stripline.
        width: Signal line width (um). Mutually exclusive with Z0.
        Z0: Target characteristic impedance (ohms). Mutually exclusive
            with width.
        npoints: Number of points used to draw the straights.

    Returns:
        A Component containing signal and ground lines.

    Raises:
        ValueError: If both *width* and *Z0* are provided.
    """
    width, Z0 = _resolve_tline_width_and_Z0(
        width=width,
        Z0=Z0,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
    )

    c = gf.Component()

    signal = c.add_ref(
        gf.c.straight(
            length=length,
            cross_section=signal_cross_section,
            width=width,
            npoints=npoints,
        )
    )
    c.add_ports(signal.ports)

    if isinstance(ground_cross_section, list):
        ground_low = c.add_ref(
            gf.c.straight(
                length=length + 6 * width,
                cross_section=ground_cross_section[0],
                width=7 * width,
                npoints=npoints,
            )
        )
        ground_low.move((-3 * width, 0))
        ground_high = c.add_ref(
            gf.c.straight(
                length=length + 6 * width,
                cross_section=ground_cross_section[1],
                width=7 * width,
                npoints=npoints,
            )
        )
        ground_high.move((-3 * width, 0))
    else:
        ground = c.add_ref(
            gf.c.straight(
                length=length + 6 * width,
                cross_section=ground_cross_section,
                width=7 * width,
                npoints=npoints,
            )
        )
        ground.move((-3 * width, 0))

    return c


@gf.cell
def tline_bend_circular(
    radius: float = 10,
    angle: float = 90,
    signal_cross_section: CrossSectionSpec = "topmetal2_routing",
    ground_cross_section: CrossSectionSpec = "topmetal1_routing",
    width: float | None = None,
    Z0: float | None = None,
) -> gf.Component:
    """Returns a circular bend coplanar transmission line.

    Creates a signal bend and a wider ground bend aligned around it.

    Args:
        radius: Bend radius (um).
        angle: Bend angle (degrees).
        signal_cross_section: Cross-section for the signal line.
        ground_cross_section: Cross-section for the ground line.
        width: Line width (µm). Mutually exclusive with Z0.
        Z0: Target characteristic impedance (ohms). Mutually exclusive with width.
    """

    width, Z0 = _resolve_tline_width_and_Z0(
        width=width,
        Z0=Z0,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
    )

    c = gf.Component()

    if angle == 90 or angle == 180:
        signal = c.add_ref(
            gf.c.bend_circular(
                radius=radius,
                angle=angle,
                cross_section=signal_cross_section,
                width=width,
                allow_min_radius_violation=True,
            )
        )
        c.add_ports(signal.ports)
        c.add_ref(
            gf.c.bend_circular(
                radius=radius,
                angle=angle,
                cross_section=ground_cross_section,
                width=7 * width,
                allow_min_radius_violation=True,
            )
        )
    else:
        signal = c.add_ref_off_grid(
            gf.c.bend_circular_all_angle(
                radius=radius,
                angle=angle,
                cross_section=signal_cross_section,
                width=width,
                allow_min_radius_violation=True,
            )
        )
        c.add_ports(signal.ports)
        c.add_ref_off_grid(
            gf.c.bend_circular_all_angle(
                radius=radius,
                angle=angle,
                cross_section=ground_cross_section,
                width=7 * width,
                allow_min_radius_violation=True,
            )
        )

    return c


@gf.cell
def tline_bend_euler(
    radius: float = 10,
    angle: float = 90,
    signal_cross_section: CrossSectionSpec = "topmetal2_routing",
    ground_cross_section: CrossSectionSpec = "topmetal1_routing",
    width: float | None = None,
    Z0: float | None = None,
) -> gf.Component:
    """Returns an euler bend coplanar transmission line.

    Creates a signal bend and a wider ground bend aligned around it.

    Args:
        radius: Bend radius (um).
        angle: Bend angle (degrees).
        signal_cross_section: Cross-section for the signal line.
        ground_cross_section: Cross-section for the ground line.
        width: Line width (µm). Mutually exclusive with Z0.
        Z0: Target characteristic impedance (ohms). Mutually exclusive with width.
    """

    width, Z0 = _resolve_tline_width_and_Z0(
        width=width,
        Z0=Z0,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
    )

    c = gf.Component()

    if angle == 90 or angle == 180:
        signal = c.add_ref(
            gf.c.bend_euler(
                radius=radius,
                angle=angle,
                cross_section=signal_cross_section,
                width=width,
                allow_min_radius_violation=True,
            )
        )
        c.add_ports(signal.ports)
        c.add_ref(
            gf.c.bend_euler(
                radius=radius,
                angle=angle,
                cross_section=ground_cross_section,
                width=7 * width,
                allow_min_radius_violation=True,
            )
        )
    else:
        signal = c.add_ref_off_grid(
            gf.c.bend_euler_all_angle(
                radius=radius,
                angle=angle,
                cross_section=signal_cross_section,
                width=width,
                allow_min_radius_violation=True,
            )
        )
        c.add_ports(signal.ports)
        c.add_ref_off_grid(
            gf.c.bend_euler_all_angle(
                radius=radius,
                angle=angle,
                cross_section=ground_cross_section,
                width=7 * width,
                allow_min_radius_violation=True,
            )
        )

    return c


@gf.cell
def tline_bend_s(
    size: Size = (11, 1.8),
    signal_cross_section: CrossSectionSpec = "topmetal2_routing",
    ground_cross_section: CrossSectionSpec = "topmetal1_routing",
    width: float | None = None,
    Z0: float | None = None,
) -> gf.Component:
    """Returns an S bend coplanar transmission line.

    Creates a signal bend and a wider ground bend aligned around it.

    Args:
        size: in x and y direction.
        signal_cross_section: Cross-section for the signal line.
        ground_cross_section: Cross-section for the ground line.
        width: Line width (µm). Mutually exclusive with Z0.
        Z0: Target characteristic impedance (ohms). Mutually exclusive with width.
    """

    width, Z0 = _resolve_tline_width_and_Z0(
        width=width,
        Z0=Z0,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
    )

    c = gf.Component()

    signal = c.add_ref(
        gf.c.bend_s(
            size=size,
            cross_section=signal_cross_section,
            width=width,
            allow_min_radius_violation=True,
        )
    )
    c.add_ports(signal.ports)
    c.add_ref(
        gf.c.bend_s(
            size=(size),
            cross_section=ground_cross_section,
            width=7 * width,
            allow_min_radius_violation=True,
        )
    )

    return c


@gf.cell
def tline_corner(
    length: float = 10,
    signal_cross_section: CrossSectionSpec = "topmetal2_routing",
    ground_cross_section: CrossSectionSpec
    | list[CrossSectionSpec] = "topmetal1_routing",
    width: float | None = None,
    Z0: float | None = None,
) -> gf.Component:
    """Return a right-angle corner transition for a transmission line.

    Args:
        length: Reserved parameter for API compatibility.
        signal_cross_section: Cross-section for the signal line.
        ground_cross_section: Ground cross-section, or ``[lower, upper]``
            for stripline.
        width: Signal width in um. Mutually exclusive with ``Z0``.
        Z0: Target characteristic impedance in ohms. Mutually exclusive
            with ``width``.

    Returns:
        A corner component with four electrical ports.
    """
    width, Z0 = _resolve_tline_width_and_Z0(
        width=width,
        Z0=Z0,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
    )

    c = gf.Component()
    # signal
    c.add_polygon(
        points=[(0, 0), (0, width), (width, width), (width, 0)],
        layer=gf.get_cross_section(signal_cross_section).layer,
    )

    extension = 3  # extension over signal plate
    if isinstance(ground_cross_section, list):
        # ground planes for stripline
        for gc in ground_cross_section:
            c.add_polygon(
                points=[
                    (0 - extension * width, -extension * width),
                    (0 - extension * width, width + extension * width),
                    (width + extension * width, width + extension * width),
                    (width + extension * width, 0 - extension * width),
                ],
                layer=gf.get_cross_section(gc).layer,
            )
    else:
        # ground plate
        c.add_polygon(
            points=[
                (0 - extension * width, -extension * width),
                (0 - extension * width, width + extension * width),
                (width + extension * width, width + extension * width),
                (width + extension * width, 0 - extension * width),
            ],
            layer=gf.get_cross_section(ground_cross_section).layer,
        )

    c.add_port(
        name="e1",
        center=(0, width / 2),
        width=width,
        orientation=180,
        port_type="electrical",
        layer=gf.get_cross_section(signal_cross_section).layer,
    )
    c.add_port(
        name="e2",
        center=(width / 2, width),
        width=width,
        orientation=90,
        port_type="electrical",
        layer=gf.get_cross_section(signal_cross_section).layer,
    )
    c.add_port(
        name="e3",
        center=(width, width / 2),
        width=width,
        orientation=0,
        port_type="electrical",
        layer=gf.get_cross_section(signal_cross_section).layer,
    )
    c.add_port(
        name="e4",
        center=(width / 2, 0),
        width=width,
        orientation=270,
        port_type="electrical",
        layer=gf.get_cross_section(signal_cross_section).layer,
    )
    return c


@gf.cell
def coupler_tline(
    Z0e: float = 50,
    Z0o: float = 50,
    length: float = 10,
    signal_cross_section: CrossSectionSpec = "topmetal2_routing",
    ground_cross_section: CrossSectionSpec = "topmetal1_routing",
    e_r: float = 4.1,
    npoints: int = 2,
) -> gf.Component:
    """Return a straight coupled coplanar transmission line.

    Creates two parallel signal lines separated by a gap, with a shared
    ground plane underneath (and optionally above for stripline).  The
    ground plane extends 3x the signal width beyond each end of the
    signal lines and is wide enough to cover both lines plus margins.

    Args:
        length: Length of the signal lines (um).
        gap: Spacing between the two signal lines (um).
        signal_cross_section: Cross-section for the signal lines.
        ground_cross_section: Cross-section for the ground plane.
            Accepts a single spec for microstrip or a two-element list
            ``[lower, upper]`` for stripline.
        width: Signal line width (um). Mutually exclusive with Z0.
        Z0: Target characteristic impedance (ohms). Mutually exclusive
            with width.
        npoints: Number of points used to draw the straights.

    Returns:
        A Component containing two coupled signal lines (with ports
        prefixed ``top_`` and ``bot_``) and ground plane(s).

    Raises:
        ValueError: If neither or both of *width* and *Z0* are provided.
    """
    Z0 = sqrt(Z0e * Z0o)

    width = _calculate_width_from_Z0(
        Z0=Z0,
        ground_cross_section=ground_cross_section,
        signal_cross_section=signal_cross_section,
        e_r=e_r,
    )

    h, t = _get_stack_geometry(signal_cross_section, ground_cross_section)

    # calculate separation gap from even and odd mode impedances
    # https://www.dmcrf.com/microstrip-calculators/differential-microstrip-impedance-calculator/
    Z_d = 2 * Z0o
    d = (
        -h
        / 0.98
        * log(1 - (Z_d * sqrt(e_r + 1.41)) / (174 * log(5.98 * h / (0.8 * width + t))))
    )

    c = gf.Component()

    top = c.add_ref(
        tline(
            length=length,
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            width=width,
            npoints=npoints,
        )
    )
    top.movey(d / 2 + width / 2)

    bot = c.add_ref(
        tline(
            length=length,
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            width=width,
            npoints=npoints,
        )
    )
    bot.movey(-d / 2 - width / 2)

    c.add_port(name="e1", port=top.ports["e1"])
    c.add_port(name="e2", port=top.ports["e2"])
    c.add_port(name="e3", port=bot.ports["e2"])
    c.add_port(name="e4", port=bot.ports["e1"])
    c.flatten()

    return c
