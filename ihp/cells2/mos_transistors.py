from __future__ import annotations

import warnings
from typing import Literal

import gdsfactory as gf
from gdsfactory.typings import LayerSpec

from .. import tech
from .ihp_pycell import eng_string_to_float
from .ihp_pycell import nmos as nmosIHP
from .ihp_pycell import nmosHV as nmosHVIHP
from .ihp_pycell import pmos as pmosIHP
from .ihp_pycell import pmosHV as pmosHVIHP
from .ihp_pycell import rfnmos as rfnmosIHP
from .ihp_pycell import rfnmosHV as rfnmosHVIHP
from .ihp_pycell import rfpmos as rfpmosIHP
from .ihp_pycell import rfpmosHV as rfpmosHVIHP
from .utils import *


def _add_ports_from_boxes_safe(
    component: gf.Component,
    pin_layer: LayerSpec,
    port_type: str = "electrical",
    port_name_prefix: str | None = None,
    ports_on_short_side: bool = False,
) -> None:
    """Add ports from boxes, silently skipping duplicates.

    Wraps ``gf.add_ports.add_ports_from_boxes`` to handle cases where
    multiple overlapping shapes on the same layer (e.g. GatPolydrawing
    with gate-ring connecting stripes) produce ports at identical
    locations.  Rather than raising a ``ValueError``, duplicate ports
    are simply skipped.
    """
    try:
        gf.add_ports.add_ports_from_boxes(
            component,
            pin_layer=pin_layer,
            port_type=port_type,
            port_name_prefix=port_name_prefix,
            ports_on_short_side=ports_on_short_side,
            auto_rename_ports=False,
        )
    except ValueError as exc:
        if "already in" not in str(exc):
            raise
        # Overlapping shapes (e.g. gate-ring stripes sharing edges with
        # gate fingers) produced ports at the same physical location.
        # This is harmless -- the first unique port was already added
        # before the error was raised, so we just move on.
        warnings.warn(
            f"Duplicate port detected on layer {pin_layer}; "
            "skipping overlapping port(s).",
            stacklevel=2,
        )


@gf.cell(tags=["IHP", "mos", "lv"])
def nmos(
    w: float = 0.15,
    l: float = 0.13,
    ng: int = 1,
    guardRingType: Literal["none", "psub"] = "none",
    guardRingDistance: float = 1,
) -> gf.Component:
    """Create an NMOS transistor layout.

    This function generates a parametric NMOS transistor with configurable
    width, length, number of gates/fingers, and optional P-substrate guard ring.

    Args:
        w: Total width of the transistor in micrometers.
        l: Length of the transistor in micrometers.
        ng: Number of gates/fingers.
        guardRingType: Type of guard ring to include. Options:
            - 'none': No guard ring.
            - 'psub': P-substrate guard ring.
        guardRingDistance: Spacing between the transistor and the guard ring, in micrometers.

    Returns:
        gdsfactory.Component: The generated NMOS transistor layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "model": tech.techParams["nmos_model"],
        "w": w * 1e-6,  # Width in μm
        "ws": eng_string_to_float(tech.techParams["nmos_defW"])
        / eng_string_to_float(tech.techParams["nmos_defNG"]),  # Single Width in nm
        "l": l * 1e-6,  # Length in μm
        "ng": ng,  # Number of gates
        "m": 1,  # Multiplier
        "Wmin": eng_string_to_float(tech.techParams["nmos_minW"]),
        "Lmin": eng_string_to_float(tech.techParams["nmos_minL"]),
        "trise": "",
        "Display": "Selected",
        "guardRingType": guardRingType,
        "guardRingDistance": guardRingDistance * 1e-6,
    }

    c = generate_gf_from_ihp(
        cell_name="nmos", cell_params=params, function_name=nmosIHP()
    )

    # add ports
    _add_ports_from_boxes_safe(
        c,
        pin_layer=(tech.LAYER.Metal1drawing),
        port_type="electrical",
        port_name_prefix="DS_",
        ports_on_short_side=True,
    )
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    for i, port in enumerate(c.ports):
        port.orientation = (
            90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
        )

    _add_ports_from_boxes_safe(
        c,
        pin_layer=(tech.LAYER.GatPolydrawing),
        port_type="electrical",
        port_name_prefix="G_",
        ports_on_short_side=True,
    )
    return c


@gf.cell(tags=["IHP", "mos", "hv"])
def nmosHV(
    w: float = 0.60,
    l: float = 0.45,
    ng: int = 1,
    guardRingType: Literal["none", "psub"] = "none",
    guardRingDistance: float = 1,
) -> gf.Component:
    """Create a high-voltage NMOS transistor layout.

    This function generates a parametric high-voltage NMOS transistor with
    configurable width, length, number of gates/fingers, and optional
    P-substrate guard ring.

    Args:
        w: Total width of the transistor in micrometers.
        l: Length of the transistor in micrometers.
        ng: Number of gates/fingers.
        guardRingType: Type of guard ring to include. Options:
            - 'none': No guard ring.
            - 'psub': P-substrate guard ring.
        guardRingDistance: Spacing between the transistor and the guard ring, in micrometers.

    Returns:
        gdsfactory.Component: The generated high-voltage NMOS transistor layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "model": tech.techParams["nmosHV_model"],
        "w": w * 1e-6,  # Width in μm
        "ws": eng_string_to_float(tech.techParams["nmosHV_defW"])
        / eng_string_to_float(tech.techParams["nmosHV_defNG"]),  # Single Width in nm
        "l": l * 1e-6,  # Length in μm
        "ng": ng,  # Number of gates
        "m": 1,  # Multiplier
        "Wmin": eng_string_to_float(tech.techParams["nmosHV_minW"]),
        "Lmin": eng_string_to_float(tech.techParams["nmosHV_minL"]),
        "trise": "",
        "Display": "Selected",
        "guardRingType": guardRingType,
        "guardRingDistance": guardRingDistance * 1e-6,
    }

    c = generate_gf_from_ihp(
        cell_name="nmosHV", cell_params=params, function_name=nmosHVIHP()
    )

    # add ports
    _add_ports_from_boxes_safe(
        c,
        pin_layer=(tech.LAYER.Metal1drawing),
        port_type="electrical",
        port_name_prefix="DS_",
        ports_on_short_side=True,
    )
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    for i, port in enumerate(c.ports):
        port.orientation = (
            90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
        )

    _add_ports_from_boxes_safe(
        c,
        pin_layer=(tech.LAYER.GatPolydrawing),
        port_type="electrical",
        port_name_prefix="G_",
        ports_on_short_side=True,
    )

    return c


@gf.cell(tags=["IHP", "mos", "lv"])
def pmos(
    w: float = 0.15,
    l: float = 0.13,
    ng: int = 1,
    guardRingType: Literal["none", "nwell"] = "none",
    guardRingDistance: float = 1,
) -> gf.Component:
    """Create a PMOS transistor layout.

    This function generates a parametric PMOS transistor with configurable
    width, length, number of gates/fingers, and optional guard ring.

    Args:
        w: Total width of the transistor in micrometers.
        l: Length of the transistor in micrometers.
        ng: Number of gates/fingers.
        guardRingType: Type of guard ring to include. Options:
            - 'none': No guard ring.
            - 'nwell': N-well guard ring.
        guardRingDistance: Spacing between the transistor and the guard ring, in micrometers.

    Returns:
        gdsfactory.Component: The generated PMOS transistor layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "model": tech.techParams["pmos_model"],
        "w": w * 1e-6,  # Width in μm
        "ws": eng_string_to_float(tech.techParams["pmos_defW"])
        / eng_string_to_float(tech.techParams["pmos_defNG"]),  # Single Width in nm
        "l": l * 1e-6,  # Length in μm
        "ng": ng,  # Number of gates
        "m": 1,  # Multiplier
        "Wmin": eng_string_to_float(tech.techParams["pmos_minW"]),
        "Lmin": eng_string_to_float(tech.techParams["pmos_minL"]),
        "trise": "",
        "Display": "Selected",
        "guardRingType": guardRingType,
        "guardRingDistance": guardRingDistance * 1e-6,
    }

    c = generate_gf_from_ihp(
        cell_name="pmos", cell_params=params, function_name=pmosIHP()
    )

    # add ports
    _add_ports_from_boxes_safe(
        c,
        pin_layer=(tech.LAYER.Metal1drawing),
        port_type="electrical",
        port_name_prefix="DS_",
        ports_on_short_side=True,
    )
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    for i, port in enumerate(c.ports):
        port.orientation = (
            90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
        )

    _add_ports_from_boxes_safe(
        c,
        pin_layer=(tech.LAYER.GatPolydrawing),
        port_type="electrical",
        port_name_prefix="G_",
        ports_on_short_side=True,
    )
    return c


@gf.cell(tags=["IHP", "mos", "hv"])
def pmosHV(
    w: float = 0.30,
    l: float = 0.40,
    ng: int = 1,
    guardRingType: Literal["none", "psub"] = "none",
    guardRingDistance: float = 1,
) -> gf.Component:
    """Create a high-voltage PMOS (PMOSHV) transistor layout.

    This function generates a parametric high-voltage PMOS transistor with
    configurable width, length, number of gates/fingers, and optional
    P-substrate guard ring.

    Args:
        w: Total width of the transistor in micrometers.
        l: Length of the transistor in micrometers.
        ng: Number of gates/fingers.
        guardRingType: Type of guard ring to include. Options:
            - 'none': No guard ring.
            - 'psub': P-substrate guard ring.
        guardRingDistance: Spacing between the transistor and the guard ring, in micrometers.

    Returns:
        gdsfactory.Component: The generated high-voltage PMOS transistor layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "model": tech.techParams["pmosHV_model"],
        "w": w * 1e-6,  # Width in μm
        "ws": eng_string_to_float(tech.techParams["pmosHV_defW"])
        / eng_string_to_float(tech.techParams["pmosHV_defNG"]),  # Single Width in nm
        "l": l * 1e-6,  # Length in μm
        "ng": ng,  # Number of gates
        "m": 1,  # Multiplier
        "Wmin": eng_string_to_float(tech.techParams["pmosHV_minW"]),
        "Lmin": eng_string_to_float(tech.techParams["pmosHV_minL"]),
        "trise": "",
        "Display": "Selected",
        "guardRingType": guardRingType,
        "guardRingDistance": guardRingDistance * 1e-6,
    }

    c = generate_gf_from_ihp(
        cell_name="pmosHV", cell_params=params, function_name=pmosHVIHP()
    )

    # add ports
    _add_ports_from_boxes_safe(
        c,
        pin_layer=(tech.LAYER.Metal1drawing),
        port_type="electrical",
        port_name_prefix="DS_",
        ports_on_short_side=True,
    )
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    for i, port in enumerate(c.ports):
        port.orientation = (
            90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
        )

    _add_ports_from_boxes_safe(
        c,
        pin_layer=(tech.LAYER.GatPolydrawing),
        port_type="electrical",
        port_name_prefix="G_",
        ports_on_short_side=True,
    )
    return c


@gf.cell(tags=["IHP", "mos", "lv", "rf"])
def rfnmos(
    w: float = 1.0,
    l: float = 0.72,
    ng: int = 1,
    cnt_rows: int = 1,
    Met2Cont: Literal["Yes", "No"] = "Yes",
    gat_ring: Literal["Yes", "No"] = "Yes",
    guard_ring: Literal["Yes", "No", "U", "Top+Bottom"] = "Yes",
) -> gf.Component:
    """Create an RF NMOS transistor layout.

    This function generates a parametric RF NMOS transistor with configurable
    width, length, number of gates/fingers, number of rows, and optional
    contacts and guard structures.

    Args:
        w: Total width of the transistor in micrometers.
        l: Length of the transistor in micrometers.
        ng: Number of gates/fingers.
        cnt_rows: Number of transistor rows (vertical stacking of fingers).
        Met2Cont: Include Metal2-to-contact connection. Options: 'Yes' or 'No'.
        gat_ring: Include gate ring around the transistor. Options: 'Yes' or 'No'.
        guard_ring: Include guard ring around the transistor. Options:
            - 'U': U-shaped guard ring (One side stays open).
            - 'Top+Bottom': Guard ring on top and bottom (North/South).
            - 'Yes': Default guard ring.
            - 'No': No guard ring.

    Returns:
        gdsfactory.Component: The generated RF NMOS transistor layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "rfmode": 1,
        "model": tech.techParams["rfnmos_model"],
        "w": w * 1e-6,  # Width in μm
        "ws": eng_string_to_float(tech.techParams["rfnmos_defW"])
        / eng_string_to_float(tech.techParams["rfnmos_defNG"])
        * 1e-6,  # Single Width in nm
        "l": l * 1e-6,  # Length in μm
        "ng": ng,  # Number of gates
        "calculate": True,
        "cnt_rows": cnt_rows,
        "Met2Cont": Met2Cont,
        "gat_ring": gat_ring,
        "guard_ring": guard_ring,
        "Wmin": eng_string_to_float(tech.techParams["rfnmos_minW"]),
        "Lmin": eng_string_to_float(tech.techParams["rfnmos_minL"]),
        "m": 1,
        "trise": "",
        "Display": "Selected",
    }

    c = generate_gf_from_ihp(
        cell_name="rfnmos", cell_params=params, function_name=rfnmosIHP()
    )

    # add ports
    _add_ports_from_boxes_safe(
        c,
        pin_layer=(tech.LAYER.Metal1drawing),
        port_type="electrical",
        port_name_prefix="DS_",
        ports_on_short_side=True,
    )
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    for i, port in enumerate(c.ports):
        port.orientation = (
            90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
        )

    _add_ports_from_boxes_safe(
        c,
        pin_layer=(tech.LAYER.GatPolydrawing),
        port_type="electrical",
        port_name_prefix="G_",
        ports_on_short_side=True,
    )
    return c


@gf.cell(tags=["IHP", "mos", "hv", "rf"])
def rfnmosHV(
    w: float = 1.0,
    l: float = 0.72,
    ng: int = 1,
    cnt_rows: int = 1,
    Met2Cont: Literal["Yes", "No"] = "Yes",
    gat_ring: Literal["Yes", "No"] = "Yes",
    guard_ring: Literal["Yes", "No", "U", "Top+Bottom"] = "Yes",
) -> gf.Component:
    """Create a high-voltage RF NMOS (rfnmosHV) transistor layout.

    This function generates a parametric high-voltage RF NMOS transistor with
    configurable width, length, number of gates/fingers, number of rows, and
    optional contacts, gate ring, and guard ring structures.

    Args:
        w: Total width of the transistor in micrometers.
        l: Length of the transistor in micrometers.
        ng: Number of gates/fingers.
        cnt_rows: Number of transistor rows (vertical stacking of fingers).
        Met2Cont: Include Metal2-to-contact connection. Options: 'Yes' or 'No'.
        gat_ring: Include gate ring around the transistor. Options: 'Yes' or 'No'.
        guard_ring: Include guard ring around the transistor. Options:
            - 'U': U-shaped guard ring (One side stays open).
            - 'Top+Bottom': Guard ring on top and bottom (North/South).
            - 'Yes': Default guard ring.
            - 'No': No guard ring.

    Returns:
        gdsfactory.Component: The generated high-voltage RF NMOS transistor layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "rfmode": 1,
        "model": tech.techParams["rfnmosHV_model"],
        "w": w * 1e-6,  # Width in μm
        "ws": eng_string_to_float(tech.techParams["rfnmosHV_defW"])
        / eng_string_to_float(tech.techParams["rfnmosHV_defNG"])
        * 1e-6,  # Single Width in nm
        "l": l * 1e-6,  # Length in μm
        "ng": ng,  # Number of gates
        "calculate": True,
        "cnt_rows": cnt_rows,
        "Met2Cont": Met2Cont,
        "gat_ring": gat_ring,
        "guard_ring": guard_ring,
        "Wmin": eng_string_to_float(tech.techParams["rfnmosHV_minW"]),
        "Lmin": eng_string_to_float(tech.techParams["rfnmosHV_minL"]),
        "m": 1,
        "trise": "",
        "Display": "Selected",
    }

    c = generate_gf_from_ihp(
        cell_name="rfnmosHV", cell_params=params, function_name=rfnmosHVIHP()
    )
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    # for i, port in enumerate(c.ports):
    #     port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
    return c


@gf.cell(tags=["IHP", "mos", "lv", "rf"])
def rfpmos(
    w: float = 1.0,
    l: float = 0.72,
    ng: int = 1,
    cnt_rows: int = 1,
    Met2Cont: Literal["Yes", "No"] = "Yes",
    gat_ring: Literal["Yes", "No"] = "Yes",
    guard_ring: Literal["Yes", "No", "U", "Top+Bottom"] = "Yes",
) -> gf.Component:
    """Create an RF PMOS transistor layout.

    This function generates a parametric RF PMOS transistor with configurable
    width, length, number of gates/fingers, number of rows, and optional
    contacts, gate ring, and guard ring structures.

    Args:
        w: Total width of the transistor in micrometers.
        l: Length of the transistor in micrometers.
        ng: Number of gates/fingers.
        cnt_rows: Number of transistor rows (vertical stacking of fingers).
        Met2Cont: Include Metal2-to-contact connection. Options: 'Yes' or 'No'.
        gat_ring: Include gate ring around the transistor. Options: 'Yes' or 'No'.
        guard_ring: Include guard ring around the transistor. Options:
            - 'U': U-shaped guard ring (One side stays open).
            - 'Top+Bottom': Guard ring on top and bottom (North/South).
            - 'Yes': Default guard ring.
            - 'No': No guard ring.

    Returns:
        gdsfactory.Component: The generated RF PMOS transistor layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "rfmode": 1,
        "model": tech.techParams["rfpmos_model"],
        "w": w * 1e-6,  # Width in μm
        "ws": eng_string_to_float(tech.techParams["rfpmos_defW"])
        / eng_string_to_float(tech.techParams["rfpmos_defNG"])
        * 1e-6,  # Single Width in nm
        "l": l * 1e-6,  # Length in μm
        "ng": ng,  # Number of gates
        "calculate": True,
        "cnt_rows": cnt_rows,
        "Met2Cont": Met2Cont,
        "gat_ring": gat_ring,
        "guard_ring": guard_ring,
        "Wmin": eng_string_to_float(tech.techParams["rfpmos_minW"]),
        "Lmin": eng_string_to_float(tech.techParams["rfpmos_minL"]),
        "m": 1,
        "trise": "",
        "Display": "Selected",
    }

    c = generate_gf_from_ihp(
        cell_name="rfpmos", cell_params=params, function_name=rfpmosIHP()
    )
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    # for i, port in enumerate(c.ports):
    #     port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
    return c


@gf.cell(tags=["IHP", "mos", "hv", "rf"])
def rfpmosHV(
    w: float = 1.0,
    l: float = 0.72,
    ng: int = 1,
    cnt_rows: int = 1,
    Met2Cont: Literal["Yes", "No"] = "Yes",
    gat_ring: Literal["Yes", "No"] = "Yes",
    guard_ring: Literal["Yes", "No", "U", "Top+Bottom"] = "Yes",
) -> gf.Component:
    """Create a high-voltage RF PMOS (rfpmosHV) transistor layout.

    This function generates a parametric high-voltage RF PMOS transistor with
    configurable width, length, number of gates/fingers, number of rows, and
    optional contacts, gate ring, and guard ring structures.

    Args:
        w: Total width of the transistor in micrometers.
        l: Length of the transistor in micrometers.
        ng: Number of gates/fingers.
        cnt_rows: Number of transistor rows (vertical stacking of fingers).
        Met2Cont: Include Metal2-to-contact connection. Options: 'Yes' or 'No'.
        gat_ring: Include gate ring around the transistor. Options: 'Yes' or 'No'.
        guard_ring: Include guard ring around the transistor. Options:
            - 'U': U-shaped guard ring (One side stays open).
            - 'Top+Bottom': Guard ring on top and bottom (North/South).
            - 'Yes': Default guard ring.
            - 'No': No guard ring.

    Returns:
        gdsfactory.Component: The generated high-voltage RF PMOS transistor layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "rfmode": 1,
        "model": tech.techParams["rfpmosHV_model"],
        "w": w * 1e-6,  # Width in μm
        "ws": eng_string_to_float(tech.techParams["rfpmosHV_defW"])
        / eng_string_to_float(tech.techParams["rfpmosHV_defNG"])
        * 1e-6,  # Single Width in nm
        "l": l * 1e-6,  # Length in μm
        "ng": ng,  # Number of gates
        "calculate": True,
        "cnt_rows": cnt_rows,
        "Met2Cont": Met2Cont,
        "gat_ring": gat_ring,
        "guard_ring": guard_ring,
        "Wmin": eng_string_to_float(tech.techParams["rfpmosHV_minW"]),
        "Lmin": eng_string_to_float(tech.techParams["rfpmosHV_minL"]),
        "m": 1,
        "trise": "",
        "Display": "Selected",
    }

    c = generate_gf_from_ihp(
        cell_name="rfpmosHV", cell_params=params, function_name=rfpmosHVIHP()
    )
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    # for i, port in enumerate(c.ports):
    #     port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
    return c
