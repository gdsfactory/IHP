"""Antenna components for IHP PDK."""

from typing import Literal

import gdsfactory as gf

from .. import tech
from .ihp_pycell import dantenna as dantennaIHP
from .ihp_pycell import dpantenna as dpantennaIHP
from .utils import *


@gf.cell(tags=["IHP", "diode", "antenna"])
def dantenna(
    width: float = 0.78,
    length: float = 0.78,
    addRecLayer: str = "t",
    guardRingType: Literal["none", "psub"] = "none",
    guardRingDistance: float = 1,
) -> gf.Component:
    """Creates a diode antenna (dantenna) structure.

    This function generates a layout cell containing a rectangular antenna
    region with optional recognition layers and guard ring structures.
    Parameters allow customization of the antenna geometry and the type
    and spacing of guard rings.

    Args:
        width: Width of the antenna rectangle in microns.
        length: Length of the antenna rectangle in microns.
        addRecLayer: Recognition layer to add (e.g., 't' for top, 'b' for bottom,
            or '' for none).
        guardRingType: Type of guard ring to include. Options include:
            - 'none': No guard ring
            - 'psub': P-type guard ring
        guardRingDistance: Spacing between the antenna body and guard ring in microns.

    Returns:
        gdsfactory.Component: The generated antenna component.
    """

    area = width * 1e-6 * length * 1e-6
    perimeter = 2 * (width * 1e-6 + length * 1e-6)
    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "Display": "Selected",
        "model": tech.techParams["dantenna_model"],
        "Calculate": "a",
        "w": width * 1e-6,
        "l": length * 1e-6,
        "a": area,
        "p": perimeter,
        "addRecLayer": addRecLayer,
        "bn": "sub!",
        "off": False,
        "Vd": "",
        "perim": "",
        "m": 1,
        "trise": "",
        "region": "",
        "dtemp": "",
        "mode": "No",
        "guardRingType": guardRingType,
        "guardRingDistance": guardRingDistance * 1e-6,
    }

    c = generate_gf_from_ihp(
        cell_name="dantenna", cell_params=params, function_name=dantennaIHP()
    )

    # add ports to the component
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(tech.LAYER.Metal1drawing),
        port_type="electrical",
        port_name_prefix="t",
        ports_on_short_side=True,
    )

    return c


@gf.cell(tags=["IHP", "diode", "antenna"])
def dpantenna(
    width: float = 0.78,
    length: float = 0.78,
    addRecLayer: Literal["t", "f"] = "t",
    guardRingType: Literal["none", "nwell"] = "none",
    guardRingDistance: float = 1,
) -> gf.Component:
    """Creates a dual-polarity antenna (dpantenna) structure.

    Generates a layout cell containing a rectangular antenna region with an
    optional recognition layer and an optional n-well guard ring. Parameters
    allow customization of the antenna geometry and the spacing between the
    antenna body and the surrounding guard ring.

    Args:
        width: Width of the antenna rectangle in microns.
        length: Length of the antenna rectangle in microns.
        addRecLayer: Whether to add a recognition layer. Valid values:
            - 't': Add recognition layer.
            - 'f': Do not add a recognition layer.
        guardRingType: Type of guard ring to include. Valid values:
            - 'none': No guard ring.
            - 'nwell': Surrounding n-well guard ring.
        guardRingDistance: Spacing between the antenna body and the n-well
            guard ring, in microns.

    Returns:
        gdsfactory.Component: The generated antenna component.
    """

    area = width * 1e-6 * length * 1e-6
    perimeter = 2 * (width * 1e-6 + length * 1e-6)
    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "Display": "Selected",
        "model": tech.techParams["dpantenna_model"],
        "Calculate": "a",
        "w": width * 1e-6,
        "l": length * 1e-6,
        "a": area,
        "p": perimeter,
        "addRecLayer": addRecLayer,
        "bn": "sub!",
        "off": False,
        "Vd": "",
        "perim": "",
        "m": 1,
        "trise": "",
        "region": "",
        "dtemp": "",
        "mode": "No",
        "guardRingType": guardRingType,
        "guardRingDistance": guardRingDistance * 1e-6,
    }

    c = generate_gf_from_ihp(
        cell_name="dpantenna", cell_params=params, function_name=dpantennaIHP()
    )

    # add ports to the component
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(tech.LAYER.Metal1drawing),
        port_type="electrical",
        port_name_prefix="DS",
        ports_on_short_side=True,
    )

    return c
