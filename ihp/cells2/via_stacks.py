"""Via stack components for IHP PDK. Also includes NoFillerStack."""

from typing import Literal

import gdsfactory as gf

from .. import tech
from .ihp_pycell import NoFillerStack as no_filler_stackIHP
from .ihp_pycell import via_stack as via_stackIHP
from .utils import *


@gf.cell
def via_stack(
    bottom_layer: Literal[
        "Activ",
        "GatPoly",
        "Metal1",
        "Metal2",
        "Metal3",
        "Metal4",
        "Metal5",
        "TopMetal1",
        "TopMetal2",
    ] = "Metal1",
    top_layer: Literal[
        "Activ",
        "GatPoly",
        "Metal1",
        "Metal2",
        "Metal3",
        "Metal4",
        "Metal5",
        "TopMetal1",
        "TopMetal2",
    ] = "Metal2",
    vn_columns: int = 2,
    vn_rows: int = 2,
    vt1_columns: int = 1,
    vt1_rows: int = 1,
    vt2_columns: int = 1,
    vt2_rows: int = 1,
) -> gf.Component:
    """Create a via stack component.

    This function generates a layout for a via stack connecting a bottom
    layer to a top layer. The number of columns and rows for standard vias
    (Via1-Via4) and top vias (TopVia1, TopVia2) can be specified.

    Args:
        bottom_layer: Bottom layer name. Options: 'Activ', 'GatPoly', 'Metal1'-'Metal5', 'TopMetal1', 'TopMetal2'.
        top_layer: Top layer name. Options: 'Activ', 'GatPoly', 'Metal1'-'Metal5', 'TopMetal1', 'TopMetal2'.
        vn_columns: Number of columns for standard vias (Via1-Via4).
        vn_rows: Number of rows for standard vias.
        vt1_columns: Number of columns for TopVia1.
        vt1_rows: Number of rows for TopVia1.
        vt2_columns: Number of columns for TopVia2.
        vt2_rows: Number of rows for TopVia2.

    Returns:
        gdsfactory.Component: The generated via stack test layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "Display": "Selected",
        "b_layer": bottom_layer,
        "t_layer": top_layer,
        "vn_columns": vn_columns,
        "vn_rows": vn_rows,
        "vt1_columns": vt1_columns,
        "vt1_rows": vt1_rows,
        "vt2_columns": vt2_columns,
        "vt2_rows": vt2_rows,
    }

    c = generate_gf_from_ihp(
        cell_name="via_stack", cell_params=params, function_name=via_stackIHP()
    )

    # add ports to the component
    layer_map = {  # necessary for mapping layer names to tech layers
        "Activ": tech.LAYER.Activdrawing,
        "GatPoly": tech.LAYER.GatPolydrawing,
        "Metal1": tech.LAYER.Metal1drawing,
        "Metal2": tech.LAYER.Metal2drawing,
        "Metal3": tech.LAYER.Metal3drawing,
        "Metal4": tech.LAYER.Metal4drawing,
        "Metal5": tech.LAYER.Metal5drawing,
        "TopMetal1": tech.LAYER.TopMetal1drawing,
        "TopMetal2": tech.LAYER.TopMetal2drawing,
    }

    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(layer_map[bottom_layer]),
        port_type="electrical",
        ports_on_short_side=False,
        auto_rename_ports=False,
    )
    c.ports["e1"].name = "bottom"
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(layer_map[top_layer]),
        port_type="electrical",
        ports_on_short_side=False,
        auto_rename_ports=False,
    )
    c.ports["e1"].name = "top"

    return c


@gf.cell
def no_filler_stack(
    width: int = 10,
    length: int = 10,
    noAct: Literal["Yes", "No"] = "Yes",  # no active filler
    noGP: Literal["Yes", "No"] = "Yes",  # no GatePoly filler
    noM1: Literal["Yes", "No"] = "Yes",  # no M1 filler
    noM2: Literal["Yes", "No"] = "Yes",  # no M2 filler
    noM3: Literal["Yes", "No"] = "Yes",  # no M3 filler
    noM4: Literal["Yes", "No"] = "Yes",  # no M4 filler
    noM5: Literal["Yes", "No"] = "Yes",  # no M5 filler
    noTM1: Literal["Yes", "No"] = "Yes",  # no TM1 filler
    noTM2: Literal["Yes", "No"] = "Yes",  # no TM2 filler
) -> gf.Component:
    """Create a NoFiller via stack test component.

    This function generates a via stack layout without filler structures
    for the selected layers. Each layer can be individually excluded
    from filler insertion using Yes/No flags.

    Args:
        width: Device width in micrometers.
        length: Device length in micrometers.
        noAct: Exclude filler for the active layer. Options: 'Yes', 'No'.
        noGP: Exclude filler for the GatePoly layer. Options: 'Yes', 'No'.
        noM1: Exclude filler for Metal1. Options: 'Yes', 'No'.
        noM2: Exclude filler for Metal2. Options: 'Yes', 'No'.
        noM3: Exclude filler for Metal3. Options: 'Yes', 'No'.
        noM4: Exclude filler for Metal4. Options: 'Yes', 'No'.
        noM5: Exclude filler for Metal5. Options: 'Yes', 'No'.
        noTM1: Exclude filler for TopMetal1. Options: 'Yes', 'No'.
        noTM2: Exclude filler for TopMetal2. Options: 'Yes', 'No'.

    Returns:
        gdsfactory.Component: The generated NoFiller via stack layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "Display": "Selected",
        "w": width * 1e-6,
        "l": length * 1e-6,
        "minLW": 10e-9,  # hardcoded not in tech file
        "noAct": noAct,
        "noGP": noGP,
        "noM1": noM1,
        "noM2": noM2,
        "noM3": noM3,
        "noM4": noM4,
        "noM5": noM5,
        "noTM1": noTM1,
        "noTM2": noTM2,
    }

    c = generate_gf_from_ihp(
        cell_name="no_filler_stack",
        cell_params=params,
        function_name=no_filler_stackIHP(),
    )
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    # for i, port in enumerate(c.ports):
    #     port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
    return c


if __name__ == "__main__":
    # Test the components
    c = via_stack(bottom_layer="Metal1", top_layer="Metal5")
    c.show()
