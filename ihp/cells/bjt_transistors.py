"""BJT Transistor components for IHP PDK."""

import math

import gdsfactory as gf
from gdsfactory.typings import LayerSpec
from kfactory.schematic import DSchematic

from ihp.tech import TECH as _TECH

_XS = "metal1_routing"


def fix(value):
    if type(value) is float:
        return int(math.floor(value))
    else:
        return value


def _snap_width_to_grid(width_um: float) -> float:
    """Snap port width to the nearest multiple of 0.002 um (2 DBU = 0.002 um).

    Args:
        width_um: Port width in microns.

    Returns:
        Width snapped to the nearest valid grid multiple.
    """
    grid = 0.002
    w = max(width_um, grid)
    return round(w / grid) * grid


def npn13G2_schematic(
    baspolyx: float = 0.3,
    bipwinx: float = 0.07,
    bipwiny: float = 0.1,
    empolyx: float = 0.15,
    empolyy: float = 0.18,
    STI: float = 0.44,
    emitter_length: float = 0.9,
    emitter_width: float = 0.7,
    Nx: int = 1,
    Ny: int = 1,
    text: str = "npn13G2",
    CMetY1: float = 0,
    CMetY2: float = 0,
) -> DSchematic:
    s = DSchematic()
    s.info["symbol"] = "npn"
    s.info["ports"] = [
        {"name": "BN", "side": "top", "type": "electric"},
        {"name": "E", "side": "bottom", "type": "electric"},
        {"name": "B", "side": "left", "type": "electric"},
        {"name": "C", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "implementation": "NgSpice",
            "name": "npn13G2",
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerHBT.lib",
            "sections": ["hbt_typ", "hbt_bcs", "hbt_wcs"],
            "port_order": ["C", "B", "E", "BN"],
            "params": {
                "Nx": "Nx",
                "Ny": "Ny",
                "we": "emitter_width * 1e-6",
                "le": "emitter_length * 1e-6",
            },
        },
        {
            "language": "spectre",
            "implementation": "VACASK",
            "name": "npn13G2",
            "spice_type": "SUBCKT",
            "library": "ihp/models/vacask/models/cornerHBT.lib",
            "sections": ["hbt_typ", "hbt_bcs", "hbt_wcs"],
            "port_order": ["C", "B", "E", "BN"],
            "params": {
                "Nx": "Nx",
                "Ny": "Ny",
                "we": "emitter_width * 1e-6",
                "le": "emitter_length * 1e-6",
            },
        },
    ]
    s.create_port(name="C", cross_section=_XS, x=1, y=0, orientation=0)
    s.create_port(name="B", cross_section=_XS, x=-1, y=0, orientation=180)
    s.create_port(name="E", cross_section=_XS, x=0, y=-1, orientation=270)
    s.create_port(name="BN", cross_section=_XS, x=0, y=1, orientation=90)
    return s


@gf.cell(schematic_function=npn13G2_schematic, tags=["IHP", "bjt", "npn"])
def npn13G2(
    baspolyx: float = 0.3,
    bipwinx: float = 0.07,
    bipwiny: float = 0.1,
    empolyx: float = 0.15,
    empolyy: float = 0.18,
    STI: float = 0.44,
    emitter_length: float = 0.9,
    emitter_width: float = 0.7,
    Nx: int = 1,
    Ny: int = 1,
    text: str = "npn13G2",
    CMetY1: float = 0,
    CMetY2: float = 0,
) -> gf.Component:
    """Returns the IHP npn13G2 BJT transistor as a gdsfactory Component.

    Args:
        Nx: Number of emitter fingers in the x-direction.
        Ny: Number of emitter fingers in the y-direction.
        emitter_length: Length of the emitter region in microns.
        emitter_width: Width of the emitter region in microns.
        STI: Shallow Trench Isolation width in microns.
        baspolyx: Base poly extension in x-direction in microns.
        bipwinx: Bipolar window extension in x-direction in microns.
        bipwiny: Bipolar window extension in y-direction in microns.
        empolyx: Emitter poly extension in x-direction in microns.
        empolyy: Emitter poly extension in y-direction in microns.
        text: Text label for the transistor.
        CMetY1: Contact metal Y1 dimension in microns.
        CMetY2: Contact metal Y2 dimension in microns.

    Returns:
        gdsfactory.Component: The generated npn13G2 transistor layout.

    Raises:
        ValueError: If finger count is outside allowed range.
    """
    total_nx = Nx * Ny
    if total_nx < _TECH.npn_min_nx or total_nx > _TECH.npn_max_nx:
        raise ValueError(
            f"npn13G2 Nx*Ny={total_nx} out of range [{_TECH.npn_min_nx}, {_TECH.npn_max_nx}]"
        )

    c = gf.Component()

    layer_via1: LayerSpec = "Via1drawing"
    layer_metal1: LayerSpec = "Metal1drawing"
    layer_cont: LayerSpec = "Contdrawing"
    layer_emwind: LayerSpec = "EmWinddrawing"
    layer_activmask: LayerSpec = "Activmask"
    layer_activ: LayerSpec = "Activdrawing"
    layer_metal1: LayerSpec = "Metal1drawing"
    layer_metal1_pin: LayerSpec = "Metal1pin"
    layer_metal2_pin: LayerSpec = "Metal2pin"
    layer_metal2: LayerSpec = "Metal2drawing"
    layer_nSDblock: LayerSpec = "nSDblock"
    layer_text: LayerSpec = "TEXTdrawing"
    layer_trans: LayerSpec = "TRANSdrawing"
    layer_pSD: LayerSpec = "pSDdrawing"

    ActivShift = 0.01
    ActivShift = 0.0

    # for multiplied npn: le has to be bigger
    stepX = 1.85
    stretchX = stepX * (Nx - 1)

    # stretchX = stepX * (Nx - 1)
    bipwinyoffset = (2 * (bipwiny - 0.1) - 0) / 2
    empolyyoffset = (2 * (empolyy - 0.18)) / 2

    empolyxoffset = (2 * (empolyx - 0.15)) / 2
    baspolyxoffset = (2 * (baspolyx - 0.3)) / 2
    STIoffset = (2 * (STI - 0.44)) / 2

    tmp = emitter_length
    le = emitter_width
    we = tmp

    nSDBlockShift = (
        0.43 - le
    )  # 23.07.09: needed to draw nSDBlock shorter in small pCell

    leoffset = 0  # ((le - 0.07) / 2)

    ##############
    # npn13G2_base

    pcStepY = 0.41
    yOffset = 0.20

    pcRepeatY = 4

    if Nx > 1:
        CMetY1 = 1.01 + we / 2 + leoffset + bipwinyoffset + empolyyoffset
        CMetY2 = 0.57 + we / 2 + leoffset + bipwinyoffset + empolyyoffset
    else:
        CMetY1 = 0.8 + we / 2 + leoffset + bipwinyoffset + empolyyoffset
        CMetY2 = 0.56 + we / 2 + leoffset + bipwinyoffset + empolyyoffset

    for pcIndexX in range(int(math.floor(Nx))):
        # loop for generate the given number of vias in variable pcRepeatY
        # two vias are generated per loop
        for pcIndexY in range(int(math.floor(pcRepeatY))):
            # Via on left side
            via1_size = 0.19
            left = (stepX * pcIndexX) - 0.3
            bottom = (
                -(
                    (-0.3 - yOffset - leoffset - bipwinyoffset - empolyyoffset)
                    + (pcIndexY * pcStepY)
                )
                + 0.2
                - via1_size
            )
            c.add_ref(
                gf.components.rectangle(
                    size=(
                        via1_size,
                        via1_size,
                    ),
                    layer=layer_via1,
                )
            ).move((left, bottom))

            left = (stepX * pcIndexX) + 0.11
            # Via on the right side
            c.add_ref(
                gf.components.rectangle(
                    size=(
                        via1_size,
                        via1_size,
                    ),
                    layer=layer_via1,
                )
            ).move((left, bottom))

        # Emitter metal
        left = (stepX * pcIndexX) - 0.35
        bottom = -(0.335 + we / 2 + leoffset + bipwinyoffset + empolyyoffset)
        right = stepX * pcIndexX + 0.35
        top = -(-0.32 - we / 2 - leoffset - bipwinyoffset - empolyyoffset)
        c.add_ref(
            gf.components.rectangle(
                size=(
                    right - left,
                    top - bottom,
                ),
                layer=layer_metal1,
            )
        ).move((left, bottom))
        # Cont layer
        left = stepX * pcIndexX - 0.79 - le / 2
        top = -(-0.76 - we / 2 - leoffset - bipwinyoffset - empolyyoffset)
        right = stepX * pcIndexX + 0.79 + le / 2
        bottom = -(-0.6 - we / 2 - leoffset - bipwinyoffset - empolyyoffset)
        c.add_ref(
            gf.components.rectangle(
                size=(
                    right - left,
                    top - bottom,
                ),
                layer=layer_cont,
            )
        ).move((left, bottom))

        left = stepX * pcIndexX - 0.76
        top = -(0.61 + we / 2 - leoffset - bipwinyoffset - empolyyoffset)
        right = stepX * pcIndexX + 0.76
        bottom = -(0.77 + we / 2 - leoffset - bipwinyoffset - empolyyoffset)
        c.add_ref(
            gf.components.rectangle(
                size=(
                    right - left,
                    top - bottom,
                ),
                layer=layer_cont,
            )
        ).move((left, bottom))

        # EmWind
        left = stepX * pcIndexX - le / 2
        top = we / 2 + leoffset
        right = stepX * pcIndexX + le / 2
        bottom = -we / 2 - leoffset
        c.add_ref(
            gf.components.rectangle(
                size=(
                    right - left,
                    top - bottom,
                ),
                layer=layer_emwind,
            )
        ).move((left, bottom))

        # Activmask
        xl = stepX * pcIndexX - 0.06
        xh = xl + 0.12
        yl = -0.24 - leoffset
        yh = -yl

        c.add_polygon(
            [
                (xh + 0.865, -yl + 0.74),
                (xl - 0.865, -yl + 0.74),
                (xl - 0.865, -yh - 0.38),
                (xl - 0.385, -yh - 0.38),
                (xl - 0.175, -yh - 0.59),
                (xh + 0.175, -yh - 0.59),
                (xh + 0.385, -yh - 0.38),
                (xh + 0.865, -yh - 0.38),
            ],
            layer=layer_activmask,
        )

        # Activ
        left = (
            stepX * pcIndexX
            - 0.89
            - le / 2
            - empolyxoffset
            - baspolyxoffset
            - STIoffset
        )
        top = -(-0.83 - we / 2 - leoffset - bipwinyoffset - empolyyoffset)
        right = (
            stepX * pcIndexX
            + 0.89
            + le / 2
            + empolyxoffset
            + baspolyxoffset
            + STIoffset
        )
        bottom = -(-0.89 - we / 2 + 0.36 - leoffset - bipwinyoffset - empolyyoffset)
        c.add_ref(
            gf.components.rectangle(
                size=(
                    right - left,
                    top - bottom,
                ),
                layer=layer_activ,
            )
        ).move((left, bottom))

        c.add_polygon(
            [
                (
                    stepX * pcIndexX
                    + 0.94
                    + le / 2
                    + empolyxoffset
                    + baspolyxoffset
                    + STIoffset,
                    -(1.98 + we / 2 + leoffset + bipwinyoffset + empolyyoffset),
                ),
                (
                    stepX * pcIndexX
                    + 0.94
                    + le / 2
                    + empolyxoffset
                    + baspolyxoffset
                    + STIoffset,
                    -(0.45 + we / 2 + leoffset + bipwinyoffset + empolyyoffset),
                ),
                (
                    stepX * pcIndexX
                    + 0.52
                    + le / 2
                    + empolyxoffset
                    + baspolyxoffset
                    + STIoffset,
                    -(0.03 + we / 2 + leoffset + bipwinyoffset + empolyyoffset),
                ),
                (
                    stepX * pcIndexX
                    + 0.52
                    + le / 2
                    + empolyxoffset
                    + baspolyxoffset
                    + STIoffset,
                    -(
                        -0.6
                        - we / 2
                        + leoffset
                        + bipwinyoffset
                        + empolyyoffset
                        + nSDBlockShift
                    ),
                ),
                (
                    stepX * pcIndexX
                    + 0.27
                    + le / 2
                    + empolyxoffset
                    + baspolyxoffset
                    + STIoffset,
                    -(
                        -0.85
                        - we / 2
                        + leoffset
                        + bipwinyoffset
                        + empolyyoffset
                        + nSDBlockShift
                    ),
                ),
                (
                    stepX * pcIndexX
                    - 0.27
                    - le / 2
                    - empolyxoffset
                    - baspolyxoffset
                    - STIoffset,
                    -(
                        -0.85
                        - we / 2
                        + leoffset
                        + bipwinyoffset
                        + empolyyoffset
                        + nSDBlockShift
                    ),
                ),
                (
                    stepX * pcIndexX
                    - 0.52
                    - le / 2
                    - empolyxoffset
                    - baspolyxoffset
                    - STIoffset,
                    -(
                        -0.6
                        - we / 2
                        + leoffset
                        + bipwinyoffset
                        + empolyyoffset
                        + nSDBlockShift
                    ),
                ),
                (
                    stepX * pcIndexX
                    - 0.52
                    - le / 2
                    - empolyxoffset
                    - baspolyxoffset
                    - STIoffset,
                    -(0.03 + we / 2 + leoffset + bipwinyoffset + empolyyoffset),
                ),
                (
                    stepX * pcIndexX
                    - 0.94
                    - le / 2
                    - empolyxoffset
                    - baspolyxoffset
                    - STIoffset,
                    -(0.45 + we / 2 + leoffset + bipwinyoffset + empolyyoffset),
                ),
                (
                    stepX * pcIndexX
                    - 0.94
                    - le / 2
                    - empolyxoffset
                    - baspolyxoffset
                    - STIoffset,
                    -(1.98 + we / 2 + leoffset + bipwinyoffset + empolyyoffset),
                ),
            ],
            layer=layer_nSDblock,
        )

        # Collector metal
        left = -0.89 - le / 2
        top = CMetY1
        right = stretchX + 0.89 + le / 2
        bottom = CMetY2
        c.add_ref(
            gf.components.rectangle(
                size=(
                    right - left,
                    top - bottom,
                ),
                layer=layer_metal1,
            )
        ).move((left, bottom))

        # Base metal
        left = -0.94 - le / 2
        bottom = -(0.81 + we / 2 + leoffset + bipwinyoffset + empolyyoffset)
        right = stretchX + 0.94 + le / 2
        top = -(0.57 + we / 2 + leoffset + bipwinyoffset + empolyyoffset)
        c.add_ref(
            gf.components.rectangle(
                size=(
                    right - left,
                    top - bottom,
                ),
                layer=layer_metal1,
            )
        ).move((left, bottom))

        # Metal2
        left = -0.89 - le / 2
        bottom = -(0.335 + we / 2 + leoffset + bipwinyoffset + empolyyoffset)
        right = stretchX + 0.89 + le / 2
        top = -(-0.32 - we / 2 - leoffset - bipwinyoffset - empolyyoffset)
        c.add_ref(
            gf.components.rectangle(
                size=(
                    right - left,
                    top - bottom,
                ),
                layer=layer_metal2,
            )
        ).move((left, bottom))

        c.add_label(
            text=text,
            layer=layer_text,
            position=(
                0.015,
                1.86 + we / 2 + leoffset + bipwinyoffset + empolyyoffset,
            ),
        )

        c.add_polygon(
            [
                (
                    stretchX + 2.45,
                    (2.43 + we / 2 + leoffset + bipwinyoffset + empolyyoffset),
                ),
                (-2.45, (2.43 + we / 2 + leoffset + bipwinyoffset + empolyyoffset)),
                (-2.45, (-1.98 - we / 2 - leoffset - bipwinyoffset - empolyyoffset)),
                (
                    stretchX + 2.45,
                    (-1.98 - we / 2 - leoffset - bipwinyoffset - empolyyoffset),
                ),
            ],
            layer=layer_trans,
        )

        c.add_polygon(
            [
                (
                    stretchX + 3.35,
                    (3.33 + we / 2 + leoffset + bipwinyoffset + empolyyoffset),
                ),
                (
                    stretchX + 2.45,
                    (3.33 + we / 2 + leoffset + bipwinyoffset + empolyyoffset),
                ),
                (
                    stretchX + 2.45,
                    (-1.98 - we / 2 - leoffset - bipwinyoffset - empolyyoffset),
                ),
                (-2.45, (-1.98 - we / 2 - leoffset - bipwinyoffset - empolyyoffset)),
                (-2.45, (2.43 + we / 2 + leoffset + bipwinyoffset + empolyyoffset)),
                (
                    stretchX + 2.45,
                    (2.43 + we / 2 + leoffset + bipwinyoffset + empolyyoffset),
                ),
                (
                    stretchX + 2.45,
                    (3.33 + we / 2 + leoffset + bipwinyoffset + empolyyoffset),
                ),
                (-3.35, (3.33 + we / 2 + leoffset + bipwinyoffset + empolyyoffset)),
                (-3.35, (-2.88 - we / 2 - leoffset - bipwinyoffset - empolyyoffset)),
                (
                    stretchX + 3.35,
                    (-2.88 - we / 2 - leoffset - bipwinyoffset - empolyyoffset),
                ),
            ],
            layer=layer_pSD,
        )

        c.add_polygon(
            [
                (
                    stretchX + 3.15 + ActivShift,
                    3.13
                    + we / 2
                    + leoffset
                    + bipwinyoffset
                    + empolyyoffset
                    + ActivShift,
                ),
                (
                    stretchX + 2.65 + ActivShift,
                    3.13
                    + we / 2
                    + leoffset
                    + bipwinyoffset
                    + empolyyoffset
                    + ActivShift,
                ),
                (
                    stretchX + 2.65 + ActivShift,
                    -2.18
                    - we / 2
                    - leoffset
                    - bipwinyoffset
                    - empolyyoffset
                    - ActivShift,
                ),
                (
                    -2.65 - ActivShift,
                    -2.18
                    - we / 2
                    - leoffset
                    - bipwinyoffset
                    - empolyyoffset
                    - ActivShift,
                ),
                (
                    -2.65 - ActivShift,
                    2.63
                    + we / 2
                    + leoffset
                    + bipwinyoffset
                    + empolyyoffset
                    + ActivShift,
                ),
                (
                    stretchX + 2.65 + ActivShift,
                    2.63
                    + we / 2
                    + leoffset
                    + bipwinyoffset
                    + empolyyoffset
                    + ActivShift,
                ),
                (
                    stretchX + 2.65 + ActivShift,
                    3.13
                    + we / 2
                    + leoffset
                    + bipwinyoffset
                    + empolyyoffset
                    + ActivShift,
                ),
                (
                    -3.15 - ActivShift,
                    3.13
                    + we / 2
                    + leoffset
                    + bipwinyoffset
                    + empolyyoffset
                    + ActivShift,
                ),
                (
                    -3.15 - ActivShift,
                    -2.68
                    - we / 2
                    - leoffset
                    - bipwinyoffset
                    - empolyyoffset
                    - ActivShift,
                ),
                (
                    stretchX + 3.15 + ActivShift,
                    -2.68
                    - we / 2
                    - leoffset
                    - bipwinyoffset
                    - empolyyoffset
                    - ActivShift,
                ),
            ],
            layer=layer_activ,
        )

    if Nx > 1:
        left = -0.89 - le / 2
        bottom = 0.57 + we / 2 - leoffset - bipwinyoffset - empolyyoffset
        right = stretchX + 0.89 + le / 2
        top = 1.01 + we / 2 - leoffset - bipwinyoffset - empolyyoffset
        c.add_ref(
            gf.components.rectangle(
                size=(
                    right - left,
                    top - bottom,
                ),
                layer=layer_metal1_pin,
            )
        ).move((left, bottom))
        c.add_label(
            text="C",
            layer=layer_text,
            position=(
                0.5 * (left + right),
                0.5 * (top + bottom),
            ),
        )
    else:
        left = -0.89 - le / 2
        bottom = 0.56 + we / 2 + leoffset + bipwinyoffset + empolyyoffset
        right = stretchX + 0.89 + le / 2
        top = 0.8 + we / 2 + leoffset + bipwinyoffset + empolyyoffset
        c.add_ref(
            gf.components.rectangle(
                size=(
                    right - left,
                    top - bottom,
                ),
                layer=layer_metal1_pin,
            )
        ).move((left, bottom))
        c.add_label(
            text="C",
            layer=layer_text,
            position=(
                0.5 * (left + right),
                0.5 * (top + bottom),
            ),
        )
    # Collector port
    c.add_port(
        "C",
        center=(0.5 * (left + right), 0.5 * (top + bottom)),
        width=_snap_width_to_grid(top - bottom),
        layer=layer_metal1_pin,
        orientation=180.0,
        port_type="electrical",
    )

    left = -0.94 - le / 2
    bottom = -0.81 - we / 2 - leoffset - bipwinyoffset - empolyyoffset
    right = stretchX + 0.94 + le / 2
    top = -0.57 - we / 2 - leoffset - bipwinyoffset - empolyyoffset
    c.add_ref(
        gf.components.rectangle(
            size=(
                right - left,
                top - bottom,
            ),
            layer=layer_metal1_pin,
        )
    ).move((left, bottom))
    c.add_label(
        text="B",
        layer=layer_text,
        position=(
            0.5 * (left + right),
            0.5 * (top + bottom),
        ),
    )

    # Base port
    c.add_port(
        "B",
        center=(0.5 * (left + right), 0.5 * (top + bottom)),
        width=_snap_width_to_grid(top - bottom),
        layer=layer_metal1_pin,
        orientation=180.0,
        port_type="electrical",
    )

    left = -0.71 - le / 2
    bottom = -0.335 - we / 2 - leoffset - bipwinyoffset - empolyyoffset
    right = stretchX + 0.71 + le / 2
    top = 0.32 + we / 2 + leoffset + bipwinyoffset + empolyyoffset
    c.add_ref(
        gf.components.rectangle(
            size=(
                right - left,
                top - bottom,
            ),
            layer=layer_metal2_pin,
        )
    ).move((left, bottom))
    c.add_label(
        text="E",
        layer=layer_text,
        position=(
            0.5 * (left + right),
            0.5 * (top + bottom),
        ),
    )

    pcLabelText = f"Ae={int(Nx):d}*{int(Ny):d}*{le:.2f}*{we:.2f}"
    c.add_label(text=pcLabelText, layer=layer_text, position=(-1.977, -2.546))

    # Emitter port
    c.add_port(
        "E",
        center=(0.5 * (left + right), 0.5 * (top + bottom)),
        width=_snap_width_to_grid(top - bottom),
        layer=layer_metal2_pin,
        orientation=180.0,
        port_type="electrical",
    )

    return c


def npn13G2L_schematic(
    emitter_length: float = 1,
    emitter_width: float = 0.07,
    Nx: int = 1,
) -> DSchematic:
    s = DSchematic()
    s.info["symbol"] = "npn"
    s.info["ports"] = [
        {"name": "BN", "side": "top", "type": "electric"},
        {"name": "E", "side": "bottom", "type": "electric"},
        {"name": "B", "side": "left", "type": "electric"},
        {"name": "C", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "implementation": "NgSpice",
            "name": "npn13G2l",
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerHBT.lib",
            "sections": ["hbt_typ", "hbt_bcs", "hbt_wcs"],
            "port_order": ["C", "B", "E", "BN"],
            "params": {
                "we": "emitter_width * 1e-6",
                "le": "emitter_length * 1e-6",
            },
        },
        {
            "language": "spectre",
            "implementation": "VACASK",
            "name": "npn13G2l",
            "spice_type": "SUBCKT",
            "library": "ihp/models/vacask/models/cornerHBT.lib",
            "sections": ["hbt_typ", "hbt_bcs", "hbt_wcs"],
            "port_order": ["C", "B", "E", "BN"],
            "params": {
                "we": "emitter_width * 1e-6",
                "le": "emitter_length * 1e-6",
            },
        },
    ]
    s.create_port(name="C", cross_section=_XS, x=1, y=0, orientation=0)
    s.create_port(name="B", cross_section=_XS, x=-1, y=0, orientation=180)
    s.create_port(name="E", cross_section=_XS, x=0, y=-1, orientation=270)
    s.create_port(name="BN", cross_section=_XS, x=0, y=1, orientation=90)
    return s


@gf.cell(schematic_function=npn13G2L_schematic, tags=["IHP", "bjt", "npn"])
def npn13G2L(
    emitter_length: float = 1,
    emitter_width: float = 0.07,
    Nx: int = 1,
) -> gf.Component:
    """Builds the IHP npn13G2L BJT transistor as a gdsfactory Component.

    The transistor geometry is defined by the number of emitter fingers and the dimensions
    of each emitter finger.

    Args:
        emitter_length: Length of each emitter finger, in microns.
        emitter_width: Width of each emitter finger, in microns.
        Nx: Number of emitter fingers.

    Returns:
        gdsfactory.Component: The generated npn13G2L transistor layout.

    Raises:
        ValueError: If finger count is outside allowed range.
    """
    if Nx < _TECH.npn_min_nx or Nx > _TECH.npn_max_nx:
        raise ValueError(
            f"npn13G2L Nx={Nx} out of range [{_TECH.npn_min_nx}, {_TECH.npn_max_nx}]"
        )

    c = gf.Component()

    layer_EmWind: LayerSpec = "EmWinddrawing"
    layer_HeatTrans: LayerSpec = "HeatTransdrawing"
    layer_activ: LayerSpec = "Activdrawing"
    layer_activ_mask: LayerSpec = "Activmask"
    layer_via1: LayerSpec = "Via1drawing"
    layer_cont: LayerSpec = "Contdrawing"
    layer_metal1: LayerSpec = "Metal1drawing"
    layer_metal1_pin: LayerSpec = "Metal1pin"
    layer_metal2: LayerSpec = "Metal2drawing"
    layer_metal2_pin: LayerSpec = "Metal2pin"
    layer_trans: LayerSpec = "TRANSdrawing"
    layer_text: LayerSpec = "TEXTdrawing"
    layer_pSD: LayerSpec = "pSDdrawing"

    le = emitter_length
    we = emitter_width
    # masterLib = "SG13_dev"

    # emPoly_enc_vert = 0.16
    # emPoly_enc_hori = 0.13
    emWindOrigin_x = 3.865
    emWindOrigin_y = 3.1
    # BiWind_enc_vert = 0.1
    # BiWind_enc_hori = 0.07
    # ColWind_enc_vert = 0.58
    # ColWind_enc_hori = 1.515
    Activ_enc_vert = 0.28
    Activ_enc_hori = 1.365
    # BasPoly_enc_vert = 0.45
    # BasPoly_enc_hori = 0.58
    Col_Metal1_distance = 0.975
    Col_Metal1_width = 0.39
    Bas_Metal1_distance = 0.32
    Bas_Metal1_width = 0.16
    Emi_Metal1_enc_vert = 0.2
    Emi_Metal1_enc_hori = 0.095

    column_pitch = 2.8

    c.add_ref(
        gf.components.rectangle(
            size=(we, le),
            layer=layer_EmWind,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x, emWindOrigin_y))

    c.add_ref(
        gf.components.rectangle(
            size=(
                we + 0.1,
                le + 0.1,
            ),
            layer=layer_HeatTrans,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x - 0.05, emWindOrigin_y - 0.05))

    c.add_label(
        text="npn13G2L",
        layer=layer_HeatTrans,
        position=(
            0.5 * (2 * emWindOrigin_x + we),
            0.5 * (2 * emWindOrigin_y + le),
        ),
    )

    # Activ Drawing
    outer = c << gf.components.rectangle(
        size=(
            we + 2 * Activ_enc_hori,
            le + 2 * Activ_enc_vert,
        ),
        layer=layer_activ,
    )
    outer.move((emWindOrigin_x - Activ_enc_hori, emWindOrigin_y - Activ_enc_vert))

    # Activ mask
    inner = c << gf.components.rectangle(
        size=(
            0.705 - Emi_Metal1_enc_hori,
            le + 2 * Activ_enc_vert,
        ),
        layer=layer_activ_mask,
    )
    inner.move((emWindOrigin_x - 0.705, emWindOrigin_y - Activ_enc_vert))

    inner1 = c << gf.components.rectangle(
        size=(
            0.705 - Emi_Metal1_enc_hori,
            le + 2 * Activ_enc_vert,
        ),
        layer=layer_activ_mask,
    )
    inner1.move(
        (emWindOrigin_x + we + Emi_Metal1_enc_hori, emWindOrigin_y - Activ_enc_vert)
    )

    # Combine mask's rectangles in order to remove them from activ
    inners = gf.boolean(inner, inner1, operation="or", layer=layer_activ_mask)

    c.add_ref(inners, columns=Nx, column_pitch=column_pitch)

    c.add_ref(
        gf.boolean(
            outer,
            inners,
            operation="not",
            layer=layer_activ,
            layer1=layer_activ,
            layer2=layer_activ_mask,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    )
    # Delete the rectangle that was covering the whole region
    outer.delete()

    # Draw contacts and Via
    c.add_ref(
        gf.components.rectangle(
            size=(
                0.19,
                0.2 + le,
            ),
            layer=layer_via1,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((3.805, 3))

    c.add_ref(
        gf.components.rectangle(
            size=(
                0.16,
                0.3 + le,
            ),
            layer=layer_cont,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((2.68, 2.95))

    c.add_ref(
        gf.components.rectangle(
            size=(
                0.16,
                0.3 + le,
            ),
            layer=layer_cont,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((3.82, 2.95))

    c.add_ref(
        gf.components.rectangle(
            size=(
                0.16,
                0.3 + le,
            ),
            layer=layer_cont,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((4.96, 2.95))

    cont_cnt = fix((le + 0.21) / (0.16 + 0.18))

    for i in range(int(cont_cnt + 1)):
        c.add_ref(
            gf.components.rectangle(
                size=(
                    0.16,
                    0.16,
                ),
                layer=layer_cont,
            ),
            columns=Nx,
            column_pitch=column_pitch,
        ).move((3.385, 2.89 + i * (0.16 + 0.18)))

        c.add_ref(
            gf.components.rectangle(
                size=(
                    0.16,
                    0.16,
                ),
                layer=layer_cont,
            ),
            columns=Nx,
            column_pitch=column_pitch,
        ).move((4.255, 2.89 + i * (0.16 + 0.18)))

    # Metals
    # Metal Path upwards
    # Collector
    c.add_ref(
        gf.components.rectangle(
            size=(
                Col_Metal1_width,
                4.1 - 2.82 + le,
            ),
            layer=layer_metal1,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x - Col_Metal1_distance - Col_Metal1_width, 2.82))

    c.add_ref(
        gf.components.rectangle(
            size=(
                Col_Metal1_width,
                4.1 - 2.82 + le,
            ),
            layer=layer_metal1,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x + we + Col_Metal1_distance, 2.82))

    c.add_ref(
        gf.components.rectangle(
            size=(
                2 * Col_Metal1_distance + we + 2 * Col_Metal1_width,
                0.65,
            ),
            layer=layer_metal1,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x - Col_Metal1_distance - Col_Metal1_width, 4.1 + le))

    collector_pin_xmin = emWindOrigin_x - Col_Metal1_distance - Col_Metal1_width
    collector_pin_xmax = (
        collector_pin_xmin + 2 * Col_Metal1_distance + we + 2 * Col_Metal1_width
    )
    # The maximum x depends on the number of elements
    collector_pin_xmax += (Nx - 1) * (collector_pin_xmax - collector_pin_xmin)
    collector_pin_ymin = 4.1 + le
    collector_pin_ymax = collector_pin_ymin + 0.65

    c.add_ref(
        gf.components.rectangle(
            size=(
                2 * Col_Metal1_distance + we + 2 * Col_Metal1_width,
                0.65,
            ),
            layer=layer_metal1_pin,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x - Col_Metal1_distance - Col_Metal1_width, 4.1 + le))

    c.add_ref(
        gf.components.rectangle(
            size=(
                Bas_Metal1_width,
                1.28 + le,
            ),
            layer=layer_metal1,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x - Bas_Metal1_distance - Bas_Metal1_width, 2.1))

    c.add_ref(
        gf.components.rectangle(
            size=(
                Bas_Metal1_width,
                1.28 + le,
            ),
            layer=layer_metal1,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x + we + Bas_Metal1_distance, 2.1))

    c.add_ref(
        gf.components.rectangle(
            size=(
                2 * Bas_Metal1_distance + we + 2 * Bas_Metal1_width,
                0.65,
            ),
            layer=layer_metal1,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x - Bas_Metal1_distance - Bas_Metal1_width, 1.45))

    base_pin_xmin = emWindOrigin_x - Bas_Metal1_distance - Bas_Metal1_width
    base_pin_xmax = base_pin_xmin + 2 * Bas_Metal1_distance + we + 2 * Bas_Metal1_width
    # The maximum x depends on the number of elements
    base_pin_xmax += (Nx - 1) * column_pitch
    base_pin_ymin = 1.45
    base_pin_ymax = base_pin_ymin + 0.65

    c.add_ref(
        gf.components.rectangle(
            size=(
                2 * Bas_Metal1_distance + we + 2 * Bas_Metal1_width,
                0.65,
            ),
            layer=layer_metal1_pin,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x - Bas_Metal1_distance - Bas_Metal1_width, 1.45))

    # Emitter
    c.add_ref(
        gf.components.rectangle(
            size=(
                we + 2 * Emi_Metal1_enc_hori,
                le + 2 * Emi_Metal1_enc_vert,
            ),
            layer=layer_metal1,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x - Emi_Metal1_enc_hori, emWindOrigin_y - Emi_Metal1_enc_vert))

    c.add_ref(
        gf.components.rectangle(
            size=(
                we + 2 * Col_Metal1_distance + 2 * Col_Metal1_width,
                le + 0.4,
            ),
            layer=layer_metal2,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x - Col_Metal1_distance - Col_Metal1_width, 2.9))

    emitter_pin_xmin = emWindOrigin_x - Col_Metal1_distance - Col_Metal1_width
    emitter_pin_xmax = (
        emitter_pin_xmin + 2 * Col_Metal1_distance + we + 2 * Col_Metal1_width
    )
    # The maximum x depends on the number of elements
    emitter_pin_xmax += (Nx - 1) * (emitter_pin_xmax - emitter_pin_xmin)
    emitter_pin_ymin = 2.9
    emitter_pin_ymax = emitter_pin_ymin + le + 0.4

    c.add_ref(
        gf.components.rectangle(
            size=(
                we + 2 * Col_Metal1_distance + 2 * Col_Metal1_width,
                le + 0.4,
            ),
            layer=layer_metal2_pin,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x - Col_Metal1_distance - Col_Metal1_width, 2.9))

    # Draw Guard Ring
    c.add_ref(
        gf.components.rectangle(
            size=(
                6 + ((Nx - 1) * 2.8),
                le + 4.4,
            ),
            layer=layer_trans,
        )
    ).move((0.9, 0.9))

    outer = c << gf.components.rectangle(
        size=(
            7.8 + ((Nx - 1) * 2.8),
            le + 6.2,
        ),
        layer=layer_pSD,
    )

    inner = c << gf.components.rectangle(
        size=(
            6 + ((Nx - 1) * 2.8),
            le + 4.4,
        ),
        layer=layer_pSD,
    )
    inner.move((0.9, 0.9))

    c.add_ref(
        gf.boolean(
            outer,
            inner,
            operation="not",
            layer=layer_pSD,
            layer1=layer_pSD,
            layer2=layer_pSD,
        )
    )
    # Delete the rectangle that was covering the whole region
    outer.delete()
    # Delete the inner rectangle used for boolean
    inner.delete()

    outer = c << gf.components.rectangle(
        size=(
            7.4 + ((Nx - 1) * 2.8),
            le + 5.8,
        ),
        layer=layer_activ,
    )
    outer.move((0.2, 0.2))
    inner = c << gf.components.rectangle(
        size=(
            6.4 + ((Nx - 1) * 2.8),
            le + 4.8,
        ),
        layer=layer_activ,
    )
    inner.move((0.7, 0.7))
    c.add_ref(
        gf.boolean(
            outer,
            inner,
            operation="not",
            layer=layer_activ,
            layer1=layer_activ,
            layer2=layer_activ,
        )
    )
    # Delete the rectangle that was covering the whole region
    outer.delete()
    # Delete the inner rectangle used for boolean
    inner.delete()

    # Texts
    pcLabelText = f"Ae={int(Nx):d}*{1:d}*{le:.2f}*{we:.2f}"
    c.add_label(text=pcLabelText, layer=layer_text, position=(1.5, 1.0))

    c.add_label(text="npn13G2L", layer=layer_text, position=(1.75, 1.0))

    if Nx > 1:
        c.add_ref(
            gf.components.rectangle(
                size=(
                    1.77,
                    0.65,
                ),
                layer=layer_metal1,
            ),
            columns=Nx - 1,
            column_pitch=column_pitch,
        ).move((4.415, 1.45))
        c.add_ref(
            gf.components.rectangle(
                size=(
                    1.77,
                    0.65,
                ),
                layer=layer_metal1_pin,
            ),
            columns=Nx - 1,
            column_pitch=column_pitch,
        ).move((4.415, 1.45))

    # Ports
    # Collector port
    c.add_port(
        "C",
        center=(
            0.5 * (collector_pin_xmin + collector_pin_xmax),
            0.5 * (collector_pin_ymin + collector_pin_ymax),
        ),
        width=_snap_width_to_grid(collector_pin_ymax - collector_pin_ymin),
        layer=layer_metal1_pin,
        orientation=180.0,
        port_type="electrical",
    )

    c.add_label(
        text="C",
        layer=layer_text,
        position=(
            0.5 * (collector_pin_xmin + collector_pin_xmax),
            0.5 * (collector_pin_ymin + collector_pin_ymax),
        ),
    )

    # Base port
    c.add_port(
        "B",
        center=(
            0.5 * (base_pin_xmin + base_pin_xmax),
            0.5 * (base_pin_ymin + base_pin_ymax),
        ),
        width=_snap_width_to_grid(base_pin_ymax - base_pin_ymin),
        layer=layer_metal1_pin,
        orientation=180.0,
        port_type="electrical",
    )
    c.add_label(
        text="B",
        layer=layer_text,
        position=(
            0.5 * (base_pin_xmin + base_pin_xmax),
            0.5 * (base_pin_ymin + base_pin_ymax),
        ),
    )

    # Emitter port
    c.add_port(
        "E",
        center=(
            0.5 * (emitter_pin_xmin + emitter_pin_xmax),
            0.5 * (emitter_pin_ymin + emitter_pin_ymax),
        ),
        width=_snap_width_to_grid(emitter_pin_ymax - emitter_pin_ymin),
        layer=layer_metal2_pin,
        orientation=180.0,
        port_type="electrical",
    )
    c.add_label(
        text="E",
        layer=layer_text,
        position=(
            0.5 * (emitter_pin_xmin + emitter_pin_xmax),
            0.5 * (emitter_pin_ymin + emitter_pin_ymax),
        ),
    )

    return c


def npn13G2V_schematic(
    emitter_length: float = 1,
    emitter_width: float = 0.12,
    Nx: int = 1,
) -> DSchematic:
    s = DSchematic()
    s.info["symbol"] = "npn"
    s.info["ports"] = [
        {"name": "BN", "side": "top", "type": "electric"},
        {"name": "E", "side": "bottom", "type": "electric"},
        {"name": "B", "side": "left", "type": "electric"},
        {"name": "C", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "implementation": "NgSpice",
            "name": "npn13G2v",
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerHBT.lib",
            "sections": ["hbt_typ", "hbt_bcs", "hbt_wcs"],
            "port_order": ["C", "B", "E", "BN"],
            "params": {
                "we": "emitter_width * 1e-6",
                "le": "emitter_length * 1e-6",
            },
        },
        {
            "language": "spectre",
            "implementation": "VACASK",
            "name": "npn13G2v",
            "spice_type": "SUBCKT",
            "library": "ihp/models/vacask/models/cornerHBT.lib",
            "sections": ["hbt_typ", "hbt_bcs", "hbt_wcs"],
            "port_order": ["C", "B", "E", "BN"],
            "params": {
                "we": "emitter_width * 1e-6",
                "le": "emitter_length * 1e-6",
            },
        },
    ]
    s.create_port(name="C", cross_section=_XS, x=1, y=0, orientation=0)
    s.create_port(name="B", cross_section=_XS, x=-1, y=0, orientation=180)
    s.create_port(name="E", cross_section=_XS, x=0, y=-1, orientation=270)
    s.create_port(name="BN", cross_section=_XS, x=0, y=1, orientation=90)
    return s


@gf.cell(schematic_function=npn13G2V_schematic, tags=["IHP", "bjt", "npn"])
def npn13G2V(
    emitter_length: float = 1,
    emitter_width: float = 0.12,
    Nx: int = 1,
) -> gf.Component:
    """Builds the IHP npn13G2V BJT transistor as a gdsfactory Component.

    The transistor geometry is defined by the number of emitter fingers and the dimensions
    of each emitter finger.

    Args:
        emitter_length: Length of each emitter finger, in microns.
        emitter_width: Width of each emitter finger, in microns.
        Nx: Number of emitter fingers.

    Returns:
        gdsfactory.Component: The generated npn13G2V transistor layout.

    Raises:
        ValueError: If finger count is outside allowed range.
    """
    if Nx < _TECH.npn_min_nx or Nx > _TECH.npn_max_nx:
        raise ValueError(
            f"npn13G2V Nx={Nx} out of range [{_TECH.npn_min_nx}, {_TECH.npn_max_nx}]"
        )

    c = gf.Component()

    layer_EmWiHV: LayerSpec = "EmWiHVdrawing"
    layer_HeatTrans: LayerSpec = "HeatTransdrawing"
    layer_activ: LayerSpec = "Activdrawing"
    layer_activ_mask: LayerSpec = "Activmask"
    layer_via1: LayerSpec = "Via1drawing"
    layer_cont: LayerSpec = "Contdrawing"
    layer_metal1: LayerSpec = "Metal1drawing"
    layer_metal1_pin: LayerSpec = "Metal1pin"
    layer_metal2: LayerSpec = "Metal2drawing"
    layer_metal2_pin: LayerSpec = "Metal2pin"
    layer_trans: LayerSpec = "TRANSdrawing"
    layer_text: LayerSpec = "TEXTdrawing"
    layer_pSD: LayerSpec = "pSDdrawing"

    le = emitter_length
    we = emitter_width
    # masterLib = "SG13_dev"

    emWindOrigin_x = 3.81
    emWindOrigin_y = 3.1
    Activ_enc_vert = 0.28
    Activ_enc_hori = 1.11
    Col_Metal1_distance = 0.79
    Col_Metal1_width = 0.32
    Bas_Metal1_distance = 0.295
    Bas_Metal1_width = 0.17
    Emi_Metal1_enc_vert = 0.28
    Emi_Metal1_enc_hori = 0.07

    Via1Width = _TECH.via1_size_rf
    Via1Space = _TECH.via1_spacing_narrow
    m1EncVia1 = _TECH.via1_enc

    column_pitch = 2.34

    c.add_ref(
        gf.components.rectangle(
            size=(we, le),
            layer=layer_EmWiHV,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x, emWindOrigin_y))

    c.add_ref(
        gf.components.rectangle(
            size=(
                we + 0.1,
                le + 0.1,
            ),
            layer=layer_HeatTrans,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x - 0.05, emWindOrigin_y - 0.05))

    c.add_label(
        text="npn13G2V",
        layer=layer_HeatTrans,
        position=(
            0.5 * (2 * emWindOrigin_x + we),
            0.5 * (2 * emWindOrigin_y + le),
        ),
    )

    # Activ Drawing
    outer = c << gf.components.rectangle(
        size=(
            we + 2 * Activ_enc_hori,
            le + 2 * Activ_enc_vert,
        ),
        layer=layer_activ,
    )
    outer.move((emWindOrigin_x - Activ_enc_hori, emWindOrigin_y - Activ_enc_vert))

    # Activ mask
    inner = c << gf.components.rectangle(
        size=(
            0.705 - Emi_Metal1_enc_hori,
            le + 2 * Activ_enc_vert,
        ),
        layer=layer_activ_mask,
    )
    inner.move((emWindOrigin_x - 0.705, emWindOrigin_y - Activ_enc_vert))

    inner1 = c << gf.components.rectangle(
        size=(
            0.705 - Emi_Metal1_enc_hori,
            le + 2 * Activ_enc_vert,
        ),
        layer=layer_activ_mask,
    )
    inner1.move(
        (emWindOrigin_x + we + Emi_Metal1_enc_hori, emWindOrigin_y - Activ_enc_vert)
    )

    # Combine mask's rectangles in order to remove them from activ
    inners = gf.boolean(inner, inner1, operation="xor", layer=layer_activ_mask)

    c.add_ref(inners, columns=Nx, column_pitch=column_pitch)

    c.add_ref(
        gf.boolean(
            outer,
            inners,
            operation="not",
            layer=layer_activ,
            layer1=layer_activ,
            layer2=layer_activ_mask,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    )
    # Delete the rectangle that was covering the whole region
    outer.delete()

    # Draw Via
    via_cnt = int((le + 0.46) / (0.19 + 0.22))

    emMet1_height = le + 2 * Emi_Metal1_enc_vert

    viaColumn = (
        via_cnt * Via1Width
        + (via_cnt - 1) * Via1Space
        + (Via1Width + Via1Space)
        + 0.05
        + m1EncVia1
    )

    if emMet1_height < viaColumn:
        via_cnt -= 1

    c.add_ref(
        gf.components.rectangle(
            size=(
                0.19,
                0.19,
            ),
            layer=layer_via1,
        ),
        rows=via_cnt + 1,
        row_pitch=0.41,
        columns=Nx,
        column_pitch=column_pitch,
    ).move((3.775, 2.87))

    # Draw contacts
    cont_cnt = int(fix((le + 0.21) / (0.16 + 0.18)))

    c.add_ref(
        gf.components.rectangle(
            size=(
                0.16,
                0.12 + le,
            ),
            layer=layer_cont,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((3.79, 3.04))

    c.add_ref(
        gf.components.rectangle(
            size=(
                0.16,
                0.16,
            ),
            layer=layer_cont,
        ),
        rows=cont_cnt + 1,
        row_pitch=0.34,
        columns=Nx,
        column_pitch=column_pitch,
    ).move((2.8, 2.89))

    c.add_ref(
        gf.components.rectangle(
            size=(
                0.16,
                0.16,
            ),
            layer=layer_cont,
        ),
        rows=cont_cnt + 1,
        row_pitch=0.34,
        columns=Nx,
        column_pitch=column_pitch,
    ).move((3.35, 2.89))

    c.add_ref(
        gf.components.rectangle(
            size=(
                0.16,
                0.16,
            ),
            layer=layer_cont,
        ),
        rows=cont_cnt + 1,
        row_pitch=0.34,
        columns=Nx,
        column_pitch=column_pitch,
    ).move((4.23, 2.89))

    c.add_ref(
        gf.components.rectangle(
            size=(
                0.16,
                0.16,
            ),
            layer=layer_cont,
        ),
        rows=cont_cnt + 1,
        row_pitch=0.34,
        columns=Nx,
        column_pitch=column_pitch,
    ).move((4.78, 2.89))

    # Metals
    # Metal Path upwards
    # Collector
    c.add_ref(
        gf.components.rectangle(
            size=(
                Col_Metal1_width,
                4.1 - 2.82 + le,
            ),
            layer=layer_metal1,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x - Col_Metal1_distance - Col_Metal1_width, 2.82))

    c.add_ref(
        gf.components.rectangle(
            size=(
                Col_Metal1_width,
                4.1 - 2.82 + le,
            ),
            layer=layer_metal1,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x + we + Col_Metal1_distance, 2.82))

    c.add_ref(
        gf.components.rectangle(
            size=(
                2 * Col_Metal1_distance + we + 2 * Col_Metal1_width,
                0.65,
            ),
            layer=layer_metal1,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x - Col_Metal1_distance - Col_Metal1_width, 4.1 + le))

    collector_pin_xmin = emWindOrigin_x - Col_Metal1_distance - Col_Metal1_width
    collector_pin_xmax = (
        collector_pin_xmin + 2 * Col_Metal1_distance + we + 2 * Col_Metal1_width
    )
    # The maximum x depends on the number of elements
    collector_pin_xmax += (Nx - 1) * (collector_pin_xmax - collector_pin_xmin)
    collector_pin_ymin = 4.1 + le
    collector_pin_ymax = collector_pin_ymin + 0.65

    c.add_ref(
        gf.components.rectangle(
            size=(
                2 * Col_Metal1_distance + we + 2 * Col_Metal1_width,
                0.65,
            ),
            layer=layer_metal1_pin,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x - Col_Metal1_distance - Col_Metal1_width, 4.1 + le))

    c.add_ref(
        gf.components.rectangle(
            size=(
                Bas_Metal1_width,
                1.28 + le,
            ),
            layer=layer_metal1,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x - Bas_Metal1_distance - Bas_Metal1_width, 2.1))

    c.add_ref(
        gf.components.rectangle(
            size=(
                Bas_Metal1_width,
                1.28 + le,
            ),
            layer=layer_metal1,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x + we + Bas_Metal1_distance, 2.1))

    c.add_ref(
        gf.components.rectangle(
            size=(
                2 * Bas_Metal1_distance + we + 2 * Bas_Metal1_width,
                0.65,
            ),
            layer=layer_metal1,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x - Bas_Metal1_distance - Bas_Metal1_width, 1.45))

    base_pin_xmin = emWindOrigin_x - Bas_Metal1_distance - Bas_Metal1_width
    base_pin_xmax = base_pin_xmin + 2 * Bas_Metal1_distance + we + 2 * Bas_Metal1_width
    # The maximum x depends on the number of elements
    base_pin_xmax += (Nx - 1) * column_pitch
    base_pin_ymin = 1.45
    base_pin_ymax = base_pin_ymin + 0.65

    c.add_ref(
        gf.components.rectangle(
            size=(
                2 * Bas_Metal1_distance + we + 2 * Bas_Metal1_width,
                0.65,
            ),
            layer=layer_metal1_pin,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x - Bas_Metal1_distance - Bas_Metal1_width, 1.45))

    # Emitter
    c.add_ref(
        gf.components.rectangle(
            size=(
                we + 2 * Emi_Metal1_enc_hori,
                le + 2 * Emi_Metal1_enc_vert,
            ),
            layer=layer_metal1,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x - Emi_Metal1_enc_hori, emWindOrigin_y - Emi_Metal1_enc_vert))

    c.add_ref(
        gf.components.rectangle(
            size=(
                we + 2 * Col_Metal1_distance + 2 * Col_Metal1_width,
                le + 0.56,
            ),
            layer=layer_metal2,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x - Col_Metal1_distance - Col_Metal1_width, 2.82))

    emitter_pin_xmin = emWindOrigin_x - Col_Metal1_distance - Col_Metal1_width
    emitter_pin_xmax = (
        emitter_pin_xmin + 2 * Col_Metal1_distance + we + 2 * Col_Metal1_width
    )
    # The maximum x depends on the number of elements
    emitter_pin_xmax += (Nx - 1) * (emitter_pin_xmax - emitter_pin_xmin)
    emitter_pin_ymin = 2.9
    emitter_pin_ymax = emitter_pin_ymin + le + 0.4

    c.add_ref(
        gf.components.rectangle(
            size=(
                we + 2 * Col_Metal1_distance + 2 * Col_Metal1_width,
                le + 0.56,
            ),
            layer=layer_metal2_pin,
        ),
        columns=Nx,
        column_pitch=column_pitch,
    ).move((emWindOrigin_x - Col_Metal1_distance - Col_Metal1_width, 2.82))

    # Draw Guard Ring
    c.add_ref(
        gf.components.rectangle(
            size=(
                5.94 + ((Nx - 1) * 2.34),
                le + 4.4,
            ),
            layer=layer_trans,
        )
    ).move((0.9, 0.9))

    outer = c << gf.components.rectangle(
        size=(
            7.74 + ((Nx - 1) * 2.34),
            le + 6.2,
        ),
        layer=layer_pSD,
    )

    inner = c << gf.components.rectangle(
        size=(
            5.94 + ((Nx - 1) * 2.34),
            le + 4.4,
        ),
        layer=layer_pSD,
    )
    inner.move((0.9, 0.9))

    c.add_ref(
        gf.boolean(
            outer,
            inner,
            operation="not",
            layer=layer_pSD,
            layer1=layer_pSD,
            layer2=layer_pSD,
        )
    )
    # Delete the rectangle that was covering the whole region
    outer.delete()
    # Delete the inner rectangle used for boolean
    inner.delete()

    outer = c << gf.components.rectangle(
        size=(
            7.34 + ((Nx - 1) * 2.34),
            le + 5.8,
        ),
        layer=layer_activ,
    )
    outer.move((0.2, 0.2))
    inner = c << gf.components.rectangle(
        size=(
            6.34 + ((Nx - 1) * 2.34),
            le + 4.8,
        ),
        layer=layer_activ,
    )
    inner.move((0.7, 0.7))
    c.add_ref(
        gf.boolean(
            outer,
            inner,
            operation="not",
            layer=layer_activ,
            layer1=layer_activ,
            layer2=layer_activ,
        )
    )
    # Delete the rectangle that was covering the whole region
    outer.delete()
    # Delete the inner rectangle used for boolean
    inner.delete()

    # Texts
    pcLabelText = f"Ae={int(Nx):d}*{1:d}*{le:.2f}*{we:.2f}"
    c.add_label(text=pcLabelText, layer=layer_text, position=(1.5, 1.0))

    c.add_label(text="npn13G2L", layer=layer_text, position=(1.75, 1.0))

    if Nx > 1:
        c.add_ref(
            gf.components.rectangle(
                size=(
                    1.3,
                    0.65,
                ),
                layer=layer_metal1,
            ),
            columns=Nx - 1,
            column_pitch=column_pitch,
        ).move((4.395, 1.45))
        c.add_ref(
            gf.components.rectangle(
                size=(
                    1.3,
                    0.65,
                ),
                layer=layer_metal1_pin,
            ),
            columns=Nx - 1,
            column_pitch=column_pitch,
        ).move((4.395, 1.45))

    # Ports
    # Collector port
    c.add_port(
        "C",
        center=(
            0.5 * (collector_pin_xmin + collector_pin_xmax),
            0.5 * (collector_pin_ymin + collector_pin_ymax),
        ),
        width=_snap_width_to_grid(collector_pin_ymax - collector_pin_ymin),
        layer=layer_metal1_pin,
        orientation=180.0,
        port_type="electrical",
    )

    c.add_label(
        text="C",
        layer=layer_text,
        position=(
            0.5 * (collector_pin_xmin + collector_pin_xmax),
            0.5 * (collector_pin_ymin + collector_pin_ymax),
        ),
    )

    # Base port
    c.add_port(
        "B",
        center=(
            0.5 * (base_pin_xmin + base_pin_xmax),
            0.5 * (base_pin_ymin + base_pin_ymax),
        ),
        width=_snap_width_to_grid(base_pin_ymax - base_pin_ymin),
        layer=layer_metal1_pin,
        orientation=180.0,
        port_type="electrical",
    )
    c.add_label(
        text="B",
        layer=layer_text,
        position=(
            0.5 * (base_pin_xmin + base_pin_xmax),
            0.5 * (base_pin_ymin + base_pin_ymax),
        ),
    )

    # Emitter port
    c.add_port(
        "E",
        center=(
            0.5 * (emitter_pin_xmin + emitter_pin_xmax),
            0.5 * (emitter_pin_ymin + emitter_pin_ymax),
        ),
        width=_snap_width_to_grid(emitter_pin_ymax - emitter_pin_ymin),
        layer=layer_metal2_pin,
        orientation=180.0,
        port_type="electrical",
    )
    c.add_label(
        text="E",
        layer=layer_text,
        position=(
            0.5 * (emitter_pin_xmin + emitter_pin_xmax),
            0.5 * (emitter_pin_ymin + emitter_pin_ymax),
        ),
    )

    return c


def tog(x: float) -> float:
    SG13_GRID = 0.005
    SG13_EPSILON = 0.001
    SG13_IGRID = 1.0 / SG13_GRID
    return fix(x * SG13_IGRID + SG13_EPSILON) * SG13_GRID


def contactArray(
    c: gf.Component,
    length: float,
    width: float,
    contactLayer: LayerSpec,
    xl: float,
    yl: float,
    ox: float,
    oy: float,
    ws: float,
    ds: float,
) -> None:
    """
    Distributes as many square contact of size ws, into a rectangle of (length, width), with distances >= ds.
    The distances are adjusted so that the outer contacts have fixed distances ox and oy from the sides of the rectangle.

    Args:
        c : gf.Component
            The GDSFactory component on which the array is placed.
        length : float
            Length (x-dimension) of the region which contains the pin array.
        width : float
            Width (y-dimension) of the region which contains the pin array.
        contactLayer : LayerSpec
            Layer on which each square contact rectangle is drawn.
        xl: float
            Minimum x-coordinate of the array that contains the pins.
        yl: float
            Minimum y-coordinate of the array that contains the pins.
        ox: float
            Distance from edge in x direction.
        oy: float
            Distance from edge in y direction.
        ws : float
            Dimension, x and y, of the individual square contact.
        ds: float
            Distance between first column from left edge, last column from right edge, first (bottom) row and bottom edge, and last (top) row and top edge.

    """
    eps = _TECH.epsilon

    nx = math.floor((length - ox * 2 + ds) / (ws + ds) + eps)

    dsx = 0
    if nx == 1:
        dsx = 0
    else:
        dsx = (length - ox * 2 - ws * nx) / (nx - 1)

    ny = math.floor((width - oy * 2 + ds) / (ws + ds) + eps)

    dsy = 0
    if ny == 1:
        dsy = 0
    else:
        dsy = (width - oy * 2 - ws * ny) / (ny - 1)

    x = 0
    if nx == 1:
        x = (length - ws) / 2
    else:
        x = ox

    for _ in range(int(nx)):
        # for(i=1; i<=nx; i++) {
        y = 0
        if ny == 1:
            y = (width - ws) / 2
        else:
            y = oy

        for _ in range(int(ny)):
            # for(j=1; j<=ny; j++) {
            contact_ref = c << gf.components.rectangle(
                size=(ws, ws),
                layer=contactLayer,
            )
            contact_ref.move((tog(x) + xl, tog(y) + yl))

            y = y + ws + dsy

        x = x + ws + dsx


def pnpMPA_schematic(length: float = 2, width: float = 0.7) -> DSchematic:
    s = DSchematic()
    s.info["symbol"] = "pnp"
    s.info["ports"] = [
        {"name": "E", "side": "bottom", "type": "electric"},
        {"name": "B", "side": "left", "type": "electric"},
        {"name": "C", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "implementation": "NgSpice",
            "name": "pnpMPA",
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerHBT.lib",
            "sections": ["hbt_typ", "hbt_bcs", "hbt_wcs"],
            "port_order": ["C", "B", "E"],
            "params": {},
        },
        {
            "language": "spectre",
            "implementation": "VACASK",
            "name": "pnpMPA",
            "spice_type": "SUBCKT",
            "library": "ihp/models/vacask/models/cornerHBT.lib",
            "sections": ["hbt_typ", "hbt_bcs", "hbt_wcs"],
            "port_order": ["C", "B", "E"],
            "params": {},
        },
    ]
    s.create_port(name="C", cross_section=_XS, x=1, y=0, orientation=0)
    s.create_port(name="B", cross_section=_XS, x=-1, y=0, orientation=180)
    s.create_port(name="E", cross_section=_XS, x=0, y=-1, orientation=270)
    return s


@gf.cell(schematic_function=pnpMPA_schematic, tags=["IHP", "bjt", "pnp"])
def pnpMPA(length: float = 2, width: float = 0.7) -> gf.Component:
    """Returns the IHP pnpMPA BJT transistor as a gdsfactory Component.

    This function generates a layout for a PNP transistor using the IHP process.
    The geometry of the transistor is defined by its width and length.

    Args:
        length: Length of the transistor, in microns.
        width: Width of the transistor, in microns.

    Returns:
        gdsfactory.Component: The generated pnpMPA transistor layout.

    Raises:
        ValueError: If width or length is outside allowed range.
    """
    if width < _TECH.pnp_min_width or width > _TECH.pnp_max_width:
        raise ValueError(
            f"pnpMPA width={width} out of range [{_TECH.pnp_min_width}, {_TECH.pnp_max_width}]"
        )
    if length < _TECH.pnp_min_length or length > _TECH.pnp_max_length:
        raise ValueError(
            f"pnpMPA length={length} out of range [{_TECH.pnp_min_length}, {_TECH.pnp_max_length}]"
        )

    c = gf.Component()

    SG13_GRID = _TECH.grid
    SG13_IGRID = 1.0 / SG13_GRID
    epsilon = _TECH.epsilon

    hact = (fix(length * SG13_IGRID + epsilon) * SG13_GRID) * 0.5
    wact = (fix(width * SG13_IGRID + epsilon) * SG13_GRID) * 0.5

    Cnt_a = _TECH.cont_size
    Cnt_b = _TECH.cont_spacing
    Cnt_b1 = _TECH.cont_b1
    M1_c1 = _TECH.m1_endcap
    pSD_c = _TECH.psd_activ_over

    w1m1 = wact - 0.02
    h1m1 = hact - 0.02
    wpsd = wact + 0.21
    hpsd = hact + 0.18
    w2act = wpsd + pSD_c
    h2act = hpsd + pSD_c
    dw2act = max(wact, 0.3)
    dh2act = 0.29
    w2m1 = w2act + 0.02
    h2m1 = h2act + 0.02
    dw2m1 = dw2act - 0.04
    dh2m1 = dh2act - 0.04
    wbulay = w2act + dw2act + 0.05
    hbulay = h2act + dh2act + 0.05
    wnwell = wbulay + 0.26
    hnwell = hbulay + 0.26
    w2psd = wnwell + 0.5
    h2psd = hnwell + 0.5
    d2psd = 0.75
    w3act = w2psd + 0.2
    h3act = h2psd + 0.2
    d3act = 0.35

    activLayer: LayerSpec = "Activdrawing"  # 1
    contLayer: LayerSpec = "Contdrawing"  # 6
    metal1Layer: LayerSpec = "Metal1drawing"  # 8
    metal1_pin_Layer: LayerSpec = "Metal1pin"  # 8
    pSdLayer: LayerSpec = "pSDdrawing"  # 14
    nwellLayer: LayerSpec = "NWelldrawing"  # 31
    nBuLayer: LayerSpec = "nBuLaydrawing"  # 32
    textLayer: LayerSpec = "TEXTdrawing"  # 63

    c.add_ref(
        gf.components.rectangle(size=(2 * wact, 2 * hact), layer=activLayer)
    ).move((-wact, -hact))

    # Labels
    c.add_label(
        text="PLUS",
        layer=textLayer,
    )

    c.add_label(
        text="MINUS",
        layer=textLayer,
        position=(-w2m1 - dw2m1 / 2, 0),
    )

    c.add_label(text="pnpMPA", layer=textLayer, position=(0, -(hnwell + h2psd) / 2))

    c.add_ref(gf.components.rectangle(size=(2 * wpsd, 2 * hpsd), layer=pSdLayer)).move(
        (-wpsd, -hpsd)
    )

    _xl = -w1m1
    _xh = w1m1
    _yl = -h1m1
    _yh = h1m1
    _ox = M1_c1
    _oy = M1_c1
    _ws = Cnt_a
    _ds = Cnt_b
    vg4 = (Cnt_a + Cnt_b) * 4 + Cnt_a + _ox * 2
    if _xh - _xl >= vg4 and _yh - _yl >= vg4:
        _ds = Cnt_b1

    contactArray(
        c,
        length=_xh - _xl,
        width=_yh - _yl,
        contactLayer=contLayer,
        xl=_xl,
        yl=_yl,
        ox=_ox,
        oy=_oy,
        ws=_ws,
        ds=_ds,
    )

    ref1 = c << gf.components.rectangle(size=(2 * w2act, 2 * h2act), layer=activLayer)
    ref1.move((-w2act, -h2act))

    ref2 = c << gf.components.rectangle(
        size=(2 * w2act + 2 * dw2act, 2 * h2act + 2 * dh2act), layer=activLayer
    )
    ref2.move((-w2act - dw2act, -h2act - dh2act))

    c.add_ref(
        gf.boolean(
            ref2,
            ref1,
            operation="xor",
            layer=activLayer,
            layer1=activLayer,
            layer2=activLayer,
        )
    )
    # Delete the rectangle that was covering the whole region
    ref1.delete()
    # Delete the inner rectangle used for boolean
    ref2.delete()

    # Metals
    ref1 = c << gf.components.rectangle(size=(2 * w2m1, 2 * h2m1), layer=metal1Layer)
    ref1.move((-w2m1, -h2m1))

    ref2 = c << gf.components.rectangle(
        size=(2 * w2m1 + 2 * dw2m1, 2 * h2m1 + 2 * dh2m1), layer=metal1Layer
    )
    ref2.move((-w2m1 - dw2m1, -h2m1 - dh2m1))

    c.add_ref(
        gf.boolean(
            ref2,
            ref1,
            operation="xor",
            layer=metal1Layer,
            layer1=metal1Layer,
            layer2=metal1Layer,
        )
    )
    # Delete the rectangle that was covering the whole region
    ref1.delete()
    # Delete the inner rectangle used for boolean
    ref2.delete()

    _xl = -w2m1 - dw2m1
    _xh = -w2m1
    _yl = -h2m1
    _yh = h2m1
    if _xh - _xl >= vg4 and _yh - _yl >= vg4:
        _ds = Cnt_b1

    contactArray(
        c,
        length=_xh - _xl,
        width=_yh - _yl,
        contactLayer=contLayer,
        xl=_xl,
        yl=_yl,
        ox=_ox,
        oy=_oy,
        ws=_ws,
        ds=_ds,
    )
    _xl = w2m1
    _xh = w2m1 + dw2m1
    contactArray(
        c,
        length=_xh - _xl,
        width=_yh - _yl,
        contactLayer=contLayer,
        xl=_xl,
        yl=_yl,
        ox=_ox,
        oy=_oy,
        ws=_ws,
        ds=_ds,
    )

    c.add_ref(
        gf.components.rectangle(size=(2 * wbulay, 2 * hbulay), layer=nBuLayer)
    ).move((-wbulay, -hbulay))

    c.add_ref(
        gf.components.rectangle(size=(2 * wnwell, 2 * hnwell), layer=nwellLayer)
    ).move((-wnwell, -hnwell))

    # Ring
    ref1 = c << gf.components.rectangle(size=(2 * w2psd, 2 * h2psd), layer=pSdLayer)
    ref1.move((-w2psd, -h2psd))

    ref2 = c << gf.components.rectangle(
        size=(2 * w2psd + 2 * d2psd, 2 * h2psd + 2 * d2psd), layer=pSdLayer
    )
    ref2.move((-w2psd - d2psd, -h2psd - d2psd))

    c.add_ref(
        gf.boolean(
            ref2,
            ref1,
            operation="xor",
            layer=pSdLayer,
            layer1=pSdLayer,
            layer2=pSdLayer,
        )
    )
    # Delete the rectangle that was covering the whole region
    ref1.delete()
    # Delete the inner rectangle used for boolean
    ref2.delete()

    ref1 = c << gf.components.rectangle(size=(2 * w3act, 2 * h3act), layer=activLayer)
    ref1.move((-w3act, -h3act))

    ref2 = c << gf.components.rectangle(
        size=(2 * w3act + 2 * d3act, 2 * h3act + 2 * d3act), layer=activLayer
    )
    ref2.move((-w3act - d3act, -h3act - d3act))

    c.add_ref(
        gf.boolean(
            ref2,
            ref1,
            operation="xor",
            layer=activLayer,
            layer1=activLayer,
            layer2=activLayer,
        )
    )
    # Delete the rectangle that was covering the whole region
    ref1.delete()
    # Delete the inner rectangle used for boolean
    ref2.delete()

    ref1 = c << gf.components.rectangle(size=(2 * w3act, 2 * h3act), layer=metal1Layer)
    ref1.move((-w3act, -h3act))

    ref2 = c << gf.components.rectangle(
        size=(2 * w3act + 2 * d3act, 2 * h3act + 2 * d3act), layer=metal1Layer
    )
    ref2.move((-w3act - d3act, -h3act - d3act))

    c.add_ref(
        gf.boolean(
            ref2,
            ref1,
            operation="xor",
            layer=metal1Layer,
            layer1=metal1Layer,
            layer2=metal1Layer,
        )
    )
    # Delete the rectangle that was covering the whole region
    ref1.delete()
    # Delete the inner rectangle used for boolean
    ref2.delete()

    # Ring Metal
    MetT = True  # include pins on top
    MetB = True  # include pins on bottom
    MetL = True  # include pins left
    MetR = True  # include pins right
    _ds = Cnt_b
    _ox = 0.095
    idtie = 0

    if MetT:
        _xl = -w3act - d3act
        _xh = w3act + d3act
        _yl = h3act
        _yh = h3act + d3act
        contactArray(
            c,
            length=_xh - _xl,
            width=_yh - _yl,
            contactLayer=contLayer,
            xl=_xl,
            yl=_yl,
            ox=_ox,
            oy=_oy,
            ws=_ws,
            ds=_ds,
        )
        if idtie == 0:
            # Assigning reference to idtie, so that it is not used again in the next if statements.
            idtie = c << gf.components.rectangle(
                size=(2 * (w3act + d3act), d3act), layer=metal1_pin_Layer
            )
            idtie.move((-w3act - d3act, h3act))

            # Coordinates to be used for port
            idtie_xmin = -w3act - d3act
            idtie_xmax = idtie_xmin + 2 * (w3act + d3act)
            idtie_ymin = h3act
            idtie_ymax = idtie_ymin + d3act

            c.add_label(text="TIE", layer=textLayer, position=(0, h3act + d3act / 2))

    if MetB:
        _xl = -w3act - d3act
        _xh = w3act + d3act
        _yl = -h3act - d3act
        _yh = -h3act
        contactArray(
            c,
            length=_xh - _xl,
            width=_yh - _yl,
            contactLayer=contLayer,
            xl=_xl,
            yl=_yl,
            ox=_ox,
            oy=_oy,
            ws=_ws,
            ds=_ds,
        )
        if idtie == 0:
            idtie = c << gf.components.rectangle(
                size=(2 * (w3act + d3act), d3act), layer=metal1_pin_Layer
            )
            idtie.move((-w3act - d3act, -h3act - d3act))

            # Coordinates to be used for port
            idtie_xmin = -w3act - d3act
            idtie_xmax = idtie_xmin + 2 * (w3act + d3act)
            idtie_ymin = -h3act - d3act
            idtie_ymax = idtie_ymin + d3act

            c.add_label(text="TIE", layer=textLayer, position=(0, -h3act - d3act / 2))

    _oy = 0.085
    if MetL:
        _xl = -w3act - d3act
        _xh = -w3act
        _yl = -h3act
        _yh = h3act
        contactArray(
            c,
            length=_xh - _xl,
            width=_yh - _yl,
            contactLayer=contLayer,
            xl=_xl,
            yl=_yl,
            ox=_ox,
            oy=_oy,
            ws=_ws,
            ds=_ds,
        )
        if idtie == 0:
            idtie = c << gf.components.rectangle(
                size=(d3act, 2 * h3act), layer=metal1_pin_Layer
            )
            idtie.move((-w3act - d3act, -h3act))

            # Coordinates to be used for port
            idtie_xmin = -w3act - d3act
            idtie_xmax = idtie_xmin + d3act
            idtie_ymin = -h3act
            idtie_ymax = idtie_ymin + 2 * h3act

            c.add_label(text="TIE", layer=textLayer, position=(-w3act - d3act / 2, 0))

    if MetR:
        _xl = w3act
        _xh = w3act + d3act
        _yl = -h3act
        _yh = h3act
        contactArray(
            c,
            length=_xh - _xl,
            width=_yh - _yl,
            contactLayer=contLayer,
            xl=_xl,
            yl=_yl,
            ox=_ox,
            oy=_oy,
            ws=_ws,
            ds=_ds,
        )
        if idtie == 0:
            idtie = c << gf.components.rectangle(
                size=(d3act, 2 * h3act), layer=metal1_pin_Layer
            )
            idtie.move((w3act, -h3act))

            # Coordinates to be used for port
            idtie_xmin = w3act
            idtie_xmax = idtie_xmin + d3act
            idtie_ymin = -h3act
            idtie_ymax = idtie_ymin + 2 * h3act

            c.add_label(text="TIE", layer=textLayer, position=(w3act + d3act / 2, 0))

    c.add_ref(
        gf.components.rectangle(size=(2 * w1m1, 2 * h1m1), layer=metal1_pin_Layer)
    ).move((-w1m1, -h1m1))

    c.add_ref(
        gf.components.rectangle(size=(2 * w1m1, 2 * h1m1), layer=metal1Layer)
    ).move((-w1m1, -h1m1))

    c.add_ref(
        gf.components.rectangle(size=(dw2m1, 2 * h2m1), layer=metal1_pin_Layer)
    ).move((-w2m1 - dw2m1, -h2m1))

    if idtie != 0:
        c.add_port(
            "TIE",
            center=(0.5 * (idtie_xmin + idtie_xmax), 0.5 * (idtie_ymin + idtie_ymax)),
            width=_snap_width_to_grid(idtie_ymax - idtie_ymin),
            layer=metal1_pin_Layer,
            orientation=180.0,
            port_type="electrical",
        )

    c.add_port(
        "PLUS",
        center=(0, 0),
        width=_snap_width_to_grid(2 * w1m1),
        layer=metal1_pin_Layer,
        orientation=270.0,
        port_type="electrical",
    )

    c.add_port(
        "MINUS",
        center=(-w2m1 - dw2m1 / 2, 0),
        width=_snap_width_to_grid(dw2m1),
        layer=metal1_pin_Layer,
        orientation=270.0,
        port_type="electrical",
    )

    return c
