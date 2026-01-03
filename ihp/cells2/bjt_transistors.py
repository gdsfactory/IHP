import gdsfactory as gf

from .. import tech
from .ihp_pycell import npn13G2 as npn13G2IHP
from .ihp_pycell import npn13G2L as npn13G2LIHP
from .ihp_pycell import npn13G2V as npn13G2VIHP
from .ihp_pycell import pnpMPA as pnpMPAIHP
from .utils import *


@gf.cell
def npn13G2(
    STI: float = 0.44,
    baspolyx: float = 0.3,
    bipwinx: float = 0.07,
    bipwiny: float = 0.1,
    empolyx: float = 0.15,
    empolyy: float = 0.18,
    emitter_length: float = 0.9,
    emitter_width: float = 0.7,
    Nx: int = 1,
    Ny: int = 1,
    text: str = "npn13G2",
    CMetY1: float = 0,
    CMetY2: float = 0,
) -> gf.Component:
    """Returns the IHP npn13G2 BJT transistor as a gdsfactory Component.

    This function generates a parametric layout of the npn13G2 heterojunction
    bipolar transistor (HBT) from the IHP SG13G2 process. Geometry parameters
    control the emitter, base, and implant enclosure sizes, while Nx and Ny
    define the emitter finger array configuration.

    Args:
        STI: STI enclosure around the active device, in microns.
        baspolyx: Base poly enclosure in the x-direction, in microns.
        bipwinx: BIP window enclosure in the x-direction, in microns.
        bipwiny: BIP window enclosure in the y-direction, in microns.
        empolyx: Emitter poly enclosure in the x-direction, in microns.
        empolyy: Emitter poly enclosure in the y-direction, in microns.
        emitter_length: Length of each emitter finger, in microns.
        emitter_width: Width of each emitter finger, in microns.
        Nx: Number of emitter fingers.
        Ny: Number of emitter rows (not used by current IHP PyCell implementation).
        text: Label text to place on the device.
        CMetY1: Optional metal extension on the collector side (lower side), in microns.
        CMetY2: Optional metal extension on the collector side (upper side), in microns.

    Returns:
        gdsfactory.Component: The generated npn13G2 transistor layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "Display": "Selected",
        "model": tech.techParams["npn13G2_model"],
        "Nx": Nx,
        "Ny": Ny,
        "le": emitter_length * 1e-6,  # Length in μm
        "we": emitter_width * 1e-6,  # Width in nm
        "STI": STI * 1e-6,
        "baspolyx": baspolyx * 1e-6,
        "bipwinx": bipwinx * 1e-6,
        "bipwiny": bipwiny * 1e-6,
        "empolyx": empolyx * 1e-6,
        "empolyy": empolyy * 1e-6,
        "Icmax": 3 * 1e-3,  # hardcoded in IHP PyCell, not in techparams
        "Iarea": 1 * 1e-3,  # hardcoded in IHP PyCell, not in techparams
        "area": 1,  # hardcoded in IHP PyCell, not in techparams
        "bn": "sub!",  # hardcoded in IHP PyCell, not in techparams
        "m": 1,
        "trise": "",
        "Text": text,
        "CMetY1": CMetY1 * 1e-6,  # hardcoded in IHP PyCell, not in techparams
        "CMetY2": CMetY2 * 1e-6,  # hardcoded in IHP PyCell, not in techparams
    }

    # add ports to the component
    c = generate_gf_from_ihp(
        cell_name="npn13G2", cell_params=params, function_name=npn13G2IHP()
    )
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(tech.LAYER.Metal1pin),
        port_type="electrical",
        ports_on_short_side=True,
        auto_rename_ports=False,
    )
    c.ports["e1"].name = "C"
    c.ports["e2"].name = "B"
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(tech.LAYER.Metal2pin),
        port_name_prefix="E",
        port_type="electrical",
        ports_on_short_side=True,
        auto_rename_ports=False,
    )
    c.ports["E1"].name = "E"
    # c.ports["e1"].name = "B"
    # c.ports["e2"].name = "C"
    # c.ports["e3"].name = "E"

    return c


@gf.cell
def npn13G2L(
    Nx: int = 1,
    emitter_length: float = 1,
    emitter_width: float = 0.07,
) -> gf.Component:
    """Returns the IHP npn13G2L BJT transistor as a gdsfactory Component.

    This function generates a layout for the npn13G2L heterojunction
    bipolar transistor (HBT) from the IHP SG13G2 process. The transistor
    geometry is defined by the number of emitter fingers and the dimensions
    of each emitter finger.

    Args:
        Nx: Number of emitter fingers.
        emitter_length: Length of each emitter finger, in microns.
        emitter_width: Width of each emitter finger, in microns.

    Returns:
        gdsfactory.Component: The generated npn13G2L transistor layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "Display": "Selected",
        "model": tech.techParams["npn13G2L_model"],
        "Nx": Nx,
        "le": emitter_length * 1e-6,  # Length in μm
        "we": emitter_width * 1e-6,  # Width in nm
        "Icmax": 3 * 1e-3,  # hardcoded in IHP PyCell, not in techparams
        "Iarea": 1 * 1e-3,  # hardcoded in IHP PyCell, not in techparams
        "area": 1,  # hardcoded in IHP PyCell, not in techparams
        "bn": "sub!",  # hardcoded in IHP PyCell, not in techparams
        "Vbe": "",
        "Vce": "",
        "m": 1,
        "trise": "",
    }

    c = generate_gf_from_ihp(
        cell_name="npn13G2L", cell_params=params, function_name=npn13G2LIHP()
    )

    # add ports to the component
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(tech.LAYER.Metal1pin),
        port_type="electrical",
        ports_on_short_side=True,
    )
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(tech.LAYER.Metal2pin),
        port_name_prefix="E",
        port_type="electrical",
        ports_on_short_side=True,
    )
    c.ports["e1"].name = "B"
    c.ports["e2"].name = "E"
    c.ports["e3"].name = "C"

    return c


@gf.cell
def npn13G2V(
    Nx: int = 1,
    emitter_length: float = 1,
    emitter_width: float = 0.12,
) -> gf.Component:
    """Returns the IHP npn13G2V BJT transistor as a gdsfactory Component.

    This function generates a layout for the npn13G2V heterojunction
    bipolar transistor (HBT) from the IHP SG13G2 process. The transistor
    geometry is defined by the number of emitter fingers and the dimensions
    of each emitter finger.

    Args:
        Nx: Number of emitter fingers. Valid range: [1, 8].
        emitter_length: Length of each emitter finger, in microns.
        emitter_width: Width of each emitter finger, in microns.

    Returns:
        gdsfactory.Component: The generated npn13G2V transistor layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "Display": "Selected",
        "model": tech.techParams["npn13G2V_model"],
        "Nx": Nx,
        "le": emitter_length * 1e-6,  # Length in μm
        "we": emitter_width * 1e-6,  # Width in nm
        "Icmax": 3 * 1e-3,  # hardcoded in IHP PyCell, not in techparams
        "Iarea": 1 * 1e-3,  # hardcoded in IHP PyCell, not in techparams
        "area": 1,  # hardcoded in IHP PyCell, not in techparams
        "bn": "sub!",  # hardcoded in IHP PyCell, not in techparams
        "Vbe": "",
        "Vce": "",
        "m": 1,
        "trise": "",
    }

    c = generate_gf_from_ihp(
        cell_name="npn13G2V", cell_params=params, function_name=npn13G2VIHP()
    )

    # add ports to the component
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(tech.LAYER.Metal1pin),
        port_type="electrical",
        ports_on_short_side=True,
    )
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(tech.LAYER.Metal2pin),
        port_name_prefix="E",
        port_type="electrical",
        ports_on_short_side=True,
    )
    c.ports["e1"].name = "B"
    c.ports["e2"].name = "C"
    c.ports["e3"].name = "E"

    return c


@gf.cell
def pnpMPA(
    width: float = 0.7,
    length: float = 2,
) -> gf.Component:
    """Returns the IHP pnpMPA BJT transistor as a gdsfactory Component.

    This function generates a layout for a PNP transistor using the IHP process.
    The geometry of the transistor is defined by its width and length.

    Args:
        width: Width of the transistor, in microns.
        length: Length of the transistor, in microns.

    Returns:
        gdsfactory.Component: The generated pnpMPA transistor layout.
    """

    area = width * length
    perimeter = 2 * (width + length)
    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "Display": "Selected",
        "model": tech.techParams["pnpMPA_model"],
        "Calculate": "a",
        "w": width * 1e-6,  # Length in μm
        "l": length * 1e-6,  # Width in nm
        "a": area * 1e-12,
        "p": perimeter * 1e-6,
        "ac": 7.524 * 1e-12,
        "pc": 11.16 * 1e-6,
        "m": 1,  # Multiplier
        "region": "",
        "trise": "",
    }

    c = generate_gf_from_ihp(
        cell_name="pnpMPA", cell_params=params, function_name=pnpMPAIHP()
    )

    # add ports to the component
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(tech.LAYER.Metal1pin),
        port_type="electrical",
        ports_on_short_side=True,
    )
    c.ports["e1"].name = "TIE"
    c.ports["e2"].name = "PLUS"
    c.ports["e3"].name = "MINUS"

    return c
