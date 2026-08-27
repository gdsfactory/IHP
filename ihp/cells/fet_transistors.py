"""FET transistor components for IHP PDK.

Pure GDSFactory implementations that replicate the geometry from the IHP PyCell
library (cells2/ihp_pycell). The layout algorithm follows the PyCell construction
exactly: left-to-right sequential placement of source contacts, gate poly, drain
contacts, with design rules from the CNI tech parameters.

Shared helper functions and constants used by both FET and RF transistor modules
are defined here.
"""

import math

import gdsfactory as gf
from gdsfactory import Component
from gdsfactory.typings import LayerSpec
from kfactory.schematic import DSchematic

from ..tech import TECH

_XS = "metal1_routing"


# ---------------------------------------------------------------------------
# Helper functions matching PyCell utility_functions.py
# ---------------------------------------------------------------------------
def _fix(value):
    """Floor for floats (matches PyCell fix())."""
    if isinstance(value, float):
        return int(math.floor(value))
    return value


def _grid_fix(x: float) -> float:
    """Snap to manufacturing grid (matches PyCell GridFix/tog/Snap)."""
    return _fix(x * (1.0 / TECH.grid) + TECH.epsilon) * TECH.grid


def _add_rect(
    c: Component, layer: LayerSpec, x1: float, y1: float, x2: float, y2: float
):
    """Add a rectangle directly as a polygon (no sub-cell hierarchy).

    Using add_polygon avoids sub-cell + transform indirection that can
    introduce 1-dbu rounding mismatches during hierarchy flattening.
    """
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1
    if x2 - x1 <= 0 or y2 - y1 <= 0:
        return
    c.add_polygon([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], layer=layer)


def _place_contacts(
    c: Component,
    layer_cont: LayerSpec,
    xl: float,
    yl: float,
    xh: float,
    yh: float,
    ox: float,
    oy: float,
    ws: float,
    ds: float,
):
    """Place contact array matching PyCell contactArray() from geometry.py.

    Args:
        c: Component to add contacts to.
        layer_cont: Contact layer.
        xl: X coordinate of the lower-left corner of the bounding box (um).
        yl: Y coordinate of the lower-left corner of the bounding box (um).
        xh: X coordinate of the upper-right corner of the bounding box (um).
        yh: Y coordinate of the upper-right corner of the bounding box (um).
        ox: X-direction enclosure (0 for transistor S/D contacts).
        oy: Y-direction enclosure (cont_Activ_overRec for transistor S/D).
        ws: Contact size.
        ds: Contact spacing.
    """
    w = xh - xl
    h = yh - yl

    nx = _fix((w - ox * 2 + ds) / (ws + ds) + TECH.epsilon)
    if nx <= 0:
        return

    if nx == 1:
        dsx = 0.0
    else:
        dsx = (w - ox * 2 - ws * nx) / (nx - 1)

    ny = _fix((h - oy * 2 + ds) / (ws + ds) + TECH.epsilon)
    if ny <= 0:
        return

    if ny == 1:
        dsy = 0.0
    else:
        dsy = (h - oy * 2 - ws * ny) / (ny - 1)

    if nx == 1:
        x_start = (w - ws) / 2
    else:
        x_start = ox

    for _i in range(int(nx)):
        if ny == 1:
            y = (h - ws) / 2
        else:
            y = oy

        for _j in range(int(ny)):
            cx = _grid_fix(xl + x_start)
            cy = _grid_fix(yl + y)
            _add_rect(
                c,
                layer_cont,
                cx,
                cy,
                _grid_fix(xl + x_start + ws),
                _grid_fix(yl + y + ws),
            )
            y += ws + dsy

        x_start += ws + dsx


def _even_dbu(w):
    """Round width to even multiples of dbu (0.002 um) per kfactory."""
    dbu_w = round(w / 0.001)
    return (dbu_w + dbu_w % 2) * 0.001


# ---------------------------------------------------------------------------
# Core MOS layout engine
# ---------------------------------------------------------------------------
def _mos_core(
    width: float,
    length: float,
    nf: int,
    is_pmos: bool = False,
    is_hv: bool = False,
    layer_gatpoly: LayerSpec = "GatPolydrawing",
    layer_activ: LayerSpec = "Activdrawing",
    layer_cont: LayerSpec = "Contdrawing",
    layer_metal1: LayerSpec = "Metal1drawing",
    layer_psd: LayerSpec = "pSDdrawing",
    layer_nwell: LayerSpec = "NWelldrawing",
    layer_thickgateox: LayerSpec = "ThickGateOxdrawing",
    layer_heattrans: LayerSpec = "HeatTransdrawing",
    layer_substrate: LayerSpec = "Substratedrawing",
    layer_metal1_pin: LayerSpec = "Metal1pin",
    layer_gatpoly_pin: LayerSpec = "GatPolypin",
) -> Component:
    """Core MOS transistor layout matching IHP PyCell geometry.

    Constructs layout left-to-right: source contacts -> gate poly -> drain contacts.
    Exactly replicates nmos_code.py / pmos_code.py / nmosHV_code.py / pmosHV_code.py.
    """
    c = Component()

    # Tech params
    epsilon = TECH.epsilon
    endcap = TECH.m1_endcap
    cont_size = TECH.cont_size
    cont_dist = TECH.cont_spacing
    cont_Activ_overRec = TECH.cont_enc_active
    cont_metall_over = TECH.m1_over
    gatpoly_Activ_over = TECH.gatpoly_activ_over
    gatpoly_cont_dist = TECH.cont_gate_dist
    smallw_gatpoly_cont_dist = TECH.cont_enc_active + TECH.gat_d
    contActMin = 2 * TECH.cont_enc_active + TECH.cont_size

    # PMOS-specific params
    if is_pmos:
        psd_pActiv_over = TECH.psd_activ_over
        psd_PFET_over = TECH.psd_gate_over_hv if is_hv else TECH.psd_gate_over_lv
        nwell_pActiv_over = TECH.nw_activ_over_hv if is_hv else TECH.nw_activ_over_lv

    # HV params
    thGateOxGat = TECH.tgo_gatpoly
    thGateOxAct = TECH.tgo_activ

    # Endcap adjustment
    if endcap < cont_metall_over:
        endcap = cont_metall_over

    # Process dimensions
    ng = _fix(nf + epsilon)
    w = width / ng
    w = _grid_fix(w)
    gate_length = _grid_fix(length)

    # Narrow-width gate-contact spacing adjustment
    if w < contActMin - epsilon:
        gatpoly_cont_dist = smallw_gatpoly_cont_dist

    xdiff_beg = 0.0
    ydiff_beg = 0.0
    ydiff_end = w

    diffoffset = 0.0
    if w < contActMin:
        diffoffset = (contActMin - w) / 2
        diffoffset = _grid_fix(diffoffset)

    # Number of contacts (differs between nmos and pmos)
    distc = cont_size + cont_dist
    if is_pmos:
        # pmos formula: subtracts 2*endcap from lcon
        lcon = w - 2 * cont_Activ_overRec
        ncont = _fix((lcon + cont_dist - 2 * endcap) / distc + epsilon)
    else:
        # nmos formula
        ncont = _fix(
            (w - 2 * cont_Activ_overRec + cont_dist) / (cont_size + cont_dist) + epsilon
        )

    if ncont == 0:
        ncont = 1

    diff_cont_offset = _grid_fix(
        (w - 2 * cont_Activ_overRec - ncont * cont_size - (ncont - 1) * cont_dist) / 2
    )

    # -----------------------------------------------------------------------
    # Source contact column (first S/D region)
    # -----------------------------------------------------------------------
    xcont_beg = xdiff_beg + cont_Activ_overRec
    ycont_beg = ydiff_beg + cont_Activ_overRec
    ycont_cnt = ycont_beg + diffoffset + diff_cont_offset
    xcont_end = xcont_beg + cont_size

    # Metal1 Y extents (computed once, reused for all S/D columns)
    yMet1 = ycont_cnt - endcap
    yMet2 = ycont_cnt + cont_size + (ncont - 1) * distc + endcap
    yMet1 = min(yMet1, ydiff_beg + diffoffset)
    yMet2 = max(yMet2, ydiff_end + diffoffset)

    # Source Metal1
    _add_rect(
        c,
        layer_metal1,
        xcont_beg - cont_metall_over,
        yMet1,
        xcont_end + cont_metall_over,
        yMet2,
    )

    # Source contacts
    _place_contacts(
        c,
        layer_cont,
        xcont_beg,
        ydiff_beg,
        xcont_end,
        ydiff_end + diffoffset * 2,
        0,
        cont_Activ_overRec,
        cont_size,
        cont_dist,
    )

    # Pin sublayer for pin markers and ports.
    pin_layer_m1 = layer_metal1_pin
    pin_layer_poly = layer_gatpoly_pin

    # Source pin marker
    _add_rect(
        c,
        pin_layer_m1,
        xcont_beg - cont_metall_over,
        yMet1,
        xcont_end + cont_metall_over,
        yMet2,
    )

    # Save source port location
    src_x = (xcont_beg - cont_metall_over + xcont_end + cont_metall_over) / 2
    src_y = (yMet1 + yMet2) / 2
    port_height = yMet2 - yMet1

    # Source diffusion (Activ)
    _add_rect(
        c,
        layer_activ,
        xcont_beg - cont_Activ_overRec,
        ycont_beg - cont_Activ_overRec,
        xcont_end + cont_Activ_overRec,
        ycont_beg + cont_size + cont_Activ_overRec,
    )

    # -----------------------------------------------------------------------
    # Gate fingers loop
    # -----------------------------------------------------------------------
    gate_x = gate_y = drain_x = drain_y = gate_height = 0.0
    for i in range(1, ng + 1):
        # Poly gate
        xpoly_beg = xcont_end + gatpoly_cont_dist
        ypoly_beg = ydiff_beg - gatpoly_Activ_over
        xpoly_end = xpoly_beg + gate_length
        ypoly_end = ydiff_end + gatpoly_Activ_over

        _add_rect(
            c,
            layer_gatpoly,
            xpoly_beg,
            ypoly_beg + diffoffset,
            xpoly_end,
            ypoly_end + diffoffset,
        )

        # HeatTrans layer (thermal marker)
        _add_rect(
            c,
            layer_heattrans,
            xpoly_beg,
            ypoly_beg + diffoffset,
            xpoly_end,
            ypoly_end + diffoffset,
        )

        # Gate pin (first finger only, matching onep(i) check)
        if i == 1:
            _add_rect(
                c,
                pin_layer_poly,
                xpoly_beg,
                ypoly_beg + diffoffset,
                xpoly_end,
                ypoly_end + diffoffset,
            )
            gate_x = (xpoly_beg + xpoly_end) / 2
            gate_y = (ypoly_beg + ypoly_end) / 2 + diffoffset
            gate_height = ypoly_end - ypoly_beg

        # Drain/next-source contact column
        xcont_beg = xpoly_end + gatpoly_cont_dist
        ycont_beg = ydiff_beg + cont_Activ_overRec
        ycont_cnt = ycont_beg + diffoffset + diff_cont_offset
        xcont_end = xcont_beg + cont_size

        # Metal1 for this S/D column
        _add_rect(
            c,
            layer_metal1,
            xcont_beg - cont_metall_over,
            yMet1,
            xcont_end + cont_metall_over,
            yMet2,
        )

        # Contacts for this S/D column
        _place_contacts(
            c,
            layer_cont,
            xcont_beg,
            ydiff_beg,
            xcont_end,
            ydiff_end + diffoffset * 2,
            0,
            cont_Activ_overRec,
            cont_size,
            cont_dist,
        )

        # Drain pin (first finger only)
        if i == 1:
            _add_rect(
                c,
                pin_layer_m1,
                xcont_beg - cont_metall_over,
                yMet1,
                xcont_end + cont_metall_over,
                yMet2,
            )
            drain_x = (xcont_beg - cont_metall_over + xcont_end + cont_metall_over) / 2
            drain_y = src_y

        # Drain/source diffusion (Activ)
        _add_rect(
            c,
            layer_activ,
            xcont_beg - cont_Activ_overRec,
            ycont_beg - cont_Activ_overRec,
            xcont_end + cont_Activ_overRec,
            ycont_beg + cont_size + cont_Activ_overRec,
        )

    # -----------------------------------------------------------------------
    # Spanning diffusion rectangle
    # -----------------------------------------------------------------------
    xdiff_end = xcont_end + cont_Activ_overRec
    _add_rect(
        c,
        layer_activ,
        xdiff_beg,
        ydiff_beg + diffoffset,
        xdiff_end,
        ydiff_end + diffoffset,
    )

    # -----------------------------------------------------------------------
    # PMOS: pSD and NWell layers
    # -----------------------------------------------------------------------
    if is_pmos:
        # pSD layer
        _add_rect(
            c,
            layer_psd,
            xdiff_beg - psd_pActiv_over,
            ypoly_beg - psd_PFET_over + gatpoly_Activ_over + diffoffset,
            xdiff_end + psd_pActiv_over,
            ypoly_end + psd_PFET_over - gatpoly_Activ_over + diffoffset,
        )

        # NWell layer with minimum-width offset
        # PyCell uses self.grid = tech.getGridResolution() which is 0.0 for SG13
        _grid_res = 0.0  # tech.getGridResolution()
        nwell_offset = max(0, _grid_fix((contActMin - w) / 2 + 0.5 * _grid_res))
        _add_rect(
            c,
            layer_nwell,
            xdiff_beg - nwell_pActiv_over,
            ydiff_beg - nwell_pActiv_over + diffoffset - nwell_offset,
            xdiff_end + nwell_pActiv_over,
            ydiff_end + nwell_pActiv_over + diffoffset + nwell_offset,
        )

    # -----------------------------------------------------------------------
    # B-Pin on Substrate (pmos only)
    # -----------------------------------------------------------------------
    if is_pmos:
        _add_rect(
            c,
            layer_substrate,
            xcont_beg - cont_Activ_overRec,
            ycont_beg - cont_Activ_overRec,
            xcont_end + cont_Activ_overRec,
            ycont_beg + cont_size + cont_Activ_overRec,
        )

    # -----------------------------------------------------------------------
    # HV: ThickGateOx layer
    # -----------------------------------------------------------------------
    if is_hv:
        if is_pmos:
            # pmosHV: check if NWell is bigger than standard TGO enclosure
            x1 = xdiff_beg - thGateOxAct
            x2 = xdiff_end + thGateOxAct
            y1 = ydiff_beg - gatpoly_Activ_over - thGateOxGat
            y2 = ydiff_end + gatpoly_Activ_over + thGateOxGat

            nwell_offset_tgo = max(0, _grid_fix((contActMin - w) / 2 + 0.5 * _grid_res))
            if nwell_pActiv_over > thGateOxAct:
                x1 = xdiff_beg - nwell_pActiv_over
                x2 = xdiff_end + nwell_pActiv_over
            if (nwell_pActiv_over + diffoffset - nwell_offset_tgo) > (
                gatpoly_Activ_over - thGateOxGat
            ):
                y1 = ydiff_beg - nwell_pActiv_over + diffoffset - nwell_offset_tgo
                y2 = ydiff_end + nwell_pActiv_over + diffoffset + nwell_offset_tgo

            _add_rect(c, layer_thickgateox, x1, y1, x2, y2)
        else:
            # nmosHV: standard TGO enclosure
            _add_rect(
                c,
                layer_thickgateox,
                xdiff_beg - thGateOxAct,
                ydiff_beg - gatpoly_Activ_over - thGateOxGat,
                xdiff_end + thGateOxAct,
                ydiff_end + gatpoly_Activ_over + thGateOxGat,
            )

    # -----------------------------------------------------------------------
    # GDSFactory ports for netlisting (S, D, G)
    # Port widths must be even multiples of dbu (0.002 um) per kfactory.
    # -----------------------------------------------------------------------
    c.add_port(
        name="S",
        center=(src_x, src_y),
        width=_even_dbu(port_height),
        orientation=180,
        layer=layer_metal1_pin,
        port_type="electrical",
    )
    c.add_port(
        name="D",
        center=(drain_x, drain_y),
        width=_even_dbu(port_height),
        orientation=0,
        layer=layer_metal1_pin,
        port_type="electrical",
    )
    c.add_port(
        name="G",
        center=(gate_x, gate_y),
        width=_even_dbu(gate_height),
        orientation=270,
        layer=layer_gatpoly_pin,
        port_type="electrical",
    )

    return c


# ---------------------------------------------------------------------------
# Public cell functions
# ---------------------------------------------------------------------------
def nmos_schematic(
    width: float = 0.15,
    length: float = 0.13,
    nf: int = 1,
    m: int = 1,
) -> DSchematic:
    s = DSchematic()
    s.info["symbol"] = "nmos"
    s.info["ports"] = [
        {"name": "D", "side": "top", "type": "electric"},
        {"name": "S", "side": "bottom", "type": "electric"},
        {"name": "G", "side": "left", "type": "electric"},
        {"name": "B", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "implementation": "NgSpice",
            "name": "sg13_lv_nmos",
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerMOSlv.lib",
            "sections": ["mos_tt", "mos_ss", "mos_ff", "mos_sf", "mos_fs"],
            "port_order": ["D", "G", "S", "B"],
            "params": {
                "w": "width * 1e-6",
                "l": "length * 1e-6",
                "ng": "nf",
                "m": "m",
            },
        },
        {
            "language": "spectre",
            "implementation": "VACASK",
            "name": "sg13_lv_nmos",
            "spice_type": "SUBCKT",
            "library": "ihp/models/vacask/models/cornerMOSlv.lib",
            "sections": ["mos_tt", "mos_ss", "mos_ff", "mos_sf", "mos_fs"],
            "port_order": ["D", "G", "S", "B"],
            "params": {
                "w": "width * 1e-6",
                "l": "length * 1e-6",
                "ng": "nf",
                "m": "m",
            },
        },
    ]
    s.create_port(name="D", cross_section=_XS, x=0, y=1, orientation=90)
    s.create_port(name="G", cross_section=_XS, x=-1, y=0, orientation=180)
    s.create_port(name="S", cross_section=_XS, x=0, y=-1, orientation=270)
    s.create_port(name="B", cross_section=_XS, x=1, y=0, orientation=0)
    return s


@gf.cell(schematic_function=nmos_schematic, tags=["IHP", "mos", "lv"])
def nmos(
    width: float = 0.15,
    length: float = 0.13,
    nf: int = 1,
    m: int = 1,
    model: str = "sg13_lv_nmos",
) -> Component:
    """Create an NMOS transistor.

    Args:
        width: Total width of the transistor in micrometers.
        length: Gate length in micrometers.
        nf: Number of fingers.
        m: Multiplier (number of parallel devices).
        model: Device model name.

    Returns:
        Component with NMOS transistor layout.

    Raises:
        ValueError: If width, length, or nf is outside allowed range.
    """
    if length < TECH.nmos_min_length or length > TECH.nmos_max_length:
        raise ValueError(
            f"nmos length={length} out of range [{TECH.nmos_min_length}, {TECH.nmos_max_length}]"
        )
    if nf < 1 or nf > TECH.nmos_max_nf:
        raise ValueError(f"nmos nf={nf} out of range [1, {TECH.nmos_max_nf}]")
    if width < TECH.nmos_min_width or width > TECH.nmos_max_width:
        raise ValueError(
            f"nmos width={width} out of range [{TECH.nmos_min_width}, {TECH.nmos_max_width}]"
        )

    c = _mos_core(width, length, nf, is_pmos=False, is_hv=False)
    return c


def pmos_schematic(
    width: float = 0.15,
    length: float = 0.13,
    nf: int = 1,
    m: int = 1,
) -> DSchematic:
    s = DSchematic()
    s.info["symbol"] = "pmos"
    s.info["ports"] = [
        {"name": "D", "side": "top", "type": "electric"},
        {"name": "S", "side": "bottom", "type": "electric"},
        {"name": "G", "side": "left", "type": "electric"},
        {"name": "B", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "implementation": "NgSpice",
            "name": "sg13_lv_pmos",
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerMOSlv.lib",
            "sections": ["mos_tt", "mos_ss", "mos_ff", "mos_sf", "mos_fs"],
            "port_order": ["D", "G", "S", "B"],
            "params": {"w": "width * 1e-6", "l": "length * 1e-6", "ng": "nf", "m": "m"},
        },
        {
            "language": "spectre",
            "implementation": "VACASK",
            "name": "sg13_lv_pmos",
            "spice_type": "SUBCKT",
            "library": "ihp/models/vacask/models/cornerMOSlv.lib",
            "sections": ["mos_tt", "mos_ss", "mos_ff", "mos_sf", "mos_fs"],
            "port_order": ["D", "G", "S", "B"],
            "params": {"w": "width * 1e-6", "l": "length * 1e-6", "ng": "nf", "m": "m"},
        },
    ]
    s.create_port(name="D", cross_section=_XS, x=0, y=1, orientation=90)
    s.create_port(name="G", cross_section=_XS, x=-1, y=0, orientation=180)
    s.create_port(name="S", cross_section=_XS, x=0, y=-1, orientation=270)
    s.create_port(name="B", cross_section=_XS, x=1, y=0, orientation=0)
    return s


@gf.cell(schematic_function=pmos_schematic, tags=["IHP", "mos", "lv"])
def pmos(
    width: float = 0.15,
    length: float = 0.13,
    nf: int = 1,
    m: int = 1,
    model: str = "sg13_lv_pmos",
) -> Component:
    """Create a PMOS transistor.

    Args:
        width: Total width of the transistor in micrometers.
        length: Gate length in micrometers.
        nf: Number of fingers.
        m: Multiplier (number of parallel devices).
        model: Device model name.

    Returns:
        Component with PMOS transistor layout.

    Raises:
        ValueError: If width, length, or nf is outside allowed range.
    """
    if width < TECH.pmos_min_width or width > TECH.pmos_max_width:
        raise ValueError(
            f"pmos width={width} out of range [{TECH.pmos_min_width}, {TECH.pmos_max_width}]"
        )
    if length < TECH.pmos_min_length or length > TECH.pmos_max_length:
        raise ValueError(
            f"pmos length={length} out of range [{TECH.pmos_min_length}, {TECH.pmos_max_length}]"
        )
    if nf < 1 or nf > TECH.pmos_max_nf:
        raise ValueError(f"pmos nf={nf} out of range [1, {TECH.pmos_max_nf}]")

    c = _mos_core(width, length, nf, is_pmos=True, is_hv=False)
    return c


def nmos_hv_schematic(
    width: float = 0.60,
    length: float = 0.45,
    nf: int = 1,
    m: int = 1,
) -> DSchematic:
    s = DSchematic()
    s.info["symbol"] = "nmos"
    s.info["ports"] = [
        {"name": "D", "side": "top", "type": "electric"},
        {"name": "S", "side": "bottom", "type": "electric"},
        {"name": "G", "side": "left", "type": "electric"},
        {"name": "B", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "implementation": "NgSpice",
            "name": "sg13_hv_nmos",
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerMOShv.lib",
            "sections": ["mos_tt", "mos_ss", "mos_ff", "mos_sf", "mos_fs"],
            "port_order": ["D", "G", "S", "B"],
            "params": {"w": "width * 1e-6", "l": "length * 1e-6", "ng": "nf", "m": "m"},
        },
        {
            "language": "spectre",
            "implementation": "VACASK",
            "name": "sg13_hv_nmos",
            "spice_type": "SUBCKT",
            "library": "ihp/models/vacask/models/cornerMOShv.lib",
            "sections": ["mos_tt", "mos_ss", "mos_ff", "mos_sf", "mos_fs"],
            "port_order": ["D", "G", "S", "B"],
            "params": {"w": "width * 1e-6", "l": "length * 1e-6", "ng": "nf", "m": "m"},
        },
    ]
    s.create_port(name="D", cross_section=_XS, x=0, y=1, orientation=90)
    s.create_port(name="G", cross_section=_XS, x=-1, y=0, orientation=180)
    s.create_port(name="S", cross_section=_XS, x=0, y=-1, orientation=270)
    s.create_port(name="B", cross_section=_XS, x=1, y=0, orientation=0)
    return s


@gf.cell(schematic_function=nmos_hv_schematic, tags=["IHP", "mos", "hv"])
def nmos_hv(
    width: float = 0.60,
    length: float = 0.45,
    nf: int = 1,
    m: int = 1,
    model: str = "sg13_hv_nmos",
) -> Component:
    """Create a high-voltage NMOS transistor.

    Args:
        width: Total width of the transistor in micrometers.
        length: Gate length in micrometers.
        nf: Number of fingers.
        m: Multiplier (number of parallel devices).
        model: Device model name.

    Returns:
        Component with HV NMOS transistor layout.

    Raises:
        ValueError: If width, length, or nf is outside allowed range.
    """
    if width < TECH.nmos_hv_min_width or width > TECH.nmos_hv_max_width:
        raise ValueError(
            f"nmos_hv width={width} out of range [{TECH.nmos_hv_min_width}, {TECH.nmos_hv_max_width}]"
        )
    if length < TECH.nmos_hv_min_length or length > TECH.nmos_hv_max_length:
        raise ValueError(
            f"nmos_hv length={length} out of range [{TECH.nmos_hv_min_length}, {TECH.nmos_hv_max_length}]"
        )
    if nf < 1 or nf > TECH.nmos_hv_max_nf:
        raise ValueError(f"nmos_hv nf={nf} out of range [1, {TECH.nmos_hv_max_nf}]")

    c = _mos_core(width, length, nf, is_pmos=False, is_hv=True)
    return c


def pmos_hv_schematic(
    width: float = 0.30,
    length: float = 0.40,
    nf: int = 1,
    m: int = 1,
) -> DSchematic:
    s = DSchematic()
    s.info["symbol"] = "pmos"
    s.info["ports"] = [
        {"name": "D", "side": "top", "type": "electric"},
        {"name": "S", "side": "bottom", "type": "electric"},
        {"name": "G", "side": "left", "type": "electric"},
        {"name": "B", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "implementation": "NgSpice",
            "name": "sg13_hv_pmos",
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerMOShv.lib",
            "sections": ["mos_tt", "mos_ss", "mos_ff", "mos_sf", "mos_fs"],
            "port_order": ["D", "G", "S", "B"],
            "params": {"w": "width * 1e-6", "l": "length * 1e-6", "ng": "nf", "m": "m"},
        },
        {
            "language": "spectre",
            "implementation": "VACASK",
            "name": "sg13_hv_pmos",
            "spice_type": "SUBCKT",
            "library": "ihp/models/vacask/models/cornerMOShv.lib",
            "sections": ["mos_tt", "mos_ss", "mos_ff", "mos_sf", "mos_fs"],
            "port_order": ["D", "G", "S", "B"],
            "params": {"w": "width * 1e-6", "l": "length * 1e-6", "ng": "nf", "m": "m"},
        },
    ]
    s.create_port(name="D", cross_section=_XS, x=0, y=1, orientation=90)
    s.create_port(name="G", cross_section=_XS, x=-1, y=0, orientation=180)
    s.create_port(name="S", cross_section=_XS, x=0, y=-1, orientation=270)
    s.create_port(name="B", cross_section=_XS, x=1, y=0, orientation=0)
    return s


@gf.cell(schematic_function=pmos_hv_schematic, tags=["IHP", "mos", "hv"])
def pmos_hv(
    width: float = 0.30,
    length: float = 0.40,
    nf: int = 1,
    m: int = 1,
    model: str = "sg13_hv_pmos",
) -> Component:
    """Create a high-voltage PMOS transistor.

    Args:
        width: Total width of the transistor in micrometers.
        length: Gate length in micrometers.
        nf: Number of fingers.
        m: Multiplier (number of parallel devices).
        model: Device model name.

    Returns:
        Component with HV PMOS transistor layout.

    Raises:
        ValueError: If width, length, or nf is outside allowed range.
    """
    if width < TECH.pmos_hv_min_width or width > TECH.pmos_hv_max_width:
        raise ValueError(
            f"pmos_hv width={width} out of range [{TECH.pmos_hv_min_width}, {TECH.pmos_hv_max_width}]"
        )
    if length < TECH.pmos_hv_min_length or length > TECH.pmos_hv_max_length:
        raise ValueError(
            f"pmos_hv length={length} out of range [{TECH.pmos_hv_min_length}, {TECH.pmos_hv_max_length}]"
        )
    if nf < 1 or nf > TECH.pmos_hv_max_nf:
        raise ValueError(f"pmos_hv nf={nf} out of range [1, {TECH.pmos_hv_max_nf}]")

    c = _mos_core(width, length, nf, is_pmos=True, is_hv=True)
    return c
