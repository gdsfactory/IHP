"""Transistor components for IHP PDK.

Pure GDSFactory implementations that replicate the geometry from the IHP PyCell
library (cells2/ihp_pycell). The layout algorithm follows the PyCell construction
exactly: left-to-right sequential placement of source contacts, gate poly, drain
contacts, with design rules from the CNI tech parameters.
"""

import math

import gdsfactory as gf
from gdsfactory import Component
from gdsfactory.typings import LayerSpec

from ..tech import techParams as _tech

# ---------------------------------------------------------------------------
# Design rule constants from tech params
# ---------------------------------------------------------------------------
_EPSILON = _tech["epsilon1"]  # 0.001
_GRID = _tech["grid"]  # 0.005
_IGRID = 1.0 / _GRID  # 200

_CONT_SIZE = _tech["Cnt_a"]  # 0.16  contact square size
_CONT_DIST = _tech["Cnt_b"]  # 0.18  contact spacing
_CONT_ACTIV_OVER = _tech["Cnt_c"]  # 0.07  contact enclosure by active
_CONT_GATE_DIST = _tech["Cnt_f"]  # 0.11  gate poly to contact spacing
_CONT_GATE_DIST_SMALL = _CONT_ACTIV_OVER + _tech["Gat_d"]  # 0.14

_M1_OVER = _tech["M1_c"]  # 0.0  metal1 enclosure of contact
_M1_ENDCAP = _tech["M1_c1"]  # 0.05  metal1 endcap beyond contacts

_GATPOLY_ACTIV_OVER = _tech["Gat_c"]  # 0.18  poly extension over active

_CONT_ACT_MIN = 2 * _CONT_ACTIV_OVER + _CONT_SIZE  # 0.30

_PSD_ACTIV_OVER = _tech["pSD_c"]  # 0.18
_PSD_GATE_OVER_LV = _tech["pSD_i"]  # 0.3
_PSD_GATE_OVER_HV = _tech["pSD_i1"]  # 0.4
_NW_ACTIV_OVER_LV = _tech["NW_c"]  # 0.31
_NW_ACTIV_OVER_HV = _tech["NW_c1"]  # 0.62
_TGO_ACTIV = _tech["TGO_a"]  # 0.27
_TGO_GATPOLY = _tech["TGO_c"]  # 0.34


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
    return _fix(x * _IGRID + _EPSILON) * _GRID


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
        xl, yl: Lower-left of bounding box.
        xh, yh: Upper-right of bounding box.
        ox: X-direction enclosure (0 for transistor S/D contacts).
        oy: Y-direction enclosure (cont_Activ_overRec for transistor S/D).
        ws: Contact size.
        ds: Contact spacing.
    """
    w = xh - xl
    h = yh - yl

    nx = _fix((w - ox * 2 + ds) / (ws + ds) + _EPSILON)
    if nx <= 0:
        return

    if nx == 1:
        dsx = 0.0
    else:
        dsx = (w - ox * 2 - ws * nx) / (nx - 1)

    ny = _fix((h - oy * 2 + ds) / (ws + ds) + _EPSILON)
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
    epsilon = _EPSILON
    endcap = _M1_ENDCAP
    cont_size = _CONT_SIZE
    cont_dist = _CONT_DIST
    cont_Activ_overRec = _CONT_ACTIV_OVER
    cont_metall_over = _M1_OVER
    gatpoly_Activ_over = _GATPOLY_ACTIV_OVER
    gatpoly_cont_dist = _CONT_GATE_DIST
    smallw_gatpoly_cont_dist = _CONT_GATE_DIST_SMALL
    contActMin = _CONT_ACT_MIN

    # PMOS-specific params
    if is_pmos:
        psd_pActiv_over = _PSD_ACTIV_OVER
        psd_PFET_over = _PSD_GATE_OVER_HV if is_hv else _PSD_GATE_OVER_LV
        nwell_pActiv_over = _NW_ACTIV_OVER_HV if is_hv else _NW_ACTIV_OVER_LV

    # HV params
    thGateOxGat = _TGO_GATPOLY
    thGateOxAct = _TGO_ACTIV

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

    # Pin sublayer selection: the live PyCell's MkPin() uses Layer("Metal1", "drawing")
    # which means addPin() creates geometry on the drawing layer only for pmos.
    # For nmos and HV variants, the PyCell DOES create pin sublayer geometry.
    if is_pmos and not is_hv:
        pin_layer_m1 = layer_metal1
        pin_layer_poly = layer_gatpoly
    else:
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
    def _even_dbu(w):
        dbu_w = round(w / 0.001)
        return (dbu_w + dbu_w % 2) * 0.001

    m1_layer = (8, 0)  # Metal1 drawing
    poly_layer = (5, 0)  # GatPoly drawing
    c.add_port(
        name="S",
        center=(src_x, src_y),
        width=_even_dbu(port_height),
        orientation=180,
        layer=m1_layer,
    )
    c.add_port(
        name="D",
        center=(drain_x, drain_y),
        width=_even_dbu(port_height),
        orientation=0,
        layer=m1_layer,
    )
    c.add_port(
        name="G",
        center=(gate_x, gate_y),
        width=_even_dbu(gate_height),
        orientation=270,
        layer=poly_layer,
    )

    return c


# ---------------------------------------------------------------------------
# Public cell functions
# ---------------------------------------------------------------------------
@gf.cell
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
    """
    c = _mos_core(width, length, nf, is_pmos=False, is_hv=False)

    # VLSIR simulation metadata
    c.info["vlsir"] = {
        "model": "sg13_lv_nmos",
        "spice_type": "SUBCKT",
        "spice_lib": "sg13g2_moslv_mod.lib",
        "port_order": ["d", "g", "s", "b"],
        "port_map": {"D": "d", "G": "g", "S": "s"},
        "params": {
            "w": width * 1e-6,
            "l": length * 1e-6,
            "ng": nf,
            "m": m,
        },
    }

    return c


@gf.cell
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
    """
    c = _mos_core(width, length, nf, is_pmos=True, is_hv=False)

    # VLSIR simulation metadata
    c.info["vlsir"] = {
        "model": "sg13_lv_pmos",
        "spice_type": "SUBCKT",
        "spice_lib": "sg13g2_moslv_mod.lib",
        "port_order": ["d", "g", "s", "b"],
        "port_map": {"D": "d", "G": "g", "S": "s"},
        "params": {
            "w": width * 1e-6,
            "l": length * 1e-6,
            "ng": nf,
            "m": m,
        },
    }

    return c


@gf.cell
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
    """
    c = _mos_core(width, length, nf, is_pmos=False, is_hv=True)

    # VLSIR simulation metadata
    c.info["vlsir"] = {
        "model": "sg13_hv_nmos",
        "spice_type": "SUBCKT",
        "spice_lib": "sg13g2_moshv_mod.lib",
        "port_order": ["d", "g", "s", "b"],
        "port_map": {"D": "d", "G": "g", "S": "s"},
        "params": {
            "w": width * 1e-6,
            "l": length * 1e-6,
            "ng": nf,
            "m": m,
        },
    }

    return c


@gf.cell
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
    """
    c = _mos_core(width, length, nf, is_pmos=True, is_hv=True)

    # VLSIR simulation metadata
    c.info["vlsir"] = {
        "model": "sg13_hv_pmos",
        "spice_type": "SUBCKT",
        "spice_lib": "sg13g2_moshv_mod.lib",
        "port_order": ["d", "g", "s", "b"],
        "port_map": {"D": "d", "G": "g", "S": "s"},
        "params": {
            "w": width * 1e-6,
            "l": length * 1e-6,
            "ng": nf,
            "m": m,
        },
    }

    return c


# ---------------------------------------------------------------------------
# RF variants - delegated to fixed GDS imports (full implementation deferred)
# ---------------------------------------------------------------------------
@gf.cell
def rfnmos(
    width: float = 2.0,
    length: float = 0.13,
    nf: int = 2,
    m: int = 1,
    model: str = "sg13_lv_rfnmos",
) -> Component:
    """Create an RF NMOS transistor.

    Currently delegates to fixed GDS import. Parametric RF layout is deferred
    due to complexity (gate rings, guard rings, Metal2 connections).
    """
    from . import fixed

    c = fixed.rfnmos()
    c.info["vlsir"] = {
        "model": "sg13_lv_nmos",
        "spice_type": "SUBCKT",
        "spice_lib": "sg13g2_moslv_mod.lib",
        "port_order": ["d", "g", "s", "b"],
        "port_map": {},
        "params": {"rfmode": 1},
    }
    return c


@gf.cell
def rfpmos(
    width: float = 2.0,
    length: float = 0.13,
    nf: int = 2,
    m: int = 1,
    model: str = "sg13_lv_rfpmos",
) -> Component:
    """Create an RF PMOS transistor.

    Currently delegates to fixed GDS import. Parametric RF layout is deferred
    due to complexity (gate rings, guard rings, Metal2 connections).
    """
    from . import fixed

    c = fixed.rfpmos()
    c.info["vlsir"] = {
        "model": "sg13_lv_pmos",
        "spice_type": "SUBCKT",
        "spice_lib": "sg13g2_moslv_mod.lib",
        "port_order": ["d", "g", "s", "b"],
        "port_map": {},
        "params": {"rfmode": 1},
    }
    return c


if __name__ == "__main__":
    from gdsfactory.difftest import xor

    from ihp import PDK
    from ihp import cells2 as pycell

    PDK.activate()

    c0 = pycell.nmos()  # PyCell reference
    c1 = nmos()  # Pure GDSFactory
    c = xor(c0, c1)
    c.show()

    # c0 = pycell.pmos()
    # c1 = pmos()
    # c = xor(c0, c1)
    # c.show()

    # c0 = pycell.nmosHV()
    # c1 = nmos_hv()
    # c = xor(c0, c1)
    # c.show()

    # c0 = pycell.pmosHV()
    # c1 = pmos_hv()
    # c = xor(c0, c1)
    # c.show()
