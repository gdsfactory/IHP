"""Resistor components for IHP PDK."""

from typing import Literal

import gdsfactory as gf

from .. import tech
from .ihp_pycell import CbResCalc, CbResCurrent, eng_string_to_float
from .ihp_pycell import rhigh as rhighIHP
from .ihp_pycell import rppd as rppdIHP
from .ihp_pycell import rsil as rsilIHP
from .utils import *


@gf.cell(tags=["IHP", "resistor", "high-r"])
def rhigh(
    length: float = 0.96,
    width: float = 0.5,
    bends: int = 0,
    polySpace: float = 0.18,
    numberOfSegments: int = 1,
    segmentConnection: Literal["None", "Serial", "Parallel"] = "Serial",
    segmentSpacing: float = 2,
    guardRingType: Literal["none", "nwell", "psub"] = "none",
    guardRingDistance: float = 1,
) -> gf.Component:
    """Create a high-resistance polysilicon resistor layout.

    This function generates a parametric high-resistance polysilicon resistor
    with configurable width, length, bends, and multiple segments. Optional
    guard rings can be added for isolation.

    Args:
        length: Length of the resistor in micrometers.
        width: Width of the resistor in micrometers.
        bends: Number of bends in the resistor path.
        polySpace: Spacing between polysilicon lines in micrometers.
        numberOfSegments: Number of resistor segments.
        segmentConnection: Connection type between segments. Options:
            - 'None': Segments not connected.
            - 'Serial': Segments connected in series.
            - 'Parallel': Segments connected in parallel.
        segmentSpacing: Spacing between segments in micrometers.
        guardRingType: Type of guard ring to include. Options:
            - 'none': No guard ring.
            - 'nwell': N-well guard ring.
            - 'psub': P-substrate guard ring.
        guardRingDistance: Distance between the resistor and guard ring in micrometers.

    Returns:
        gdsfactory.Component: The generated high-resistance polysilicon resistor layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "Display": "Selected",
        "Calculate": "l",  # TODO check what to do
        "Recommendation": "No",
        "model": tech.techParams["rhigh_model"],
        "R": CbResCalc(
            "R", 0, length * 1e-6, width * 1e-6, bends, polySpace * 1e-6, "rhigh"
        ),  # TODO Is this used?
        "w": width * 1e-6,  # Length in μm
        "l": length * 1e-6,  # Length in μm
        "b": bends,
        "ps": polySpace * 1e-6,
        "Imax": CbResCurrent(
            width * 1e-6, tech.techParams["epsilon2"], "rhighG2"
        ),  # TODO Is this used?
        "bn": "sub!",
        "Wmin": eng_string_to_float(tech.techParams["rhigh_minW"]) * 1e-6,
        "Lmin": eng_string_to_float(tech.techParams["rhigh_minL"]) * 1e-6,
        "PSmin": eng_string_to_float(tech.techParams["rhigh_minPS"]) * 1e-6,
        "Rspec": tech.techParams["rhigh_rspec"],
        "Rkspec": tech.techParams["rhigh_rkspec"],
        "Rzspec": tech.techParams["rhigh_rzspec"],
        "tc1": -2300e-6,  # hardcoded in the PCell
        "tc2": 2.1e-6,  # hardcoded in the PCell
        "PWB": "No",
        "m": 1,  # Multiplier
        "trise": 0,
        "NumberOfSegments": numberOfSegments,
        "SegmentConnection": segmentConnection,
        "SegmentSpacing": segmentSpacing * 1e-6,
        "guardRingType": guardRingType,
        "guardRingDistance": guardRingDistance * 1e-6,
    }

    c = generate_gf_from_ihp(
        cell_name="rhigh", cell_params=params, function_name=rhighIHP()
    )

    # add ports to the component
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(tech.LAYER.Metal1pin),
        port_type="electrical",
        ports_on_short_side=False,
    )

    return c


@gf.cell(tags=["IHP", "resistor", "unsilicided"])
def rppd(
    length: float = 0.5,
    width: float = 0.5,
    bends: int = 0,
    polySpace: float = 0.18,
    numberOfSegments: int = 1,
    segmentConnection: Literal["None", "Serial", "Parallel"] = "Serial",
    segmentSpacing: float = 2,
    guardRingType: Literal["none", "nwell", "psub"] = "none",
    guardRingDistance: float = 1,
) -> gf.Component:
    """Create a high-resistance polysilicon resistor layout.

    This function generates a parametric high-resistance polysilicon resistor
    with configurable width, length, bends, and multiple segments. Optional
    guard rings can be added for isolation.

    Args:
        length: Length of the resistor in micrometers.
        width: Width of the resistor in micrometers.
        bends: Number of bends in the resistor path.
        polySpace: Spacing between polysilicon lines in micrometers.
        numberOfSegments: Number of resistor segments.
        segmentConnection: Connection type between segments. Options:
            - 'None': Segments not connected.
            - 'Serial': Segments connected in series.
            - 'Parallel': Segments connected in parallel.
        segmentSpacing: Spacing between segments in micrometers.
        guardRingType: Type of guard ring to include. Options:
            - 'none': No guard ring.
            - 'nwell': N-well guard ring.
            - 'psub': P-substrate guard ring.
        guardRingDistance: Distance between the resistor and guard ring in micrometers.

    Returns:
        gdsfactory.Component: The generated high-resistance polysilicon resistor layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "Display": "Selected",
        "Calculate": "l",  # TODO check what to do
        "Recommendation": "No",
        "model": tech.techParams["rppd_model"],
        "R": CbResCalc(
            "R", 0, length * 1e-6, width * 1e-6, bends, polySpace * 1e-6, "rppd"
        ),  # TODO Is this used?
        "w": width * 1e-6,  # Length in μm
        "l": length * 1e-6,  # Length in μm
        "b": bends,
        "ps": polySpace * 1e-6,
        "Imax": CbResCurrent(
            width * 1e-6, tech.techParams["epsilon2"], "rppdG2"
        ),  # TODO Is this used?
        "bn": "sub!",
        "Wmin": eng_string_to_float(tech.techParams["rppd_minW"]) * 1e-6,
        "Lmin": eng_string_to_float(tech.techParams["rppd_minL"]) * 1e-6,
        "PSmin": eng_string_to_float(tech.techParams["rppd_minPS"]) * 1e-6,
        "Rspec": tech.techParams["rppd_rspec"],
        "Rkspec": tech.techParams["rppd_rkspec"],
        "Rzspec": tech.techParams["rppd_rzspec"],
        "tc1": -170e-6,  # hardcoded in the PCell
        "tc2": 0.4e-6,  # hardcoded in the PCell
        "PWB": "No",
        "m": 1,  # Multiplier
        "trise": 0,
        "NumberOfSegments": numberOfSegments,
        "SegmentConnection": segmentConnection,
        "SegmentSpacing": segmentSpacing * 1e-6,
        "guardRingType": guardRingType,
        "guardRingDistance": guardRingDistance * 1e-6,
    }

    c = generate_gf_from_ihp(
        cell_name="rppd", cell_params=params, function_name=rppdIHP()
    )

    # add ports to the component
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(tech.LAYER.Metal1pin),
        port_type="electrical",
        ports_on_short_side=False,
    )

    return c


@gf.cell(tags=["IHP", "resistor", "silicided"])
def rsil(
    length: float = 0.5,
    width: float = 0.5,
    polySpace: float = 0.18,
    resistance: float = 24.9,
    numberOfSegments: int = 1,
    segmentConnection: Literal["None", "Serial", "Parallel"] = "Serial",
    segmentSpacing: float = 2,
    guardRingType: Literal["none", "nwell", "psub"] = "none",
    guardRingDistance: float = 1,
) -> gf.Component:
    """Create a high-resistance polysilicon resistor layout (RSIL type).

    This function generates a parametric high-resistance polysilicon resistor
    of RSIL type with configurable width, length, target resistance, bends,
    multiple segments, and optional guard rings for isolation.

    Args:
        length: Length of the resistor in micrometers.
        width: Width of the resistor in micrometers.
        polySpace: Spacing between polysilicon lines in micrometers.
        resistance: Target resistance value in ohms.
        numberOfSegments: Number of resistor segments.
        segmentConnection: Connection type between segments. Options:
            - 'None': Segments not connected.
            - 'Serial': Segments connected in series.
            - 'Parallel': Segments connected in parallel.
        segmentSpacing: Spacing between segments in micrometers.
        guardRingType: Type of guard ring to include. Options:
            - 'none': No guard ring.
            - 'nwell': N-well guard ring.
            - 'psub': P-substrate guard ring.
        guardRingDistance: Distance between the resistor and guard ring in micrometers.

    Returns:
        gdsfactory.Component: The generated RSIL polysilicon resistor layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "Display": "Selected",
        "Calculate": "l",  # TODO check what to do
        "Recommendation": "No",
        "model": tech.techParams["rsil_model"],
        "R": resistance,  # TODO IHP function defines it as user parameter but also calculates it
        "w": width * 1e-6,  # Length in μm
        "l": length * 1e-6,  # Length in μm
        "ps": polySpace * 1e-6,
        "Imax": CbResCurrent(
            width * 1e-6, tech.techParams["epsilon2"], "rsilG2"
        ),  # TODO Is this used?
        "bn": "sub!",
        "Wmin": eng_string_to_float(tech.techParams["rsil_minW"]) * 1e-6,
        "Lmin": eng_string_to_float(tech.techParams["rsil_minL"]) * 1e-6,
        "PSmin": eng_string_to_float(tech.techParams["rsil_minPS"]) * 1e-6,
        "Rspec": tech.techParams["rsil_rspec"],
        "Rkspec": tech.techParams["rsil_rkspec"],
        "Rzspec": tech.techParams["rsil_rzspec"],
        "tc1": -170e-6,  # hardcoded in the PCell
        "tc2": 0.4e-6,  # hardcoded in the PCell
        "PWB": "No",
        "m": 1,  # Multiplier
        "trise": 0,
        "NumberOfSegments": numberOfSegments,
        "SegmentConnection": segmentConnection,
        "SegmentSpacing": segmentSpacing * 1e-6,
        "guardRingType": guardRingType,
        "guardRingDistance": guardRingDistance * 1e-6,
    }

    c = generate_gf_from_ihp(
        cell_name="rsil", cell_params=params, function_name=rsilIHP()
    )

    # add ports to the component
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(tech.LAYER.Metal1pin),
        port_type="electrical",
        ports_on_short_side=False,
    )

    return c


if __name__ == "__main__":
    # Test the components
    c1 = rsil(width=1.0, length=10.0)
    c1.show()

    c2 = rppd(width=0.8, length=20.0)
    c2.show()

    c3 = rhigh(width=1.4, length=50.0)
    c3.show()
