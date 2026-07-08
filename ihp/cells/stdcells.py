"""SG13G2 standard cell library."""

from __future__ import annotations

import gdsfactory as gf
import klayout.db as kdb

from ..config import PATH

_GDS_PATH = PATH.gds / "sg13g2_stdcell.gds"
_LABEL_LAYER = (8, 25)
_PIN_LAYER = (8, 2)
_PORT_LAYER = "Metal1drawing"


def _snap(val: float, grid: float = 0.002) -> float:
    return round(round(val / grid) * grid, 6)


def _add_ports_from_labels(component: gf.Component, cell_name: str) -> None:
    layout = kdb.Layout()
    layout.read(str(_GDS_PATH))
    dbu = layout.dbu

    li_text = layout.find_layer(*_LABEL_LAYER)
    li_pin = layout.find_layer(*_PIN_LAYER)

    labels: list[tuple[str, float, float]] = []
    pins: list[tuple[float, float, float, float]] = []

    for ci in range(layout.cells()):
        cell = layout.cell(ci)
        if cell.name == cell_name:
            for s in cell.each_shape(li_text):
                if s.is_text():
                    labels.append(
                        (
                            s.text_string,
                            s.text_trans.disp.x * dbu,
                            s.text_trans.disp.y * dbu,
                        )
                    )
            for s in cell.each_shape(li_pin):
                b = s.dbbox()
                pins.append((b.left, b.bottom, b.right, b.top))
            break

    bb = component.dbbox()
    cell_mid_y = (bb.top + bb.bottom) / 2

    seen: set[str] = set()
    for name, lx, ly in labels:
        if name in seen:
            continue
        best_pin = None
        best_area = float("inf")
        for left, bottom, right, top in pins:
            if left <= lx <= right and bottom <= ly <= top:
                area = (right - left) * (top - bottom)
                if area < best_area:
                    best_area = area
                    best_pin = (left, bottom, right, top)
        if best_pin is None:
            continue

        left, bottom, right, top = best_pin
        cx = _snap((left + right) / 2)
        cy = _snap((bottom + top) / 2)
        w = right - left
        h = top - bottom
        port_width = _snap(w)

        if w > h:
            orientation = 90 if cy > cell_mid_y else 270
        else:
            dist = {
                180: abs(cx - bb.left),
                0: abs(cx - bb.right),
                90: abs(cy - bb.top),
                270: abs(cy - bb.bottom),
            }
            orientation = min(dist, key=dist.get)

        component.add_port(
            name=name,
            center=(cx, cy),
            width=port_width,
            orientation=orientation,
            layer=_PORT_LAYER,
            port_type="electrical",
        )
        seen.add(name)


def _import_stdcell(cell_name: str) -> gf.Component:
    c = gf.import_gds(_GDS_PATH, cellname=cell_name)
    _add_ports_from_labels(c, cell_name)
    return c


@gf.cell(tags=["IHP", "stdcell", "aoi"])
def sg13g2_a21o_1() -> gf.Component:
    """Returns sg13g2_a21o_1 standard cell."""
    return _import_stdcell("sg13g2_a21o_1")


@gf.cell(tags=["IHP", "stdcell", "aoi"])
def sg13g2_a21o_2() -> gf.Component:
    """Returns sg13g2_a21o_2 standard cell."""
    return _import_stdcell("sg13g2_a21o_2")


@gf.cell(tags=["IHP", "stdcell", "aoi"])
def sg13g2_a21oi_1() -> gf.Component:
    """Returns sg13g2_a21oi_1 standard cell."""
    return _import_stdcell("sg13g2_a21oi_1")


@gf.cell(tags=["IHP", "stdcell", "aoi"])
def sg13g2_a21oi_2() -> gf.Component:
    """Returns sg13g2_a21oi_2 standard cell."""
    return _import_stdcell("sg13g2_a21oi_2")


@gf.cell(tags=["IHP", "stdcell", "aoi"])
def sg13g2_a221oi_1() -> gf.Component:
    """Returns sg13g2_a221oi_1 standard cell."""
    return _import_stdcell("sg13g2_a221oi_1")


@gf.cell(tags=["IHP", "stdcell", "aoi"])
def sg13g2_a22oi_1() -> gf.Component:
    """Returns sg13g2_a22oi_1 standard cell."""
    return _import_stdcell("sg13g2_a22oi_1")


@gf.cell(tags=["IHP", "stdcell", "and"])
def sg13g2_and2_1() -> gf.Component:
    """Returns sg13g2_and2_1 standard cell."""
    return _import_stdcell("sg13g2_and2_1")


@gf.cell(tags=["IHP", "stdcell", "and"])
def sg13g2_and2_2() -> gf.Component:
    """Returns sg13g2_and2_2 standard cell."""
    return _import_stdcell("sg13g2_and2_2")


@gf.cell(tags=["IHP", "stdcell", "and"])
def sg13g2_and3_1() -> gf.Component:
    """Returns sg13g2_and3_1 standard cell."""
    return _import_stdcell("sg13g2_and3_1")


@gf.cell(tags=["IHP", "stdcell", "and"])
def sg13g2_and3_2() -> gf.Component:
    """Returns sg13g2_and3_2 standard cell."""
    return _import_stdcell("sg13g2_and3_2")


@gf.cell(tags=["IHP", "stdcell", "and"])
def sg13g2_and4_1() -> gf.Component:
    """Returns sg13g2_and4_1 standard cell."""
    return _import_stdcell("sg13g2_and4_1")


@gf.cell(tags=["IHP", "stdcell", "and"])
def sg13g2_and4_2() -> gf.Component:
    """Returns sg13g2_and4_2 standard cell."""
    return _import_stdcell("sg13g2_and4_2")


@gf.cell(tags=["IHP", "stdcell", "antenna"])
def sg13g2_antennanp() -> gf.Component:
    """Returns sg13g2_antennanp standard cell."""
    return _import_stdcell("sg13g2_antennanp")


@gf.cell(tags=["IHP", "stdcell", "buf"])
def sg13g2_buf_1() -> gf.Component:
    """Returns sg13g2_buf_1 standard cell."""
    return _import_stdcell("sg13g2_buf_1")


@gf.cell(tags=["IHP", "stdcell", "buf"])
def sg13g2_buf_2() -> gf.Component:
    """Returns sg13g2_buf_2 standard cell."""
    return _import_stdcell("sg13g2_buf_2")


@gf.cell(tags=["IHP", "stdcell", "buf"])
def sg13g2_buf_4() -> gf.Component:
    """Returns sg13g2_buf_4 standard cell."""
    return _import_stdcell("sg13g2_buf_4")


@gf.cell(tags=["IHP", "stdcell", "buf"])
def sg13g2_buf_8() -> gf.Component:
    """Returns sg13g2_buf_8 standard cell."""
    return _import_stdcell("sg13g2_buf_8")


@gf.cell(tags=["IHP", "stdcell", "buf"])
def sg13g2_buf_16() -> gf.Component:
    """Returns sg13g2_buf_16 standard cell."""
    return _import_stdcell("sg13g2_buf_16")


@gf.cell(tags=["IHP", "stdcell", "decap"])
def sg13g2_decap_4() -> gf.Component:
    """Returns sg13g2_decap_4 standard cell."""
    return _import_stdcell("sg13g2_decap_4")


@gf.cell(tags=["IHP", "stdcell", "decap"])
def sg13g2_decap_8() -> gf.Component:
    """Returns sg13g2_decap_8 standard cell."""
    return _import_stdcell("sg13g2_decap_8")


@gf.cell(tags=["IHP", "stdcell", "dff"])
def sg13g2_dfrbp_1() -> gf.Component:
    """Returns sg13g2_dfrbp_1 standard cell."""
    return _import_stdcell("sg13g2_dfrbp_1")


@gf.cell(tags=["IHP", "stdcell", "dff"])
def sg13g2_dfrbp_2() -> gf.Component:
    """Returns sg13g2_dfrbp_2 standard cell."""
    return _import_stdcell("sg13g2_dfrbp_2")


@gf.cell(tags=["IHP", "stdcell", "dff"])
def sg13g2_dfrbpq_1() -> gf.Component:
    """Returns sg13g2_dfrbpq_1 standard cell."""
    return _import_stdcell("sg13g2_dfrbpq_1")


@gf.cell(tags=["IHP", "stdcell", "dff"])
def sg13g2_dfrbpq_2() -> gf.Component:
    """Returns sg13g2_dfrbpq_2 standard cell."""
    return _import_stdcell("sg13g2_dfrbpq_2")


@gf.cell(tags=["IHP", "stdcell", "latch"])
def sg13g2_dlhq_1() -> gf.Component:
    """Returns sg13g2_dlhq_1 standard cell."""
    return _import_stdcell("sg13g2_dlhq_1")


@gf.cell(tags=["IHP", "stdcell", "latch"])
def sg13g2_dlhr_1() -> gf.Component:
    """Returns sg13g2_dlhr_1 standard cell."""
    return _import_stdcell("sg13g2_dlhr_1")


@gf.cell(tags=["IHP", "stdcell", "latch"])
def sg13g2_dlhrq_1() -> gf.Component:
    """Returns sg13g2_dlhrq_1 standard cell."""
    return _import_stdcell("sg13g2_dlhrq_1")


@gf.cell(tags=["IHP", "stdcell", "latch"])
def sg13g2_dllr_1() -> gf.Component:
    """Returns sg13g2_dllr_1 standard cell."""
    return _import_stdcell("sg13g2_dllr_1")


@gf.cell(tags=["IHP", "stdcell", "latch"])
def sg13g2_dllrq_1() -> gf.Component:
    """Returns sg13g2_dllrq_1 standard cell."""
    return _import_stdcell("sg13g2_dllrq_1")


@gf.cell(tags=["IHP", "stdcell", "delay"])
def sg13g2_dlygate4sd1_1() -> gf.Component:
    """Returns sg13g2_dlygate4sd1_1 standard cell."""
    return _import_stdcell("sg13g2_dlygate4sd1_1")


@gf.cell(tags=["IHP", "stdcell", "delay"])
def sg13g2_dlygate4sd2_1() -> gf.Component:
    """Returns sg13g2_dlygate4sd2_1 standard cell."""
    return _import_stdcell("sg13g2_dlygate4sd2_1")


@gf.cell(tags=["IHP", "stdcell", "delay"])
def sg13g2_dlygate4sd3_1() -> gf.Component:
    """Returns sg13g2_dlygate4sd3_1 standard cell."""
    return _import_stdcell("sg13g2_dlygate4sd3_1")


@gf.cell(tags=["IHP", "stdcell", "tribuf"])
def sg13g2_ebufn_2() -> gf.Component:
    """Returns sg13g2_ebufn_2 standard cell."""
    return _import_stdcell("sg13g2_ebufn_2")


@gf.cell(tags=["IHP", "stdcell", "tribuf"])
def sg13g2_ebufn_4() -> gf.Component:
    """Returns sg13g2_ebufn_4 standard cell."""
    return _import_stdcell("sg13g2_ebufn_4")


@gf.cell(tags=["IHP", "stdcell", "tribuf"])
def sg13g2_ebufn_8() -> gf.Component:
    """Returns sg13g2_ebufn_8 standard cell."""
    return _import_stdcell("sg13g2_ebufn_8")


@gf.cell(tags=["IHP", "stdcell", "triinv"])
def sg13g2_einvn_2() -> gf.Component:
    """Returns sg13g2_einvn_2 standard cell."""
    return _import_stdcell("sg13g2_einvn_2")


@gf.cell(tags=["IHP", "stdcell", "triinv"])
def sg13g2_einvn_4() -> gf.Component:
    """Returns sg13g2_einvn_4 standard cell."""
    return _import_stdcell("sg13g2_einvn_4")


@gf.cell(tags=["IHP", "stdcell", "triinv"])
def sg13g2_einvn_8() -> gf.Component:
    """Returns sg13g2_einvn_8 standard cell."""
    return _import_stdcell("sg13g2_einvn_8")


@gf.cell(tags=["IHP", "stdcell", "fill"])
def sg13g2_fill_1() -> gf.Component:
    """Returns sg13g2_fill_1 standard cell."""
    return _import_stdcell("sg13g2_fill_1")


@gf.cell(tags=["IHP", "stdcell", "fill"])
def sg13g2_fill_2() -> gf.Component:
    """Returns sg13g2_fill_2 standard cell."""
    return _import_stdcell("sg13g2_fill_2")


@gf.cell(tags=["IHP", "stdcell", "fill"])
def sg13g2_fill_4() -> gf.Component:
    """Returns sg13g2_fill_4 standard cell."""
    return _import_stdcell("sg13g2_fill_4")


@gf.cell(tags=["IHP", "stdcell", "fill"])
def sg13g2_fill_8() -> gf.Component:
    """Returns sg13g2_fill_8 standard cell."""
    return _import_stdcell("sg13g2_fill_8")


@gf.cell(tags=["IHP", "stdcell", "inv"])
def sg13g2_inv_1() -> gf.Component:
    """Returns sg13g2_inv_1 standard cell."""
    return _import_stdcell("sg13g2_inv_1")


@gf.cell(tags=["IHP", "stdcell", "inv"])
def sg13g2_inv_2() -> gf.Component:
    """Returns sg13g2_inv_2 standard cell."""
    return _import_stdcell("sg13g2_inv_2")


@gf.cell(tags=["IHP", "stdcell", "inv"])
def sg13g2_inv_4() -> gf.Component:
    """Returns sg13g2_inv_4 standard cell."""
    return _import_stdcell("sg13g2_inv_4")


@gf.cell(tags=["IHP", "stdcell", "inv"])
def sg13g2_inv_8() -> gf.Component:
    """Returns sg13g2_inv_8 standard cell."""
    return _import_stdcell("sg13g2_inv_8")


@gf.cell(tags=["IHP", "stdcell", "inv"])
def sg13g2_inv_16() -> gf.Component:
    """Returns sg13g2_inv_16 standard cell."""
    return _import_stdcell("sg13g2_inv_16")


@gf.cell(tags=["IHP", "stdcell", "icg"])
def sg13g2_lgcp_1() -> gf.Component:
    """Returns sg13g2_lgcp_1 standard cell."""
    return _import_stdcell("sg13g2_lgcp_1")


@gf.cell(tags=["IHP", "stdcell", "mux"])
def sg13g2_mux2_1() -> gf.Component:
    """Returns sg13g2_mux2_1 standard cell."""
    return _import_stdcell("sg13g2_mux2_1")


@gf.cell(tags=["IHP", "stdcell", "mux"])
def sg13g2_mux2_2() -> gf.Component:
    """Returns sg13g2_mux2_2 standard cell."""
    return _import_stdcell("sg13g2_mux2_2")


@gf.cell(tags=["IHP", "stdcell", "mux"])
def sg13g2_mux4_1() -> gf.Component:
    """Returns sg13g2_mux4_1 standard cell."""
    return _import_stdcell("sg13g2_mux4_1")


@gf.cell(tags=["IHP", "stdcell", "nand"])
def sg13g2_nand2_1() -> gf.Component:
    """Returns sg13g2_nand2_1 standard cell."""
    return _import_stdcell("sg13g2_nand2_1")


@gf.cell(tags=["IHP", "stdcell", "nand"])
def sg13g2_nand2_2() -> gf.Component:
    """Returns sg13g2_nand2_2 standard cell."""
    return _import_stdcell("sg13g2_nand2_2")


@gf.cell(tags=["IHP", "stdcell", "nand"])
def sg13g2_nand2b_1() -> gf.Component:
    """Returns sg13g2_nand2b_1 standard cell."""
    return _import_stdcell("sg13g2_nand2b_1")


@gf.cell(tags=["IHP", "stdcell", "nand"])
def sg13g2_nand2b_2() -> gf.Component:
    """Returns sg13g2_nand2b_2 standard cell."""
    return _import_stdcell("sg13g2_nand2b_2")


@gf.cell(tags=["IHP", "stdcell", "nand"])
def sg13g2_nand3_1() -> gf.Component:
    """Returns sg13g2_nand3_1 standard cell."""
    return _import_stdcell("sg13g2_nand3_1")


@gf.cell(tags=["IHP", "stdcell", "nand"])
def sg13g2_nand3b_1() -> gf.Component:
    """Returns sg13g2_nand3b_1 standard cell."""
    return _import_stdcell("sg13g2_nand3b_1")


@gf.cell(tags=["IHP", "stdcell", "nand"])
def sg13g2_nand4_1() -> gf.Component:
    """Returns sg13g2_nand4_1 standard cell."""
    return _import_stdcell("sg13g2_nand4_1")


@gf.cell(tags=["IHP", "stdcell", "nor"])
def sg13g2_nor2_1() -> gf.Component:
    """Returns sg13g2_nor2_1 standard cell."""
    return _import_stdcell("sg13g2_nor2_1")


@gf.cell(tags=["IHP", "stdcell", "nor"])
def sg13g2_nor2_2() -> gf.Component:
    """Returns sg13g2_nor2_2 standard cell."""
    return _import_stdcell("sg13g2_nor2_2")


@gf.cell(tags=["IHP", "stdcell", "nor"])
def sg13g2_nor2b_1() -> gf.Component:
    """Returns sg13g2_nor2b_1 standard cell."""
    return _import_stdcell("sg13g2_nor2b_1")


@gf.cell(tags=["IHP", "stdcell", "nor"])
def sg13g2_nor2b_2() -> gf.Component:
    """Returns sg13g2_nor2b_2 standard cell."""
    return _import_stdcell("sg13g2_nor2b_2")


@gf.cell(tags=["IHP", "stdcell", "nor"])
def sg13g2_nor3_1() -> gf.Component:
    """Returns sg13g2_nor3_1 standard cell."""
    return _import_stdcell("sg13g2_nor3_1")


@gf.cell(tags=["IHP", "stdcell", "nor"])
def sg13g2_nor3_2() -> gf.Component:
    """Returns sg13g2_nor3_2 standard cell."""
    return _import_stdcell("sg13g2_nor3_2")


@gf.cell(tags=["IHP", "stdcell", "nor"])
def sg13g2_nor4_1() -> gf.Component:
    """Returns sg13g2_nor4_1 standard cell."""
    return _import_stdcell("sg13g2_nor4_1")


@gf.cell(tags=["IHP", "stdcell", "nor"])
def sg13g2_nor4_2() -> gf.Component:
    """Returns sg13g2_nor4_2 standard cell."""
    return _import_stdcell("sg13g2_nor4_2")


@gf.cell(tags=["IHP", "stdcell", "oai"])
def sg13g2_o21ai_1() -> gf.Component:
    """Returns sg13g2_o21ai_1 standard cell."""
    return _import_stdcell("sg13g2_o21ai_1")


@gf.cell(tags=["IHP", "stdcell", "or"])
def sg13g2_or2_1() -> gf.Component:
    """Returns sg13g2_or2_1 standard cell."""
    return _import_stdcell("sg13g2_or2_1")


@gf.cell(tags=["IHP", "stdcell", "or"])
def sg13g2_or2_2() -> gf.Component:
    """Returns sg13g2_or2_2 standard cell."""
    return _import_stdcell("sg13g2_or2_2")


@gf.cell(tags=["IHP", "stdcell", "or"])
def sg13g2_or3_1() -> gf.Component:
    """Returns sg13g2_or3_1 standard cell."""
    return _import_stdcell("sg13g2_or3_1")


@gf.cell(tags=["IHP", "stdcell", "or"])
def sg13g2_or3_2() -> gf.Component:
    """Returns sg13g2_or3_2 standard cell."""
    return _import_stdcell("sg13g2_or3_2")


@gf.cell(tags=["IHP", "stdcell", "or"])
def sg13g2_or4_1() -> gf.Component:
    """Returns sg13g2_or4_1 standard cell."""
    return _import_stdcell("sg13g2_or4_1")


@gf.cell(tags=["IHP", "stdcell", "or"])
def sg13g2_or4_2() -> gf.Component:
    """Returns sg13g2_or4_2 standard cell."""
    return _import_stdcell("sg13g2_or4_2")


@gf.cell(tags=["IHP", "stdcell", "sdff"])
def sg13g2_sdfbbp_1() -> gf.Component:
    """Returns sg13g2_sdfbbp_1 standard cell."""
    return _import_stdcell("sg13g2_sdfbbp_1")


@gf.cell(tags=["IHP", "stdcell", "sdff"])
def sg13g2_sdfrbp_1() -> gf.Component:
    """Returns sg13g2_sdfrbp_1 standard cell."""
    return _import_stdcell("sg13g2_sdfrbp_1")


@gf.cell(tags=["IHP", "stdcell", "sdff"])
def sg13g2_sdfrbp_2() -> gf.Component:
    """Returns sg13g2_sdfrbp_2 standard cell."""
    return _import_stdcell("sg13g2_sdfrbp_2")


@gf.cell(tags=["IHP", "stdcell", "sdff"])
def sg13g2_sdfrbpq_1() -> gf.Component:
    """Returns sg13g2_sdfrbpq_1 standard cell."""
    return _import_stdcell("sg13g2_sdfrbpq_1")


@gf.cell(tags=["IHP", "stdcell", "sdff"])
def sg13g2_sdfrbpq_2() -> gf.Component:
    """Returns sg13g2_sdfrbpq_2 standard cell."""
    return _import_stdcell("sg13g2_sdfrbpq_2")


@gf.cell(tags=["IHP", "stdcell", "sighold"])
def sg13g2_sighold() -> gf.Component:
    """Returns sg13g2_sighold standard cell."""
    return _import_stdcell("sg13g2_sighold")


@gf.cell(tags=["IHP", "stdcell", "icg"])
def sg13g2_slgcp_1() -> gf.Component:
    """Returns sg13g2_slgcp_1 standard cell."""
    return _import_stdcell("sg13g2_slgcp_1")


@gf.cell(tags=["IHP", "stdcell", "tie"])
def sg13g2_tiehi() -> gf.Component:
    """Returns sg13g2_tiehi standard cell."""
    return _import_stdcell("sg13g2_tiehi")


@gf.cell(tags=["IHP", "stdcell", "tie"])
def sg13g2_tielo() -> gf.Component:
    """Returns sg13g2_tielo standard cell."""
    return _import_stdcell("sg13g2_tielo")


@gf.cell(tags=["IHP", "stdcell", "xor"])
def sg13g2_xnor2_1() -> gf.Component:
    """Returns sg13g2_xnor2_1 standard cell."""
    return _import_stdcell("sg13g2_xnor2_1")


@gf.cell(tags=["IHP", "stdcell", "xor"])
def sg13g2_xor2_1() -> gf.Component:
    """Returns sg13g2_xor2_1 standard cell."""
    return _import_stdcell("sg13g2_xor2_1")
