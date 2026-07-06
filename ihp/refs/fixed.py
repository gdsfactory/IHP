"""Bipolar transistor components for IHP PDK."""

import warnings
from functools import partial

import gdsfactory as gf

from ..config import PATH


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
    _safe_add_ports_from_markers, pin_layer=(8, 2), port_layer=(8, 0)
)
_add_ports_metal2 = partial(
    _safe_add_ports_from_markers, pin_layer=(10, 2), port_layer=(10, 0)
)
_add_ports = (_add_ports_metal1, _add_ports_metal2)
gdsdir = PATH.gds
import_gds = partial(gf.import_gds, post_process=_add_ports)


@gf.cell(tags=["IHP", "bondpad"])
def CuPillarPad() -> gf.Component:
    """Returns CuPillarPad fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.CuPillarPad()
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


@gf.cell(tags=["IHP", "inductor"])
def L2_IND_LVS() -> gf.Component:
    """Returns L2_IND_LVS fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.L2_IND_LVS()
      c.plot()
    """
    return import_gds(gdsdir / "L2_IND_LVS.gds")


@gf.cell(tags=["IHP", "via"])
def M1_GatPoly_CDNS_675179387644() -> gf.Component:
    """Returns M1_GatPoly_CDNS_675179387644 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.M1_GatPoly_CDNS_675179387644()
      c.plot()
    """
    return import_gds(gdsdir / "M1_GatPoly_CDNS_675179387644.gds")


@gf.cell(tags=["IHP", "via"])
def M2_M1_CDNS_675179387643() -> gf.Component:
    """Returns M2_M1_CDNS_675179387643 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.M2_M1_CDNS_675179387643()
      c.plot()
    """
    return import_gds(gdsdir / "M2_M1_CDNS_675179387643.gds")


@gf.cell(tags=["IHP", "via"])
def M3_M2_CDNS_675179387642() -> gf.Component:
    """Returns M3_M2_CDNS_675179387642 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.M3_M2_CDNS_675179387642()
      c.plot()
    """
    return import_gds(gdsdir / "M3_M2_CDNS_675179387642.gds")


@gf.cell(tags=["IHP", "via"])
def M4_M3_CDNS_675179387641() -> gf.Component:
    """Returns M4_M3_CDNS_675179387641 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.M4_M3_CDNS_675179387641()
      c.plot()
    """
    return import_gds(gdsdir / "M4_M3_CDNS_675179387641.gds")


@gf.cell(tags=["IHP", "via"])
def M5_M4_CDNS_675179387640() -> gf.Component:
    """Returns M5_M4_CDNS_675179387640 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.M5_M4_CDNS_675179387640()
      c.plot()
    """
    return import_gds(gdsdir / "M5_M4_CDNS_675179387640.gds")


@gf.cell(tags=["IHP", "fill"])
def NoFillerStack() -> gf.Component:
    """Returns NoFillerStack fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.NoFillerStack()
      c.plot()
    """
    return import_gds(gdsdir / "NoFillerStack.gds")


@gf.cell(tags=["IHP", "varicap", "hv"])
def SVaricap() -> gf.Component:
    """Returns SVaricap fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.SVaricap()
      c.plot()
    """
    return import_gds(gdsdir / "SVaricap.gds")


@gf.cell(tags=["IHP", "via"])
def TM1_M5_CDNS_675179387645() -> gf.Component:
    """Returns TM1_M5_CDNS_675179387645 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.TM1_M5_CDNS_675179387645()
      c.plot()
    """
    return import_gds(gdsdir / "TM1_M5_CDNS_675179387645.gds")


@gf.cell(tags=["IHP", "via"])
def TM2_TM1_CDNS_675179387646() -> gf.Component:
    """Returns TM2_TM1_CDNS_675179387646 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.TM2_TM1_CDNS_675179387646()
      c.plot()
    """
    return import_gds(gdsdir / "TM2_TM1_CDNS_675179387646.gds")


@gf.cell(tags=["IHP", "via", "tsv"])
def TSV() -> gf.Component:
    """Returns TSV fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.TSV()
      c.plot()
    """
    return import_gds(gdsdir / "TSV.gds")


@gf.cell(tags=["IHP", "via", "stack"])
def ViaStack() -> gf.Component:
    """Returns ViaStack fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.ViaStack()
      c.plot()
    """
    return import_gds(gdsdir / "ViaStack.gds")


@gf.cell(tags=["IHP", "bondpad"])
def bondpad() -> gf.Component:
    """Returns bondpad fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.bondpad()
      c.plot()
    """
    return import_gds(gdsdir / "bondpad.gds")


@gf.cell(tags=["IHP", "text"])
def chipText() -> gf.Component:
    """Returns chipText fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.chipText()
      c.plot()
    """
    return import_gds(gdsdir / "chipText.gds")


@gf.cell(tags=["IHP", "capacitor", "mim"])
def cmim() -> gf.Component:
    """Returns cmim fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.cmim()
      c.plot()
    """
    return import_gds(gdsdir / "cmim.gds")


@gf.cell(tags=["IHP", "layer"])
def colors_and_stipples() -> gf.Component:
    """Returns colors_and_stipples fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.colors_and_stipples()
      c.plot()
    """
    return import_gds(gdsdir / "colors_and_stipples.gds")


@gf.cell(tags=["IHP", "diode", "antenna"])
def dantenna() -> gf.Component:
    """Returns dantenna fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.dantenna()
      c.plot()
    """
    return import_gds(gdsdir / "dantenna.gds")


@gf.cell(tags=["IHP", "probe"])
def diffstbprobe() -> gf.Component:
    """Returns diffstbprobe fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.diffstbprobe()
      c.plot()
    """
    return import_gds(gdsdir / "diffstbprobe.gds")


@gf.cell(tags=["IHP", "esd"])
def diodevdd_2kv() -> gf.Component:
    """Returns diodevdd_2kv fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.diodevdd_2kv()
      c.plot()
    """
    return import_gds(gdsdir / "diodevdd_2kv.gds")


@gf.cell(tags=["IHP", "esd"])
def diodevdd_4kv() -> gf.Component:
    """Returns diodevdd_4kv fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.diodevdd_4kv()
      c.plot()
    """
    return import_gds(gdsdir / "diodevdd_4kv.gds")


@gf.cell(tags=["IHP", "esd"])
def diodevss_2kv() -> gf.Component:
    """Returns diodevss_2kv fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.diodevss_2kv()
      c.plot()
    """
    return import_gds(gdsdir / "diodevss_2kv.gds")


@gf.cell(tags=["IHP", "esd"])
def diodevss_4kv() -> gf.Component:
    """Returns diodevss_4kv fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.diodevss_4kv()
      c.plot()
    """
    return import_gds(gdsdir / "diodevss_4kv.gds")


@gf.cell(tags=["IHP", "diode", "antenna"])
def dpantenna() -> gf.Component:
    """Returns dpantenna fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.dpantenna()
      c.plot()
    """
    return import_gds(gdsdir / "dpantenna.gds")


@gf.cell(tags=["IHP", "resistor"])
def dummy1() -> gf.Component:
    """Returns dummy1 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.dummy1()
      c.plot()
    """
    return import_gds(gdsdir / "dummy1.gds")


@gf.cell(tags=["IHP", "inductor"])
def inductor2() -> gf.Component:
    """Returns inductor2 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.inductor2()
      c.plot()
    """
    return import_gds(gdsdir / "inductor2.gds")


@gf.cell(tags=["IHP", "inductor"])
def inductor3() -> gf.Component:
    """Returns inductor3 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.inductor3()
      c.plot()
    """
    return import_gds(gdsdir / "inductor3.gds")


@gf.cell(tags=["IHP", "probe"])
def iprobe() -> gf.Component:
    """Returns iprobe fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.iprobe()
      c.plot()
    """
    return import_gds(gdsdir / "iprobe.gds")


@gf.cell(tags=["IHP", "diode", "antenna"])
def isolbox() -> gf.Component:
    """Returns isolbox fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.isolbox()
      c.plot()
    """
    return import_gds(gdsdir / "isolbox.gds")


@gf.cell(tags=["IHP", "resistor"])
def lvsres() -> gf.Component:
    """Returns lvsres fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.lvsres()
      c.plot()
    """
    return import_gds(gdsdir / "lvsres.gds")


@gf.cell(tags=["IHP", "mos", "lv"])
def nmos() -> gf.Component:
    """Returns nmos fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.nmos()
      c.plot()
    """
    return import_gds(gdsdir / "nmos.gds")


@gf.cell(tags=["IHP", "mos", "hv"])
def nmosHV() -> gf.Component:
    """Returns nmosHV fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.nmosHV()
      c.plot()
    """
    return import_gds(gdsdir / "nmosHV.gds")


@gf.cell(tags=["IHP", "mos", "lv"])
def nmoscl_2() -> gf.Component:
    """Returns nmoscl_2 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.nmoscl_2()
      c.plot()
    """
    return import_gds(gdsdir / "nmoscl_2.gds")


@gf.cell(tags=["IHP", "mos", "lv"])
def nmoscl_4() -> gf.Component:
    """Returns nmoscl_4 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.nmoscl_4()
      c.plot()
    """
    return import_gds(gdsdir / "nmoscl_4.gds")


@gf.cell(tags=["IHP", "bjt", "npn"])
def npn13G2() -> gf.Component:
    """Returns npn13G2 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.npn13G2()
      c.plot()
    """
    return import_gds(gdsdir / "npn13G2.gds")


@gf.cell(tags=["IHP", "bjt", "npn"])
def npn13G2L() -> gf.Component:
    """Returns npn13G2L fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.npn13G2L()
      c.plot()
    """
    return import_gds(gdsdir / "npn13G2L.gds")


@gf.cell(tags=["IHP", "bjt", "npn"])
def npn13G2V() -> gf.Component:
    """Returns npn13G2V fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.npn13G2V()
      c.plot()
    """
    return import_gds(gdsdir / "npn13G2V.gds")


@gf.cell(tags=["IHP", "bjt", "npn"])
def npn13G2_base_CDNS_675179387640() -> gf.Component:
    """Returns npn13G2_base_CDNS_675179387640 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.npn13G2_base_CDNS_675179387640()
      c.plot()
    """
    return import_gds(gdsdir / "npn13G2_base_CDNS_675179387640.gds")


@gf.cell(tags=["IHP", "tap", "n-type"])
def ntap() -> gf.Component:
    """Returns ntap fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.ntap()
      c.plot()
    """
    return import_gds(gdsdir / "ntap.gds")


@gf.cell(tags=["IHP", "tap", "n-type"])
def ntap1() -> gf.Component:
    """Returns ntap1 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.ntap1()
      c.plot()
    """
    return import_gds(gdsdir / "ntap1.gds")


@gf.cell(tags=["IHP", "mos", "lv"])
def pmos() -> gf.Component:
    """Returns pmos fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.pmos()
      c.plot()
    """
    return import_gds(gdsdir / "pmos.gds")


@gf.cell(tags=["IHP", "mos", "hv"])
def pmosHV() -> gf.Component:
    """Returns pmosHV fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.pmosHV()
      c.plot()
    """
    return import_gds(gdsdir / "pmosHV.gds")


@gf.cell(tags=["IHP", "bjt", "pnp"])
def pnpMPA() -> gf.Component:
    """Returns pnpMPA fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.pnpMPA()
      c.plot()
    """
    return import_gds(gdsdir / "pnpMPA.gds")


@gf.cell(tags=["IHP", "tap", "p-type"])
def ptap() -> gf.Component:
    """Returns ptap fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.ptap()
      c.plot()
    """
    return import_gds(gdsdir / "ptap.gds")


@gf.cell(tags=["IHP", "tap", "p-type"])
def ptap1() -> gf.Component:
    """Returns ptap1 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.ptap1()
      c.plot()
    """
    return import_gds(gdsdir / "ptap1.gds")


@gf.cell(tags=["IHP", "capacitor", "mim", "rf"])
def rfcmim() -> gf.Component:
    """Returns rfcmim fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.rfcmim()
      c.plot()
    """
    return import_gds(gdsdir / "rfcmim.gds")


@gf.cell(tags=["IHP", "mos", "lv", "rf"])
def rfnmos() -> gf.Component:
    """Returns rfnmos fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.rfnmos()
      c.plot()
    """
    return import_gds(gdsdir / "rfnmos.gds")


@gf.cell(tags=["IHP", "mos", "hv", "rf"])
def rfnmosHV() -> gf.Component:
    """Returns rfnmosHV fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.rfnmosHV()
      c.plot()
    """
    return import_gds(gdsdir / "rfnmosHV.gds")


@gf.cell(tags=["IHP", "mos", "lv", "rf"])
def rfpmos() -> gf.Component:
    """Returns rfpmos fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.rfpmos()
      c.plot()
    """
    return import_gds(gdsdir / "rfpmos.gds")


@gf.cell(tags=["IHP", "mos", "hv", "rf"])
def rfpmosHV() -> gf.Component:
    """Returns rfpmosHV fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.rfpmosHV()
      c.plot()
    """
    return import_gds(gdsdir / "rfpmosHV.gds")


@gf.cell(tags=["IHP", "resistor", "high-r"])
def rhigh() -> gf.Component:
    """Returns rhigh fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.rhigh()
      c.plot()
    """
    return import_gds(gdsdir / "rhigh.gds")


@gf.cell(tags=["IHP", "resistor", "unsilicided"])
def rppd() -> gf.Component:
    """Returns rppd fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.rppd()
      c.plot()
    """
    return import_gds(gdsdir / "rppd.gds")


@gf.cell(tags=["IHP", "resistor", "silicided"])
def rsil() -> gf.Component:
    """Returns rsil fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.rsil()
      c.plot()
    """
    return import_gds(gdsdir / "rsil.gds")


@gf.cell(tags=["IHP", "diode", "schottky"])
def schottky_nbl1() -> gf.Component:
    """Returns schottky_nbl1 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.schottky_nbl1()
      c.plot()
    """
    return import_gds(gdsdir / "schottky_nbl1.gds")


@gf.cell(tags=["IHP", "esd"])
def scr1() -> gf.Component:
    """Returns scr1 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.scr1()
      c.plot()
    """
    return import_gds(gdsdir / "scr1.gds")


@gf.cell(tags=["IHP", "sealring"])
def sealring_CDNS_675179387642() -> gf.Component:
    """Returns sealring_CDNS_675179387642 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.sealring_CDNS_675179387642()
      c.plot()
    """
    return import_gds(gdsdir / "sealring_CDNS_675179387642.gds")


@gf.cell(tags=["IHP", "sealring"])
def sealring_complete() -> gf.Component:
    """Returns sealring_complete fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.sealring_complete()
      c.plot()
    """
    return import_gds(gdsdir / "sealring_complete.gds")


@gf.cell(tags=["IHP", "sealring"])
def sealring_corner_CDNS_675179387641() -> gf.Component:
    """Returns sealring_corner_CDNS_675179387641 fixed cell.

    .. plot::
      :include-source:

      import ihp

      c = ihp.cells.sealring_corner_CDNS_675179387641()
      c.plot()
    """
    return import_gds(gdsdir / "sealring_corner_CDNS_675179387641.gds")


if __name__ == "__main__":
    from ihp import PDK

    PDK.activate()
    # c = sealring_corner_CDNS_675179387641()
    c = CuPillarPad()
    c.pprint_ports()
    c.show()
