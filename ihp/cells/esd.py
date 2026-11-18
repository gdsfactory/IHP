"""ESD protection diode components for IHP PDK (imported from GDS)."""

import gdsfactory as gf
import klayout.db as kdb
from gdsfactory import Component
from kfactory.schematic import DSchematic

from ..config import PATH

_XS = "metal1_routing"

_PIN_LAYERS = {
    "Metal1pin": "Metal1drawing",
    "Metal2pin": "Metal2drawing",
}


def _esd_diode_schematic(model_name: str, m: int = 1) -> DSchematic:
    """Shared schematic for ESD diode cells."""
    s = DSchematic()
    s.info["ports"] = [
        {"name": "VDD", "side": "top", "type": "electric"},
        {"name": "VSS", "side": "bottom", "type": "electric"},
        {"name": "PAD", "side": "right", "type": "electric"},
    ]
    s.info["models"] = [
        {
            "language": "spice",
            "implementation": "NgSpice",
            "name": model_name,
            "spice_type": "SUBCKT",
            "library": "ihp/models/ngspice/models/sg13g2_esd.lib",
            "sections": [],
            "port_order": ["VDD", "PAD", "VSS"],
            "params": {"m": "m"},
        },
        {
            "language": "spectre",
            "implementation": "VACASK",
            "name": model_name,
            "spice_type": "SUBCKT",
            "library": "ihp/models/vacask/models/sg13g2_esd.lib",
            "sections": [],
            "port_order": ["VDD", "PAD", "VSS"],
            "params": {"m": "m"},
        },
    ]
    s.create_port(name="VDD", cross_section=_XS, x=0, y=1, orientation=90)
    s.create_port(name="PAD", cross_section=_XS, x=1, y=0, orientation=0)
    s.create_port(name="VSS", cross_section=_XS, x=0, y=-1, orientation=270)
    return s


def _esd_diode(name: str) -> Component:
    """Import an ESD diode GDS and add VDD/PAD/VSS ports from its pin labels.

    Each port sits on the edge of the labelled pin shape closest to the cell
    boundary, facing outwards.
    """
    c = gf.import_gds(PATH.gds / f"{name}.gds")
    bbox = c.dbbox()
    labels = {}
    for li in c.kcl.layer_indexes():
        for it in c.begin_shapes_rec(li).each():
            shape = it.shape()
            if shape.is_text() and shape.text_string in ("VDD", "PAD", "VSS"):
                labels[shape.text_string] = (it.dtrans() * shape.dtext).position()

    pin_shapes = [
        (p.to_dtype(c.kcl.dbu), drawing_layer)
        for pin_layer, drawing_layer in _PIN_LAYERS.items()
        for p in kdb.Region(c.begin_shapes_rec(gf.get_layer(pin_layer))).merged().each()
    ]

    for port_name, point in labels.items():
        match = next(((p, dl) for p, dl in pin_shapes if p.inside(point)), None)
        if match is None:
            raise ValueError(f"{name}: no pin shape under label {port_name!r}")
        pin, drawing_layer = match[0].bbox(), match[1]
        edges = {
            180: (pin.left - bbox.left, (pin.left, pin.center().y), pin.height()),
            0: (bbox.right - pin.right, (pin.right, pin.center().y), pin.height()),
            270: (pin.bottom - bbox.bottom, (pin.center().x, pin.bottom), pin.width()),
            90: (bbox.top - pin.top, (pin.center().x, pin.top), pin.width()),
        }
        orientation = min(edges, key=lambda o: edges[o][0])
        _, center, width = edges[orientation]
        c.add_port(
            name=port_name,
            center=center,
            width=width,
            orientation=orientation,
            layer=drawing_layer,
            port_type="electrical",
        )
    c.info["model"] = name
    return c


def diodevdd_2kv_schematic(m: int = 1) -> DSchematic:
    return _esd_diode_schematic("diodevdd_2kv", m)


def diodevdd_4kv_schematic(m: int = 1) -> DSchematic:
    return _esd_diode_schematic("diodevdd_4kv", m)


def diodevss_2kv_schematic(m: int = 1) -> DSchematic:
    return _esd_diode_schematic("diodevss_2kv", m)


def diodevss_4kv_schematic(m: int = 1) -> DSchematic:
    return _esd_diode_schematic("diodevss_4kv", m)


@gf.cell(schematic_function=diodevdd_2kv_schematic, tags=["IHP", "esd", "diode"])
def diodevdd_2kv(m: int = 1) -> Component:
    """Create a 2 kV ESD diode from PAD to VDD.

    Args:
        m: Multiplier (number of parallel devices, netlist only).
    """
    return _esd_diode("diodevdd_2kv")


@gf.cell(schematic_function=diodevdd_4kv_schematic, tags=["IHP", "esd", "diode"])
def diodevdd_4kv(m: int = 1) -> Component:
    """Create a 4 kV ESD diode from PAD to VDD.

    Args:
        m: Multiplier (number of parallel devices, netlist only).
    """
    return _esd_diode("diodevdd_4kv")


@gf.cell(schematic_function=diodevss_2kv_schematic, tags=["IHP", "esd", "diode"])
def diodevss_2kv(m: int = 1) -> Component:
    """Create a 2 kV ESD diode from VSS to PAD.

    Args:
        m: Multiplier (number of parallel devices, netlist only).
    """
    return _esd_diode("diodevss_2kv")


@gf.cell(schematic_function=diodevss_4kv_schematic, tags=["IHP", "esd", "diode"])
def diodevss_4kv(m: int = 1) -> Component:
    """Create a 4 kV ESD diode from VSS to PAD.

    Args:
        m: Multiplier (number of parallel devices, netlist only).
    """
    return _esd_diode("diodevss_4kv")
