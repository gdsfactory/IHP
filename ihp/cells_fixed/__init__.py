"""Bipolar transistor components for IHP PDK."""

import warnings
from functools import partial, wraps

import gdsfactory as gf
from kfactory.schematic import DSchematic

from ..config import PATH
from ..tech import LAYER

_XS = "metal1_routing"


def deprecated(func):
    """Mark a fixed-GDS cell as deprecated."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        warnings.warn(
            f"{func.__name__} is deprecated. Use the pure-Python pcell equivalent.",
            DeprecationWarning,
            stacklevel=2,
        )
        return func(*args, **kwargs)

    return wrapper


def _safe_add_ports_from_markers(component, pin_layer, port_layer):
    try:
        gf.add_ports.add_ports_from_markers_inside(
            component, pin_layer=pin_layer, port_layer=port_layer
        )
    except ValueError as exc:
        if "already in" not in str(exc):
            raise
        warnings.warn(
            f"Duplicate port detected on layer {pin_layer}; skipping overlapping port(s).",
            stacklevel=2,
        )


_add_ports_metal1 = partial(
    _safe_add_ports_from_markers,
    pin_layer=LAYER.Metal1pin,
    port_layer=LAYER.Metal1drawing,
)
_add_ports_metal2 = partial(
    _safe_add_ports_from_markers,
    pin_layer=LAYER.Metal2pin,
    port_layer=LAYER.Metal2drawing,
)
_add_ports = (_add_ports_metal1, _add_ports_metal2)
gdsdir = PATH.gds
import_gds = partial(gf.import_gds, post_process=_add_ports)


# ---------------------------------------------------------------------------
# Schematic functions for fixed cells
# ---------------------------------------------------------------------------


def _svaricap_fixed_schematic() -> DSchematic:
    s = DSchematic()
    s.info["symbol"] = "varicap"
    s.info["ports"] = [
        {"name": "bn", "side": "top", "type": "electric"},
        {"name": "G2", "side": "bottom", "type": "electric"},
        {"name": "G1", "side": "left", "type": "electric"},
        {"name": "W", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "name": "svaricap",
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerMOShv.lib",
            "sections": ["mos_tt", "mos_ss", "mos_ff", "mos_sf", "mos_fs"],
            "port_order": ["G1", "W", "G2", "bn"],
            "params": {},
        }
    ]
    s.create_port(name="G1", cross_section=_XS, x=-1, y=0, orientation=180)
    s.create_port(name="W", cross_section=_XS, x=1, y=0, orientation=0)
    s.create_port(name="G2", cross_section=_XS, x=0, y=-1, orientation=270)
    s.create_port(name="bn", cross_section=_XS, x=0, y=1, orientation=90)
    return s


def _bondpad_fixed_schematic() -> DSchematic:
    s = DSchematic()
    s.info["symbol"] = "pad"
    s.info["ports"] = [{"name": "PAD", "side": "top", "type": "electric"}]
    s.info["models"] = [
        {
            "language": "spice",
            "name": "bondpad",
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/sg13g2_bondpad.lib",
            "sections": [],
            "port_order": ["PAD"],
            "params": {},
        }
    ]
    s.create_port(name="PAD", cross_section=_XS, x=0, y=1, orientation=90)
    return s


def _cmim_fixed_schematic() -> DSchematic:
    s = DSchematic()
    s.info["symbol"] = "capacitor"
    s.info["ports"] = [
        {"name": "MINUS", "side": "left", "type": "electric"},
        {"name": "PLUS", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "name": "cmim",
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerCAP.lib",
            "sections": ["cap_typ", "cap_bcs", "cap_wcs"],
            "port_order": ["PLUS", "MINUS"],
            "params": {},
        }
    ]
    s.create_port(name="MINUS", cross_section=_XS, x=-1, y=0, orientation=180)
    s.create_port(name="PLUS", cross_section=_XS, x=1, y=0, orientation=0)
    return s


def _dantenna_fixed_schematic() -> DSchematic:
    s = DSchematic()
    s.info["symbol"] = "diode"
    s.info["ports"] = [
        {"name": "1", "side": "top", "type": "electric"},
        {"name": "2", "side": "bottom", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "name": "dantenna",
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerDIO.lib",
            "sections": ["dio_tt", "dio_ss", "dio_ff"],
            "port_order": ["1", "2"],
            "params": {},
        }
    ]
    s.create_port(name="1", cross_section=_XS, x=0, y=1, orientation=90)
    s.create_port(name="2", cross_section=_XS, x=0, y=-1, orientation=270)
    return s


def _esd_diode_fixed_schematic(model_name: str) -> DSchematic:
    """Shared schematic for ESD diode fixed cells."""
    s = DSchematic()
    s.info["symbol"] = "diode"
    s.info["ports"] = [
        {"name": "VDD", "side": "top", "type": "electric"},
        {"name": "VSS", "side": "bottom", "type": "electric"},
        {"name": "PAD", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "name": model_name,
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/sg13g2_esd.lib",
            "sections": [],
            "port_order": ["VDD", "PAD", "VSS"],
            "params": {},
        }
    ]
    s.create_port(name="VDD", cross_section=_XS, x=0, y=1, orientation=90)
    s.create_port(name="PAD", cross_section=_XS, x=1, y=0, orientation=0)
    s.create_port(name="VSS", cross_section=_XS, x=0, y=-1, orientation=270)
    return s


def _diodevdd_2kv_fixed_schematic() -> DSchematic:
    return _esd_diode_fixed_schematic("diodevdd_2kv")


def _diodevdd_4kv_fixed_schematic() -> DSchematic:
    return _esd_diode_fixed_schematic("diodevdd_4kv")


def _diodevss_2kv_fixed_schematic() -> DSchematic:
    return _esd_diode_fixed_schematic("diodevss_2kv")


def _diodevss_4kv_fixed_schematic() -> DSchematic:
    return _esd_diode_fixed_schematic("diodevss_4kv")


def _dpantenna_fixed_schematic() -> DSchematic:
    s = DSchematic()
    s.info["symbol"] = "diode"
    s.info["ports"] = [
        {"name": "1", "side": "top", "type": "electric"},
        {"name": "2", "side": "bottom", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "name": "dpantenna",
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerDIO.lib",
            "sections": ["dio_tt", "dio_ss", "dio_ff"],
            "port_order": ["1", "2"],
            "params": {},
        }
    ]
    s.create_port(name="1", cross_section=_XS, x=0, y=1, orientation=90)
    s.create_port(name="2", cross_section=_XS, x=0, y=-1, orientation=270)
    return s


def _dummy1_fixed_schematic() -> DSchematic:
    s = DSchematic()
    s.info["symbol"] = "resistor"
    s.info["ports"] = [
        {"name": "W", "side": "left", "type": "electric"},
        {"name": "2", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "name": "dummy1",
            "spice_type": "RESISTOR",
            "library": "ihp/models/ngspice/models/cornerRES.lib",
            "sections": ["res_typ", "res_bcs", "res_wcs"],
            "port_order": ["W", "2"],
            "params": {},
        }
    ]
    s.create_port(name="W", cross_section=_XS, x=-1, y=0, orientation=180)
    s.create_port(name="2", cross_section=_XS, x=1, y=0, orientation=0)
    return s


def _isolbox_fixed_schematic() -> DSchematic:
    s = DSchematic()
    s.info["symbol"] = "ckt"
    s.info["ports"] = [
        {"name": "bn", "side": "bottom", "type": "electric"},
        {"name": "isoub", "side": "left", "type": "electric"},
        {"name": "NWell", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "name": "isolbox",
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerDIO.lib",
            "sections": ["dio_tt", "dio_ss", "dio_ff"],
            "port_order": ["isoub", "NWell", "bn"],
            "params": {},
        }
    ]
    s.create_port(name="isoub", cross_section=_XS, x=-1, y=0, orientation=180)
    s.create_port(name="NWell", cross_section=_XS, x=1, y=0, orientation=0)
    s.create_port(name="bn", cross_section=_XS, x=0, y=-1, orientation=270)
    return s


def _lv_mos_fixed_schematic(model_name: str, symbol: str) -> DSchematic:
    """Shared schematic for LV MOS fixed cells."""
    s = DSchematic()
    s.info["symbol"] = symbol
    s.info["ports"] = [
        {"name": "d", "side": "top", "type": "electric"},
        {"name": "s", "side": "bottom", "type": "electric"},
        {"name": "g", "side": "left", "type": "electric"},
        {"name": "b", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "name": model_name,
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerMOSlv.lib",
            "sections": ["mos_tt", "mos_ss", "mos_ff", "mos_sf", "mos_fs"],
            "port_order": ["d", "g", "s", "b"],
            "params": {},
        }
    ]
    s.create_port(name="d", cross_section=_XS, x=0, y=1, orientation=90)
    s.create_port(name="s", cross_section=_XS, x=0, y=-1, orientation=270)
    s.create_port(name="g", cross_section=_XS, x=-1, y=0, orientation=180)
    s.create_port(name="b", cross_section=_XS, x=1, y=0, orientation=0)
    return s


def _hv_mos_fixed_schematic(model_name: str, symbol: str) -> DSchematic:
    """Shared schematic for HV MOS fixed cells."""
    s = DSchematic()
    s.info["symbol"] = symbol
    s.info["ports"] = [
        {"name": "d", "side": "top", "type": "electric"},
        {"name": "s", "side": "bottom", "type": "electric"},
        {"name": "g", "side": "left", "type": "electric"},
        {"name": "b", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "name": model_name,
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerMOShv.lib",
            "sections": ["mos_tt", "mos_ss", "mos_ff", "mos_sf", "mos_fs"],
            "port_order": ["d", "g", "s", "b"],
            "params": {},
        }
    ]
    s.create_port(name="d", cross_section=_XS, x=0, y=1, orientation=90)
    s.create_port(name="s", cross_section=_XS, x=0, y=-1, orientation=270)
    s.create_port(name="g", cross_section=_XS, x=-1, y=0, orientation=180)
    s.create_port(name="b", cross_section=_XS, x=1, y=0, orientation=0)
    return s


def _rf_lv_mos_fixed_schematic(model_name: str, symbol: str) -> DSchematic:
    """Shared schematic for RF LV MOS fixed cells."""
    s = DSchematic()
    s.info["symbol"] = symbol
    s.info["ports"] = [
        {"name": "d", "side": "top", "type": "electric"},
        {"name": "s", "side": "bottom", "type": "electric"},
        {"name": "g", "side": "left", "type": "electric"},
        {"name": "b", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "name": model_name,
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerMOSlv.lib",
            "sections": ["mos_tt", "mos_ss", "mos_ff", "mos_sf", "mos_fs"],
            "port_order": ["d", "g", "s", "b"],
            "params": {"rfmode": "1"},
        }
    ]
    s.create_port(name="d", cross_section=_XS, x=0, y=1, orientation=90)
    s.create_port(name="s", cross_section=_XS, x=0, y=-1, orientation=270)
    s.create_port(name="g", cross_section=_XS, x=-1, y=0, orientation=180)
    s.create_port(name="b", cross_section=_XS, x=1, y=0, orientation=0)
    return s


def _rf_hv_mos_fixed_schematic(model_name: str, symbol: str) -> DSchematic:
    """Shared schematic for RF HV MOS fixed cells."""
    s = DSchematic()
    s.info["symbol"] = symbol
    s.info["ports"] = [
        {"name": "d", "side": "top", "type": "electric"},
        {"name": "s", "side": "bottom", "type": "electric"},
        {"name": "g", "side": "left", "type": "electric"},
        {"name": "b", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "name": model_name,
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerMOShv.lib",
            "sections": ["mos_tt", "mos_ss", "mos_ff", "mos_sf", "mos_fs"],
            "port_order": ["d", "g", "s", "b"],
            "params": {"rfmode": "1"},
        }
    ]
    s.create_port(name="d", cross_section=_XS, x=0, y=1, orientation=90)
    s.create_port(name="s", cross_section=_XS, x=0, y=-1, orientation=270)
    s.create_port(name="g", cross_section=_XS, x=-1, y=0, orientation=180)
    s.create_port(name="b", cross_section=_XS, x=1, y=0, orientation=0)
    return s


def _nmos_fixed_schematic() -> DSchematic:
    return _lv_mos_fixed_schematic("sg13_lv_nmos", "nmos")


def _nmosHV_fixed_schematic() -> DSchematic:
    return _hv_mos_fixed_schematic("sg13_hv_nmos", "nmos")


def _nmoscl_lv_fixed_schematic(model_name: str) -> DSchematic:
    """Shared schematic for nmoscl fixed cells."""
    s = DSchematic()
    s.info["symbol"] = "nmos"
    s.info["ports"] = [
        {"name": "VDD", "side": "top", "type": "electric"},
        {"name": "VSS", "side": "bottom", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "name": model_name,
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerMOSlv.lib",
            "sections": ["mos_tt", "mos_ss", "mos_ff", "mos_sf", "mos_fs"],
            "port_order": ["VDD", "VSS"],
            "params": {},
        }
    ]
    s.create_port(name="VDD", cross_section=_XS, x=0, y=1, orientation=90)
    s.create_port(name="VSS", cross_section=_XS, x=0, y=-1, orientation=270)
    return s


def _nmoscl_2_fixed_schematic() -> DSchematic:
    return _nmoscl_lv_fixed_schematic("nmoscl_2")


def _nmoscl_4_fixed_schematic() -> DSchematic:
    return _nmoscl_lv_fixed_schematic("nmoscl_4")


def _npn_fixed_schematic(model_name: str) -> DSchematic:
    """Shared schematic for NPN BJT fixed cells."""
    s = DSchematic()
    s.info["symbol"] = "npn"
    s.info["ports"] = [
        {"name": "bn", "side": "top", "type": "electric"},
        {"name": "e", "side": "bottom", "type": "electric"},
        {"name": "b", "side": "left", "type": "electric"},
        {"name": "c", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "name": model_name,
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerHBT.lib",
            "sections": ["hbt_typ", "hbt_bcs", "hbt_wcs"],
            "port_order": ["c", "b", "e", "bn"],
            "params": {},
        }
    ]
    s.create_port(name="c", cross_section=_XS, x=1, y=0, orientation=0)
    s.create_port(name="b", cross_section=_XS, x=-1, y=0, orientation=180)
    s.create_port(name="e", cross_section=_XS, x=0, y=-1, orientation=270)
    s.create_port(name="bn", cross_section=_XS, x=0, y=1, orientation=90)
    return s


def _npn13G2_fixed_schematic() -> DSchematic:
    return _npn_fixed_schematic("npn13G2")


def _npn13G2L_fixed_schematic() -> DSchematic:
    return _npn_fixed_schematic("npn13G2l")


def _npn13G2V_fixed_schematic() -> DSchematic:
    return _npn_fixed_schematic("npn13G2v")


def _tap_fixed_schematic(model_name: str) -> DSchematic:
    """Shared schematic for tap fixed cells."""
    s = DSchematic()
    s.info["symbol"] = "tap"
    s.info["ports"] = [
        {"name": "1", "side": "top", "type": "electric"},
        {"name": "2", "side": "bottom", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "name": model_name,
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerRES.lib",
            "sections": ["res_typ", "res_bcs", "res_wcs"],
            "port_order": ["1", "2"],
            "params": {},
        }
    ]
    s.create_port(name="1", cross_section=_XS, x=0, y=1, orientation=90)
    s.create_port(name="2", cross_section=_XS, x=0, y=-1, orientation=270)
    return s


def _ntap1_fixed_schematic() -> DSchematic:
    return _tap_fixed_schematic("ntap1")


def _ptap1_fixed_schematic() -> DSchematic:
    return _tap_fixed_schematic("ptap1")


def _pmos_fixed_schematic() -> DSchematic:
    return _lv_mos_fixed_schematic("sg13_lv_pmos", "pmos")


def _pmosHV_fixed_schematic() -> DSchematic:
    return _hv_mos_fixed_schematic("sg13_hv_pmos", "pmos")


def _pnpMPA_fixed_schematic() -> DSchematic:
    s = DSchematic()
    s.info["symbol"] = "pnp"
    s.info["ports"] = [
        {"name": "e", "side": "bottom", "type": "electric"},
        {"name": "b", "side": "left", "type": "electric"},
        {"name": "c", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "name": "pnpMPA",
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerHBT.lib",
            "sections": ["hbt_typ", "hbt_bcs", "hbt_wcs"],
            "port_order": ["c", "b", "e"],
            "params": {},
        }
    ]
    s.create_port(name="c", cross_section=_XS, x=1, y=0, orientation=0)
    s.create_port(name="b", cross_section=_XS, x=-1, y=0, orientation=180)
    s.create_port(name="e", cross_section=_XS, x=0, y=-1, orientation=270)
    return s


def _rfcmim_fixed_schematic() -> DSchematic:
    s = DSchematic()
    s.info["symbol"] = "capacitor"
    s.info["ports"] = [
        {"name": "bn", "side": "bottom", "type": "electric"},
        {"name": "MINUS", "side": "left", "type": "electric"},
        {"name": "PLUS", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "name": "cap_rfcmim",
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerCAP.lib",
            "sections": ["cap_typ", "cap_bcs", "cap_wcs"],
            "port_order": ["PLUS", "MINUS", "bn"],
            "params": {},
        }
    ]
    s.create_port(name="MINUS", cross_section=_XS, x=-1, y=0, orientation=180)
    s.create_port(name="PLUS", cross_section=_XS, x=1, y=0, orientation=0)
    s.create_port(name="bn", cross_section=_XS, x=0, y=-1, orientation=270)
    return s


def _rfnmos_fixed_schematic() -> DSchematic:
    return _rf_lv_mos_fixed_schematic("sg13_lv_nmos", "nmos")


def _rfnmosHV_fixed_schematic() -> DSchematic:
    return _rf_hv_mos_fixed_schematic("sg13_hv_nmos", "nmos")


def _rfpmos_fixed_schematic() -> DSchematic:
    return _rf_lv_mos_fixed_schematic("sg13_lv_pmos", "pmos")


def _rfpmosHV_fixed_schematic() -> DSchematic:
    return _rf_hv_mos_fixed_schematic("sg13_hv_pmos", "pmos")


def _resistor_3port_fixed_schematic(model_name: str) -> DSchematic:
    """Shared schematic for 3-port resistor fixed cells."""
    s = DSchematic()
    s.info["symbol"] = "resistor"
    s.info["ports"] = [
        {"name": "1", "side": "top", "type": "electric"},
        {"name": "3", "side": "bottom", "type": "electric"},
        {"name": "bn", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "name": model_name,
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/cornerRES.lib",
            "sections": ["res_typ", "res_bcs", "res_wcs"],
            "port_order": ["1", "3", "bn"],
            "params": {},
        }
    ]
    s.create_port(name="1", cross_section=_XS, x=0, y=1, orientation=90)
    s.create_port(name="3", cross_section=_XS, x=0, y=-1, orientation=270)
    s.create_port(name="bn", cross_section=_XS, x=1, y=0, orientation=0)
    return s


def _rhigh_fixed_schematic() -> DSchematic:
    return _resistor_3port_fixed_schematic("rhigh")


def _rppd_fixed_schematic() -> DSchematic:
    return _resistor_3port_fixed_schematic("rppd")


def _rsil_fixed_schematic() -> DSchematic:
    return _resistor_3port_fixed_schematic("rsil")


def _schottky_nbl1_fixed_schematic() -> DSchematic:
    s = DSchematic()
    s.info["symbol"] = "diode"
    s.info["ports"] = [
        {"name": "A", "side": "top", "type": "electric"},
        {"name": "C", "side": "bottom", "type": "electric"},
        {"name": "S", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "name": "schottky_nbl1",
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/sg13g2_dschottky_nbl1_mod.lib",
            "sections": [],
            "port_order": ["A", "C", "S"],
            "params": {},
        }
    ]
    s.create_port(name="A", cross_section=_XS, x=0, y=1, orientation=90)
    s.create_port(name="C", cross_section=_XS, x=0, y=-1, orientation=270)
    s.create_port(name="S", cross_section=_XS, x=1, y=0, orientation=0)
    return s


# ---------------------------------------------------------------------------
# Fixed GDS cells
# ---------------------------------------------------------------------------


@deprecated
@gf.cell(tags=["IHP", "bondpad"])
def CuPillarPad_fixed() -> gf.Component:
    """Returns CuPillarPad fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.CuPillarPad_fixed()
      c.plot()
    """
    c = import_gds(gdsdir / "CuPillarPad.gds")
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


@deprecated
@gf.cell(tags=["IHP", "inductor"])
def L2_IND_LVS_fixed() -> gf.Component:
    """Returns L2_IND_LVS fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.L2_IND_LVS_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "L2_IND_LVS.gds")


@deprecated
@gf.cell(tags=["IHP", "via"])
def M1_GatPoly_CDNS_675179387644_fixed() -> gf.Component:
    """Returns M1_GatPoly_CDNS_675179387644 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.M1_GatPoly_CDNS_675179387644_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "M1_GatPoly_CDNS_675179387644.gds")


@deprecated
@gf.cell(tags=["IHP", "via"])
def M2_M1_CDNS_675179387643_fixed() -> gf.Component:
    """Returns M2_M1_CDNS_675179387643 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.M2_M1_CDNS_675179387643_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "M2_M1_CDNS_675179387643.gds")


@deprecated
@gf.cell(tags=["IHP", "via"])
def M3_M2_CDNS_675179387642_fixed() -> gf.Component:
    """Returns M3_M2_CDNS_675179387642 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.M3_M2_CDNS_675179387642_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "M3_M2_CDNS_675179387642.gds")


@deprecated
@gf.cell(tags=["IHP", "via"])
def M4_M3_CDNS_675179387641_fixed() -> gf.Component:
    """Returns M4_M3_CDNS_675179387641 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.M4_M3_CDNS_675179387641_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "M4_M3_CDNS_675179387641.gds")


@deprecated
@gf.cell(tags=["IHP", "via"])
def M5_M4_CDNS_675179387640_fixed() -> gf.Component:
    """Returns M5_M4_CDNS_675179387640 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.M5_M4_CDNS_675179387640_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "M5_M4_CDNS_675179387640.gds")


@deprecated
@gf.cell(tags=["IHP", "fill"])
def NoFillerStack_fixed() -> gf.Component:
    """Returns NoFillerStack fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.NoFillerStack_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "NoFillerStack.gds")


@deprecated
@gf.cell(schematic_function=_svaricap_fixed_schematic, tags=["IHP", "varicap", "hv"])
def SVaricap_fixed() -> gf.Component:
    """Returns SVaricap fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.SVaricap_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "SVaricap.gds")


@deprecated
@gf.cell(tags=["IHP", "via"])
def TM1_M5_CDNS_675179387645_fixed() -> gf.Component:
    """Returns TM1_M5_CDNS_675179387645 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.TM1_M5_CDNS_675179387645_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "TM1_M5_CDNS_675179387645.gds")


@deprecated
@gf.cell(tags=["IHP", "via"])
def TM2_TM1_CDNS_675179387646_fixed() -> gf.Component:
    """Returns TM2_TM1_CDNS_675179387646 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.TM2_TM1_CDNS_675179387646_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "TM2_TM1_CDNS_675179387646.gds")


@deprecated
@gf.cell(tags=["IHP", "via", "tsv"])
def TSV_fixed() -> gf.Component:
    """Returns TSV fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.TSV_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "TSV.gds")


@deprecated
@gf.cell(tags=["IHP", "via", "stack"])
def ViaStack_fixed() -> gf.Component:
    """Returns ViaStack fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.ViaStack_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "ViaStack.gds")


@deprecated
@gf.cell(schematic_function=_bondpad_fixed_schematic, tags=["IHP", "bondpad"])
def bondpad_fixed() -> gf.Component:
    """Returns bondpad fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.bondpad()
      c.plot()
    """
    return import_gds(gdsdir / "bondpad.gds")


@deprecated
@gf.cell(tags=["IHP", "text"])
def chipText_fixed() -> gf.Component:
    """Returns chipText fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.chipText_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "chipText.gds")


@deprecated
@gf.cell(schematic_function=_cmim_fixed_schematic, tags=["IHP", "capacitor", "mim"])
def cmim_fixed() -> gf.Component:
    """Returns cmim fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.cmim()
      c.plot()
    """
    return import_gds(gdsdir / "cmim.gds")


@deprecated
@gf.cell(tags=["IHP", "layer"])
def colors_and_stipples_fixed() -> gf.Component:
    """Returns colors_and_stipples fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.colors_and_stipples_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "colors_and_stipples.gds")


@deprecated
@gf.cell(schematic_function=_dantenna_fixed_schematic, tags=["IHP", "diode", "antenna"])
def dantenna_fixed() -> gf.Component:
    """Returns dantenna fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.dantenna()
      c.plot()
    """
    return import_gds(gdsdir / "dantenna.gds")


@deprecated
@gf.cell(tags=["IHP", "probe"])
def diffstbprobe_fixed() -> gf.Component:
    """Returns diffstbprobe fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.diffstbprobe_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "diffstbprobe.gds")


@deprecated
@gf.cell(schematic_function=_diodevdd_2kv_fixed_schematic, tags=["IHP", "esd"])
def diodevdd_2kv_fixed() -> gf.Component:
    """Returns diodevdd_2kv fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.diodevdd_2kv_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "diodevdd_2kv.gds")


@deprecated
@gf.cell(schematic_function=_diodevdd_4kv_fixed_schematic, tags=["IHP", "esd"])
def diodevdd_4kv_fixed() -> gf.Component:
    """Returns diodevdd_4kv fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.diodevdd_4kv_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "diodevdd_4kv.gds")


@deprecated
@gf.cell(schematic_function=_diodevss_2kv_fixed_schematic, tags=["IHP", "esd"])
def diodevss_2kv_fixed() -> gf.Component:
    """Returns diodevss_2kv fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.diodevss_2kv_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "diodevss_2kv.gds")


@deprecated
@gf.cell(schematic_function=_diodevss_4kv_fixed_schematic, tags=["IHP", "esd"])
def diodevss_4kv_fixed() -> gf.Component:
    """Returns diodevss_4kv fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.diodevss_4kv_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "diodevss_4kv.gds")


@deprecated
@gf.cell(
    schematic_function=_dpantenna_fixed_schematic, tags=["IHP", "diode", "antenna"]
)
def dpantenna_fixed() -> gf.Component:
    """Returns dpantenna fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.dpantenna()
      c.plot()
    """
    return import_gds(gdsdir / "dpantenna.gds")


@deprecated
@gf.cell(schematic_function=_dummy1_fixed_schematic, tags=["IHP", "resistor"])
def dummy1_fixed() -> gf.Component:
    """Returns dummy1 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.dummy1_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "dummy1.gds")


@deprecated
@gf.cell(tags=["IHP", "inductor"])
def inductor2_fixed() -> gf.Component:
    """Returns inductor2 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.inductor2()
      c.plot()
    """
    return import_gds(gdsdir / "inductor2.gds")


@deprecated
@gf.cell(tags=["IHP", "inductor"])
def inductor3_fixed() -> gf.Component:
    """Returns inductor3 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.inductor3()
      c.plot()
    """
    return import_gds(gdsdir / "inductor3.gds")


@deprecated
@gf.cell(tags=["IHP", "probe"])
def iprobe_fixed() -> gf.Component:
    """Returns iprobe fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.iprobe_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "iprobe.gds")


@deprecated
@gf.cell(schematic_function=_isolbox_fixed_schematic, tags=["IHP", "diode", "antenna"])
def isolbox_fixed() -> gf.Component:
    """Returns isolbox fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.isolbox_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "isolbox.gds")


@deprecated
@gf.cell(tags=["IHP", "resistor"])
def lvsres_fixed() -> gf.Component:
    """Returns lvsres fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.lvsres_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "lvsres.gds")


@deprecated
@gf.cell(schematic_function=_nmos_fixed_schematic, tags=["IHP", "mos", "lv"])
def nmos_fixed() -> gf.Component:
    """Returns nmos fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.nmos()
      c.plot()
    """
    return import_gds(gdsdir / "nmos.gds")


@deprecated
@gf.cell(schematic_function=_nmosHV_fixed_schematic, tags=["IHP", "mos", "hv"])
def nmosHV_fixed() -> gf.Component:
    """Returns nmosHV fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.nmosHV_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "nmosHV.gds")


@deprecated
@gf.cell(schematic_function=_nmoscl_2_fixed_schematic, tags=["IHP", "mos", "lv"])
def nmoscl_2_fixed() -> gf.Component:
    """Returns nmoscl_2 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.nmoscl_2_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "nmoscl_2.gds")


@deprecated
@gf.cell(schematic_function=_nmoscl_4_fixed_schematic, tags=["IHP", "mos", "lv"])
def nmoscl_4_fixed() -> gf.Component:
    """Returns nmoscl_4 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.nmoscl_4_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "nmoscl_4.gds")


@deprecated
@gf.cell(schematic_function=_npn13G2_fixed_schematic, tags=["IHP", "bjt", "npn"])
def npn13G2_fixed() -> gf.Component:
    """Returns npn13G2 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.npn13G2()
      c.plot()
    """
    return import_gds(gdsdir / "npn13G2.gds")


@deprecated
@gf.cell(schematic_function=_npn13G2L_fixed_schematic, tags=["IHP", "bjt", "npn"])
def npn13G2L_fixed() -> gf.Component:
    """Returns npn13G2L fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.npn13G2L()
      c.plot()
    """
    return import_gds(gdsdir / "npn13G2L.gds")


@deprecated
@gf.cell(schematic_function=_npn13G2V_fixed_schematic, tags=["IHP", "bjt", "npn"])
def npn13G2V_fixed() -> gf.Component:
    """Returns npn13G2V fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.npn13G2V()
      c.plot()
    """
    return import_gds(gdsdir / "npn13G2V.gds")


@deprecated
@gf.cell(tags=["IHP", "bjt", "npn"])
def npn13G2_base_CDNS_675179387640_fixed() -> gf.Component:
    """Returns npn13G2_base_CDNS_675179387640 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.npn13G2_base_CDNS_675179387640_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "npn13G2_base_CDNS_675179387640.gds")


@deprecated
@gf.cell(tags=["IHP", "tap", "n-type"])
def ntap_fixed() -> gf.Component:
    """Returns ntap fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.ntap_fixed()
      c.plot()
    """
    # TODO: What is this and how is it different from ntap1?
    return import_gds(gdsdir / "ntap.gds")


@deprecated
@gf.cell(schematic_function=_ntap1_fixed_schematic, tags=["IHP", "tap"])
def ntap1_fixed() -> gf.Component:
    """Returns ntap1 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.ntap1()
      c.plot()
    """
    return import_gds(gdsdir / "ntap1.gds")


@deprecated
@gf.cell(schematic_function=_pmos_fixed_schematic, tags=["IHP", "mos", "lv"])
def pmos_fixed() -> gf.Component:
    """Returns pmos fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.pmos()
      c.plot()
    """
    return import_gds(gdsdir / "pmos.gds")


@deprecated
@gf.cell(schematic_function=_pmosHV_fixed_schematic, tags=["IHP", "mos", "hv"])
def pmosHV_fixed() -> gf.Component:
    """Returns pmosHV fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.pmosHV_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "pmosHV.gds")


@deprecated
@gf.cell(schematic_function=_pnpMPA_fixed_schematic, tags=["IHP", "bjt", "pnp"])
def pnpMPA_fixed() -> gf.Component:
    """Returns pnpMPA fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.pnpMPA()
      c.plot()
    """
    return import_gds(gdsdir / "pnpMPA.gds")


@deprecated
@gf.cell(tags=["IHP", "tap", "p-type"])
def ptap_fixed() -> gf.Component:
    """Returns ptap fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.ptap_fixed()
      c.plot()
    """
    # TODO: What is this and how is it different from ptap1?
    return import_gds(gdsdir / "ptap.gds")


@deprecated
@gf.cell(schematic_function=_ptap1_fixed_schematic, tags=["IHP", "tap"])
def ptap1_fixed() -> gf.Component:
    """Returns ptap1 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.ptap1()
      c.plot()
    """
    return import_gds(gdsdir / "ptap1.gds")


@deprecated
@gf.cell(
    schematic_function=_rfcmim_fixed_schematic, tags=["IHP", "capacitor", "mim", "rf"]
)
def rfcmim_fixed() -> gf.Component:
    """Returns rfcmim fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.rfcmim()
      c.plot()
    """
    return import_gds(gdsdir / "rfcmim.gds")


@deprecated
@gf.cell(schematic_function=_rfnmos_fixed_schematic, tags=["IHP", "mos", "lv", "rf"])
def rfnmos_fixed() -> gf.Component:
    """Returns rfnmos fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.rfnmos()
      c.plot()
    """
    return import_gds(gdsdir / "rfnmos.gds")


@deprecated
@gf.cell(schematic_function=_rfnmosHV_fixed_schematic, tags=["IHP", "mos", "hv", "rf"])
def rfnmosHV_fixed() -> gf.Component:
    """Returns rfnmosHV fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.rfnmosHV_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "rfnmosHV.gds")


@deprecated
@gf.cell(schematic_function=_rfpmos_fixed_schematic, tags=["IHP", "mos", "lv", "rf"])
def rfpmos_fixed() -> gf.Component:
    """Returns rfpmos fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.rfpmos()
      c.plot()
    """
    return import_gds(gdsdir / "rfpmos.gds")


@deprecated
@gf.cell(schematic_function=_rfpmosHV_fixed_schematic, tags=["IHP", "mos", "hv", "rf"])
def rfpmosHV_fixed() -> gf.Component:
    """Returns rfpmosHV fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.rfpmosHV_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "rfpmosHV.gds")


@deprecated
@gf.cell(schematic_function=_rhigh_fixed_schematic, tags=["IHP", "resistor"])
def rhigh_fixed() -> gf.Component:
    """Returns rhigh fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.rhigh()
      c.plot()
    """
    return import_gds(gdsdir / "rhigh.gds")


@deprecated
@gf.cell(schematic_function=_rppd_fixed_schematic, tags=["IHP", "resistor"])
def rppd_fixed() -> gf.Component:
    """Returns rppd fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.rppd()
      c.plot()
    """
    return import_gds(gdsdir / "rppd.gds")


@deprecated
@gf.cell(schematic_function=_rsil_fixed_schematic, tags=["IHP", "resistor"])
def rsil_fixed() -> gf.Component:
    """Returns rsil fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.rsil()
      c.plot()
    """
    return import_gds(gdsdir / "rsil.gds")


@deprecated
@gf.cell(
    schematic_function=_schottky_nbl1_fixed_schematic, tags=["IHP", "diode", "schottky"]
)
def schottky_nbl1_fixed() -> gf.Component:
    """Returns schottky_nbl1 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.schottky_nbl1_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "schottky_nbl1.gds")


@deprecated
@gf.cell(tags=["IHP", "esd"])
def scr1_fixed() -> gf.Component:
    """Returns scr1 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.scr1_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "scr1.gds")


@deprecated
@gf.cell(tags=["IHP", "sealring"])
def sealring_CDNS_675179387642_fixed() -> gf.Component:
    """Returns sealring_CDNS_675179387642 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.sealring_CDNS_675179387642_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "sealring_CDNS_675179387642.gds")


@deprecated
@gf.cell(tags=["IHP", "sealring"])
def sealring_complete_fixed() -> gf.Component:
    """Returns sealring_complete fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.sealring_complete_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "sealring_complete.gds")


@deprecated
@gf.cell(tags=["IHP", "sealring"])
def sealring_corner_CDNS_675179387641_fixed() -> gf.Component:
    """Returns sealring_corner_CDNS_675179387641 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.sealring_corner_CDNS_675179387641_fixed()
      c.plot()
    """
    return import_gds(gdsdir / "sealring_corner_CDNS_675179387641.gds")
