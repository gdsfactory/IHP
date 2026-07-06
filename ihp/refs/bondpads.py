"""Bondpad components for IHP PDK."""

from typing import Literal

import gdsfactory as gf

from .. import tech
from .ihp_pycell import bondpad as bondpadIHP
from .utils import *


@gf.cell(tags=["IHP", "bondpad"])
def bondpad(
    shape: Literal["octagon", "square", "circle"] = "octagon",
    stack: Literal["t", "nil"] = "t",
    fillMetals: Literal["t", "nil"] = "nil",
    flipChip: Literal["yes", "no"] = "no",
    diameter: float = 80.0,
    hwQuota: float = 1,
    topMetal: Literal["TM1", "TM2"] = "TM2",
    bottomMetal: Literal["1", "2", "3", "4", "5", "TM1"] = "3",
    addFillerEx: Literal["t", "nil"] = "nil",
    passEncl: float = 2.1,
    padType: Literal["bondpad", "probepad"] = "bondpad",
) -> gf.Component:
    """Create a bondpad for wire bonding or flip-chip connection.

    This function generates a parametric bondpad with configurable shape,
    metal stack, size, passivation, filler, and flip-chip options.

    Args:
        shape: Shape of the bondpad. Options: 'octagon', 'square', 'circle'.
        stack: Stack all metal layers from bottom to top ('t' or 'nil').
        fillMetals: Add metal fill patterns ('t' for yes, 'nil' for no).
        flipChip: Enable flip-chip configuration ('yes' or 'no').
        diameter: Diameter or size of the bondpad in micrometers.
        hwQuota: Height/width quota for pad design rules.
        topMetal: Name of the top metal layer. Options: 'TM1', 'TM2'.
        bottomMetal: Name of the bottom metal layer. Options: '1', '2', '3', '4', '5', 'TM1'.
        addFillerEx: Exclude metal filler ('t' or 'nil').
        passEncl: Passivation enclosure around the pad, in micrometers.
        padType: Type of pad. Options: 'bondpad', 'probepad'.

    Returns:
        gdsfactory.Component: The generated bondpad layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "model": "bondpad",  # hardcoded for bondpad
        "Display": "Selected",
        "shape": shape,
        "stack": stack,
        "fill": fillMetals,
        "FlipChip": flipChip,
        "diameter": diameter * 1e-6,
        "hwquota": hwQuota,
        "topMetal": topMetal,
        "bottomMetal": bottomMetal,
        "addFillerEx": addFillerEx,
        "passEncl": passEncl * 1e-6,
        "padType": padType,
        "padPin": "PAD",
    }

    c = generate_gf_from_ihp(
        cell_name="bondpad", cell_params=params, function_name=bondpadIHP()
    )
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    # for i, port in enumerate(c.ports):
    #     port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
    return c


@gf.cell(tags=["IHP", "bondpad", "array"])
def bondpad_array(
    n_pads: int = 4,
    pad_pitch: float = 100.0,
    pad_diameter: float = 68.0,
    shape: Literal["octagon", "square", "circle"] = "octagon",
    stack_metals: Literal["t", "nil"] = "t",
) -> gf.Component:
    """Create an array of bondpads.

    Args:
        n_pads: Number of bondpads.
        pad_pitch: Pitch between bondpad centers in micrometers.
        pad_diameter: Diameter of each bondpad in micrometers.
        shape: Shape of the bondpads.
        stack_metals: Stack all metal layers.

    Returns:
        Component with bondpad array.
    """
    c = gf.Component()

    for i in range(n_pads):
        pad = bondpad(
            shape=shape,
            stack=stack_metals,
            diameter=pad_diameter,
        )
        pad_ref = c.add_ref(pad)
        pad_ref.movex(i * pad_pitch)

    return c


if __name__ == "__main__":
    # Test the components
    c1 = bondpad(shape="octagon")
    c1.show()

    c2 = bondpad(shape="square", flip_chip=True)
    c2.show()

    c3 = bondpad_array(n_pads=6)
    c3.show()
