"""Capacitor components for IHP PDK."""

from typing import Literal

import gdsfactory as gf

from .. import tech
from .ihp_pycell import CbCapCalc, eng_string
from .ihp_pycell import SVaricap as SVaricapIHP
from .ihp_pycell import cmim as cmimIHP
from .ihp_pycell import rfcmim as rfcmimIHP
from .utils import *


@gf.cell(tags=["IHP", "capacitor", "mim"])
def cmim(
    width: float = 6.99,
    length: float = 6.99,
    guardRingType: Literal["none", "psub", "nwell"] = "none",
    guardRingDistance: float = 1,
) -> gf.Component:
    """Create a MIM (Metal-Insulator-Metal) capacitor.

    This function generates a layout cell for a MIM capacitor with optional
    guard rings. The capacitor dimensions and the spacing to the guard ring
    can be customized.

    Args:
        width: Width of the capacitor in micrometers.
        length: Length of the capacitor in micrometers.
        guardRingType: Type of guard ring to include. Options:
            - 'none': No guard ring.
            - 'psub': P-substrate guard ring surrounding the capacitor.
            - 'nwell': N-well guard ring surrounding the capacitor.
        guardRingDistance: Spacing between the capacitor body and the guard ring, in micrometers.

    Returns:
        gdsfactory.Component: The generated MIM capacitor layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "Display": "Selected",
        "Calculate": "w&l",
        "model": tech.techParams["cmim_model"],
        "C": CbCapCalc(
            "C", 0, width * 1e-6, length * 1e-6, "cmim"
        ),  # TODO Is this used?
        "w": eng_string(width * 1e-6),  # Width as engineering string
        "l": eng_string(length * 1e-6),  # Length as engineering string
        "Cspec": tech.techParams["cmim_caspec"],
        "Wmin": tech.techParams["cmim_minLW"],
        "Lmin": tech.techParams["cmim_minLW"],
        "Cmax": tech.techParams["cmim_maxC"],
        "ic": "",
        "m": "1",  # Multiplier as string
        "trise": "",
        "guardRingType": guardRingType,
        "guardRingDistance": eng_string(guardRingDistance * 1e-6),
    }

    c = generate_gf_from_ihp(
        cell_name="cmim", cell_params=params, function_name=cmimIHP()
    )

    # add ports to the component
    # no pin layers for cmim, so we use drawing layers
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(tech.LAYER.Metal5drawing),
        port_type="electrical",
        ports_on_short_side=True,
    )
    c.ports["e1"].name = "B"
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(tech.LAYER.TopMetal1drawing),
        port_type="electrical",
        ports_on_short_side=True,
        auto_rename_ports=False,
    )
    c.ports["e1"].name = "T"
    c.ports["B"].orientation = 0
    c.ports["T"].orientation = 180

    return c


@gf.cell(tags=["IHP", "capacitor", "mim", "rf"])
def rfcmim(
    width: float = 6.99,
    length: float = 6.99,
    feed_width: float = 3,
) -> gf.Component:
    """Create an RF MIM (Metal-Insulator-Metal) capacitor with optimized layout.

    This function generates a layout for an RF MIM capacitor with a feed
    line. The capacitor dimensions and feed width can be customized.

    Args:
        width: Width of the capacitor in micrometers.
        length: Length of the capacitor in micrometers.
        feed_width: Width of the feed line connecting to the capacitor, in micrometers.

    Returns:
        gdsfactory.Component: The generated RF MIM capacitor layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "Display": "Selected",
        "Calculate": "C",
        "model": tech.techParams["rfcmim_model"],
        "C": CbCapCalc(
            "C", 0, width * 1e-6, length * 1e-6, "rfcmim"
        ),  # TODO Is this used?
        "w": eng_string(width * 1e-6),  # Width as engineering string
        "l": eng_string(length * 1e-6),  # Length as engineering string
        "wfeed": eng_string(feed_width * 1e-6),
        "Cspec": tech.techParams["rfcmim_caspec"],
        "Wmin": tech.techParams["rfcmim_minLW"],
        "Lmin": tech.techParams["rfcmim_minLW"],
        "Cmax": tech.techParams["rfcmim_maxC"],
        "ic": "",
        "m": "1",  # Multiplier as string
        "trise": "",
    }

    c = generate_gf_from_ihp(
        cell_name="rfcmim", cell_params=params, function_name=rfcmimIHP()
    )

    # add ports to the component
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(tech.LAYER.Metal5pin),
        port_type="electrical",
        ports_on_short_side=False,
        auto_rename_ports=False,
    )
    c.ports["e1"].name = "MINUS"
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(tech.LAYER.TopMetal1pin),
        port_type="electrical",
        ports_on_short_side=False,
        auto_rename_ports=False,
    )
    c.ports["e1"].name = "PLUS"
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(tech.LAYER.Metal1pin),
        port_type="electrical",
        ports_on_short_side=True,
        auto_rename_ports=False,
    )
    c.ports["e1"].name = "TIE"

    return c


@gf.cell(tags=["IHP", "varicap", "hv"])
def svaricap(
    width: Literal["3.74u", "9.74u"] = "9.74u",
    length: Literal["0.3u", "0.8u"] = "0.8u",
    Nx: int = 1,
    guardRingType: Literal["none", "nwell"] = "none",
    guardRingDistance: float = 1,
) -> gf.Component:
    """Create a MOS varicap (variable capacitor) layout.

    This function generates a parametric MOS varicap with optional n-well
    guard rings. The device geometry and number of fingers can be customized.

    Args:
        width: Width of the varicap. Must be one of: '3.74u', '9.74u'.
        length: Length of the varicap. Must be one of: '0.3u', '0.8u'.
        Nx: Number of fingers for the varicap.
        guardRingType: Type of guard ring to include. Options:
            - 'none': No guard ring.
            - 'nwell': N-well guard ring.
        guardRingDistance: Spacing between the varicap body and the guard ring, in micrometers.

    Returns:
        gdsfactory.Component: The generated varicap layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "Display": "Selected",
        "model": tech.techParams["SVaricap_model"],
        "w": width,  # Width already as string like "3.74u"
        "l": length,  # Length already as string like "0.3u"
        "Nx": Nx,
        "bn": "sub!",
        "trise": "",
        "guardRingType": guardRingType,
        "guardRingDistance": eng_string(guardRingDistance * 1e-6),
    }

    c = generate_gf_from_ihp(
        cell_name="svaricap", cell_params=params, function_name=SVaricapIHP()
    )

    # add ports to the component
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(tech.LAYER.Metal1pin),
        port_type="electrical",
        ports_on_short_side=True,
    )
    c.ports["e1"].orientation = 90
    c.ports["e2"].orientation = 270
    c.ports["e3"].orientation = 180

    return c


if __name__ == "__main__":
    # Test the components
    c1 = cmim(width=10, length=10)
    c1.show()

    c2 = rfcmim(width=20, length=20)
    c2.show()
