from typing import Literal

import gdsfactory as gf

from .. import tech
from .ihp_pycell import inductor2 as inductor2IHP
from .ihp_pycell import inductor3 as inductor3IHP
from .utils import *


@gf.cell(tags=["IHP", "inductor"])
def inductor2(
    width: float = 2,
    space: float = 2.1,
    distance: float = 15.48,
    resistance: float = 1,
    inductance: float = 1,
    num_turns: int = 1,
    block_qrc: bool = True,
    subE: bool = False,
    guardRingType: Literal["none", "psub", "nwell"] = "none",
    guardRingDistance: float = 1,
) -> gf.Component:
    """Create a parametric inductor layout.

    This function generates a planar inductor with customizable width,
    spacing, number of turns, and optional guard rings. The layout can
    also include blocking of QRC structures and substrate connections.

    Args:
        width: Width of the inductor trace in micrometers.
        space: Spacing between turns of the inductor in micrometers.
        distance: Total distance of the inductor layout in micrometers.
        resistance: Target series resistance in Ohms.
        inductance: Target inductance in nH (used for layout optimization).
        num_turns: Number of turns in the inductor.
        block_qrc: Whether to block QRC (quasi-resistor-capacitor) structures.
        subE: Whether to connect to substrate for shielding or grounding.
        guardRingType: Type of guard ring to include. Options:
            - 'none': No guard ring.
            - 'psub': P-substrate guard ring.
            - 'nwell': N-well guard ring.
        guardRingDistance: Spacing between the inductor and the guard ring, in micrometers.

    Returns:
        gdsfactory.Component: The generated inductor layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "Display": "Selected",
        "model": "inductor2",
        "w": width * 1e-6,
        "s": space * 1e-6,
        "d": distance * 1e-6,
        "r": resistance * 1e-3,
        "l": inductance * 1e-9,
        "nr_r": num_turns,
        "blockqrc": block_qrc,
        "subE": subE,
        "lEstim": 33.303 * 1e-9,
        "rEstim": 577.7 * 1e-3,
        "Wmin": 2 * 1e-6,
        "Smin": 2.1 * 1e-6,
        "Dmin": 15.48 * 1e-6,
        "minNr_t": 1,
        "mergeStat": 16,
        "guardRingType": guardRingType,
        "guardRingDistance": guardRingDistance * 1e-6,
    }

    c = generate_gf_from_ihp(
        cell_name="inductor2", cell_params=params, function_name=inductor2IHP()
    )

    # add ports to the component
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(tech.LAYER.TopMetal2pin),
        port_type="electrical",
        ports_on_short_side=True,
    )
    for port in c.ports:
        port.orientation = 270  # all ports should face downwards
    c.ports["e1"].name = "LB"
    c.ports["e2"].name = "LA"

    return c


@gf.cell(tags=["IHP", "inductor"])
def inductor3(
    width: float = 2,
    space: float = 2.1,
    distance: float = 25.84,
    resistance: float = 1,
    inductance: float = 1,
    num_turns: int = 2,
    block_qrc: bool = True,
    subE: bool = False,
    guardRingType: Literal["none", "psub", "nwell"] = "none",
    guardRingDistance: float = 1,
) -> gf.Component:
    """Create a parametric inductor layout.

    This function generates a planar inductor with customizable width,
    spacing, total distance, number of turns, and optional guard rings.
    The layout can also include blocking of QRC structures and substrate
    connections.

    Args:
        width: Width of the inductor trace in micrometers.
        space: Spacing between turns of the inductor in micrometers.
        distance: Total distance of the inductor layout in micrometers.
        resistance: Target series resistance in Ohms.
        inductance: Target inductance in nH (used for layout optimization).
        num_turns: Number of turns in the inductor.
        block_qrc: Whether to block QRC (quasi-resistor-capacitor) structures.
        subE: Whether to connect to substrate for shielding or grounding.
        guardRingType: Type of guard ring to include. Options:
            - 'none': No guard ring.
            - 'psub': P-substrate guard ring.
            - 'nwell': N-well guard ring.
        guardRingDistance: Spacing between the inductor and the guard ring, in micrometers.

    Returns:
        gdsfactory.Component: The generated inductor layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "Display": "Selected",
        "model": "inductor3",
        "w": width * 1e-6,
        "s": space * 1e-6,
        "d": distance * 1e-6,
        "r": resistance * 1e-3,
        "l": inductance * 1e-9,
        "nr_r": num_turns,
        "blockqrc": block_qrc,
        "subE": subE,
        "lEstim": 33.303 * 1e-9,
        "rEstim": 577.7 * 1e-3,
        "Wmin": 2 * 1e-6,
        "Smin": 2.1 * 1e-6,
        "Dmin": 25.84 * 1e-6,
        "minNr_t": 2,
        "mergeStat": 16,
        "guardRingType": guardRingType,
        "guardRingDistance": guardRingDistance * 1e-6,
    }

    c = generate_gf_from_ihp(
        cell_name="inductor3", cell_params=params, function_name=inductor3IHP()
    )

    # add ports to the component
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(tech.LAYER.TopMetal1pin),
        port_type="electrical",
        ports_on_short_side=True,
    )
    c.ports["e1"].name = "LA"
    c.ports["e2"].name = "LB"
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(tech.LAYER.TopMetal2pin),
        port_type="electrical",
        ports_on_short_side=True,
        auto_rename_ports=False,
    )
    c.ports["e1"].name = "LC"

    for port in c.ports:
        port.orientation = 270  # all ports should face downwards

    return c
