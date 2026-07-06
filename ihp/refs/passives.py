"""Passive components (varicaps, ESD, taps, seal rings) for IHP PDK."""

from typing import Literal

import gdsfactory as gf

from .. import tech
from .ihp_pycell import CbTapCalc, eng_string_to_float
from .ihp_pycell import esd as esdIHP
from .ihp_pycell import ntap1 as ntap1IHP
from .ihp_pycell import ptap1 as ptap1IHP
from .ihp_pycell import sealring as sealringIHP
from .utils import *


@gf.cell(tags=["IHP", "esd", "lv"])
def esd(
    model: Literal[
        "diodevdd_2kv",
        "diodevss_2kv",
        "diodevdd_4kv",
        "diodevss_4kv",
        "nmoscl_2",
        "nmoscl_4",
    ] = "diodevdd_2kv",
) -> gf.Component:
    """Create an ESD protection device layout.

    This function generates an electrostatic discharge (ESD) protection device
    using the specified model. Available models include diodes and NMOS clamps
    for different voltage ratings.

    Args:
        model: Device model name. Options:
            - 'diodevdd_2kv': Diode from VDD for 2 kV rating.
            - 'diodevss_2kv': Diode to VSS for 2 kV rating.
            - 'diodevdd_4kv': Diode from VDD for 4 kV rating.
            - 'diodevss_4kv': Diode to VSS for 4 kV rating.
            - 'nmoscl_2': NMOS clamp for 2 kV rating.
            - 'nmoscl_4': NMOS clamp for 4 kV rating.

    Returns:
        gdsfactory.Component: The generated ESD protection layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "Display": "Selected",
        "model": model,
    }

    c = generate_gf_from_ihp(
        cell_name="esd", cell_params=params, function_name=esdIHP()
    )

    ## add ports to the component
    # default direction should be away from the device center
    # set port names and orientations based on model

    if model == "diodevdd_2kv":
        gf.add_ports.add_ports_from_boxes(
            c,
            pin_layer=(tech.LAYER.Metal1pin),
            port_type="electrical",
            ports_on_short_side=True,
        )
        c.ports["e1"].orientation = 270
        c.ports["e1"].name = "VSS"
        gf.add_ports.add_ports_from_boxes(
            c,
            pin_layer=(tech.LAYER.Metal2pin),
            port_type="electrical",
            ports_on_short_side=True,
            auto_rename_ports=False,
        )
        c.ports["e1"].orientation = 180
        c.ports["e1"].name = "PAD"
        c.ports["e2"].orientation = 0
        c.ports["e2"].name = "VDD"

    elif model == "diodevdd_4kv":
        gf.add_ports.add_ports_from_boxes(
            c,
            pin_layer=(tech.LAYER.Metal1pin),
            port_type="electrical",
            ports_on_short_side=True,
        )
        c.ports["e1"].orientation = 270
        c.ports["e1"].name = "VSS"
        gf.add_ports.add_ports_from_boxes(
            c,
            pin_layer=(tech.LAYER.Metal2pin),
            port_type="electrical",
            ports_on_short_side=True,
            auto_rename_ports=False,
        )
        c.ports["e1"].orientation = 0
        c.ports["e1"].name = "VDD"
        c.ports["e2"].orientation = 180
        c.ports["e2"].name = "PAD"

    elif model in ["diodevss_2kv", "diodevss_4kv"]:
        gf.add_ports.add_ports_from_boxes(
            c,
            pin_layer=(tech.LAYER.Metal1pin),
            port_type="electrical",
            ports_on_short_side=True,
        )
        c.ports["e1"].orientation = 90
        c.ports["e1"].name = "VDD"
        gf.add_ports.add_ports_from_boxes(
            c,
            pin_layer=(tech.LAYER.Metal2pin),
            port_type="electrical",
            ports_on_short_side=True,
            auto_rename_ports=False,
        )
        c.ports["e1"].orientation = 180
        c.ports["e1"].name = "PAD"
        c.ports["e2"].orientation = 0
        c.ports["e2"].name = "VSS"

    else:  # NMOS clamp
        gf.add_ports.add_ports_from_boxes(
            c,
            pin_layer=(tech.LAYER.Metal3pin),
            port_type="electrical",
            ports_on_short_side=True,
        )
        c.ports["e1"].orientation = 270
        c.ports["e1"].name = "VSS"
        c.ports["e2"].orientation = 90
        c.ports["e2"].name = "VDD"

    return c


@gf.cell(tags=["IHP", "tap", "p-type"])
def ptap1(
    width: float = 0.78,
    length: float = 0.78,
) -> gf.Component:
    """Create a P+ substrate tap layout.

    This function generates a parametric P+ substrate tap with configurable
    width and length. It is typically used for connecting the P-substrate
    to a reference potential.

    Args:
        width: Width of the tap in micrometers.
        length: Length of the tap in micrometers.

    Returns:
        gdsfactory.Component: The generated P+ substrate tap layout.
    """

    area = width * length
    perimeter = 2 * (width + length)
    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "Display": "Selected",
        "Calculate": "R,A",
        "R": CbTapCalc(
            "R", 0, length * 1e-6, width * 1e-6, "ptap1"
        ),  # TODO Is this used?
        "w": width * 1e-6,  # Length in μm
        "l": length * 1e-6,  # Length in μm
        "A": area,
        "Perim": perimeter,
        "Rspec": 0.980 * 1e-9,  # hardcoded in the PCell
        "Wmin": eng_string_to_float(tech.techParams["ptap1_minLW"]),
        "Lmin": eng_string_to_float(tech.techParams["ptap1_minLW"]),
        "m": 1,
    }

    c = generate_gf_from_ihp(
        cell_name="ptap1", cell_params=params, function_name=ptap1IHP()
    )

    # add ports to the component
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(tech.LAYER.Metal1pin),
        port_type="electrical",
        ports_on_short_side=True,
    )

    return c


@gf.cell(tags=["IHP", "tap", "n-type"])
def ntap1(
    width=0.78,
    length=0.78,
) -> gf.Component:
    """Create an N+ substrate tap.

    Args:
        width: Width of the tap in micrometers.
        length: Length of the tap in micrometers.
        rows: Number of contact rows.
        cols: Number of contact columns.

    Returns:
        Component with N+ tap layout.
    """
    area = width * length
    perimeter = 2 * (width + length)
    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "Display": "Selected",
        "Calculate": "R,A",
        "R": CbTapCalc(
            "R", 0, length * 1e-6, width * 1e-6, "ntap1"
        ),  # TODO Is this used?
        "w": width * 1e-6,  # Length in μm
        "l": length * 1e-6,  # Length in μm
        "A": area,
        "Perim": perimeter,
        "Rspec": 0.980 * 1e-9,  # hardcoded in the PCell
        "Wmin": eng_string_to_float(tech.techParams["ntap1_minLW"]),
        "Lmin": eng_string_to_float(tech.techParams["ntap1_minLW"]),
        "m": 1,
    }

    c = generate_gf_from_ihp(
        cell_name="ntap1", cell_params=params, function_name=ntap1IHP()
    )

    # add ports to the component
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(tech.LAYER.Metal1pin),
        port_type="electrical",
        ports_on_short_side=True,
    )

    return c


@gf.cell(tags=["IHP", "sealring"])
def sealring(
    width: float = 400.0,
    height: float = 400.0,
    addLabel: Literal["nil", "t"] = "nil",
    addSlit: Literal["nil", "t"] = "nil",
    edgeBox: float = 25.0,
) -> gf.Component:
    """Create a seal ring for die protection.

    This function generates a parametric seal ring around the die with optional
    label and slit features. The seal ring helps protect the chip from mechanical
    stress and contamination.

    Args:
        width: Inner width of the seal ring in micrometers.
        height: Inner height of the seal ring in micrometers.
        addLabel: Include label on the seal ring. Options: 'nil' (no label), 't' (add label).
        addSlit: Include slit in the seal ring. Options: 'nil' (no slit), 't' (add slit).
        edgeBox: Distance from die edge to the seal ring in micrometers.

    Returns:
        gdsfactory.Component: The generated seal ring layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "Display": "Selected",
        "l": width * 1e-6,  # Length in μm
        "w": height * 1e-6,  # Length in μm
        "addLabel": addLabel,
        "addSlit": addSlit,
        "Wmin": eng_string_to_float(tech.techParams["sealring_complete_minW"]),
        "Lmin": eng_string_to_float(tech.techParams["sealring_complete_minL"]),
        "edgeBox": edgeBox * 1e-6,
    }

    c = generate_gf_from_ihp(
        cell_name="sealring", cell_params=params, function_name=sealringIHP()
    )

    # add ports to the component
    # ports should be added manually if needed

    return c


if __name__ == "__main__":
    # Test the components

    c2 = esd(width=100.0, length=0.5, nf=20)
    c2.show()

    c3 = ptap1(width=2.0, length=2.0, rows=2, cols=2)
    c3.show()

    c4 = sealring(width=500, height=500, ring_width=10)
    c4.show()
