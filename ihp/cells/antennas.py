"""Äntenna components for IHP PDK."""

import math
from typing import Literal

import gdsfactory as gf
from gdsfactory.typings import LayerSpec

from cni.tech import Tech

tech_name = "SG13_dev"
tech = Tech.get("SG13_dev").getTechParams()


def fix(value: float) -> int:
    """Rounds a floating-point value down to the nearest integer.

    Args:
        value: Value to be rounded or passed through.

    Returns:
        The rounded integer of ``value``.
    """
    return int(math.floor(value))


def GridFix(x: float) -> float:
    """Snaps a coordinate to the technology grid.

    Args:
        x: Coordinate value to be aligned to the technology grid.

    Returns:
        The grid-aligned coordinate value.
    """
    SG13_GRID = tech["grid"]
    SG13_IGRID = 1 / SG13_GRID
    SG13_EPSILON = tech["epsilon1"]
    return (
        fix(x * SG13_IGRID + SG13_EPSILON) * SG13_GRID
    )  # always use "nice" numbers, as 1/grid may be irrational


def DrawContArray(
    c,
    cont_layer,
    y_min,
    x_min,
    width,
    length,
    cont_size,
    cont_dist,
    cont_diff_over,
) -> tuple[float, float, float, float]:
    """Distributes an array of square contacts inside a rectangular region.

    Args:
        c: Target gdsfactory component to which the contacts are added.
        cont_layer: Layer on which the contact rectangles are drawn.
        y_min: Y-coordinate of the lower-left corner of the enclosing region.
        x_min: X-coordinate of the lower-left corner of the enclosing region.
        width: Width of the enclosing region.
        length: Length of the enclosing region.
        cont_size: Size of one square contact.
        cont_dist: Spacing between adjacent contacts.
        cont_diff_over: Minimum enclosure of contacts by the surrounding
            diffusion or active region.

    Returns:
        Tuple[float, float, float, float]: Coordinates of the bounding box
        enclosing the generated contact array in the form
        ``(x_min, y_min, x_max, y_max)``.
    """
    epsilon = tech["epsilon1"]

    xanz = fix(
        (width - 2 * cont_diff_over + cont_dist + epsilon) / (cont_size + cont_dist)
    )
    yanz = fix(
        (length - 2 * cont_diff_over + cont_dist + epsilon) / (cont_size + cont_dist)
    )

    name = tech["libName"]
    if name == "SG13_dev":
        cont_dist_big = tech["Cnt_b1"]
        cont_dist_big_nr = tech["Cnt_b1_nr"]
        # now check, if it is cont and more than 4 rows/lines
        if (
            cont_layer == "Cont"
            and xanz >= cont_dist_big_nr
            and yanz >= cont_dist_big_nr
        ):
            # it has to be bigger space between contacts
            cont_dist = cont_dist_big
            # it has to be bigger space between contacts
            xanz = fix(
                (width - 2 * cont_diff_over + cont_dist + epsilon)
                / (cont_size + cont_dist)
            )
            yanz = fix(
                (length - 2 * cont_diff_over + cont_dist + epsilon)
                / (cont_size + cont_dist)
            )

    xmin = xanz * (cont_size + cont_dist) - cont_dist + 2 * cont_diff_over
    ymin = yanz * (cont_size + cont_dist) - cont_dist + 2 * cont_diff_over
    xoff = (width - xmin) / 2
    xoff = GridFix(xoff)
    yoff = (length - ymin) / 2
    yoff = GridFix(yoff)

    for j in range(int(yanz)):
        for i in range(int(xanz)):
            cont = c << gf.components.rectangle(
                size=(cont_size, cont_size), layer=cont_layer
            )

            cont.move(
                (
                    x_min + xoff + cont_diff_over + (cont_size + cont_dist) * i,
                    y_min + yoff + cont_diff_over + (cont_size + cont_dist) * j,
                )
            )

    x_min = x_min + xoff + cont_diff_over
    y_min = y_min + yoff + cont_diff_over
    x_max = x_min + (cont_size + cont_dist) * i + cont_size
    y_max = y_min + (cont_size + cont_dist) * j + cont_size

    return x_min, y_min, x_max, y_max


@gf.cell
def dantenna(
    width: float = 0.78,
    length: float = 0.78,
    addRecLayer: Literal["t", "f"] = "t",
    guardRingType: Literal["none", "psub"] = "none",
    guardRingDistance: float = 1.0,
) -> gf.Component:
    """Creates a diode antenna (dantenna) structure.

    This function generates a layout cell containing a rectangular antenna
    region with optional recognition layers and guard ring structures.
    Parameters allow customization of the antenna geometry and the type
    and spacing of guard rings.

    Args:
        width: Width of the antenna rectangle in microns.
        length: Length of the antenna rectangle in microns.
        addRecLayer: Recognition layer to add (e.g., 'M1' for metal1, 'M2' for metal2,
            or None for none).
        guardRingType: Type of guard ring to include. Options include:
            - 'none': No guard ring
            - 'psub': P-type guard ring
        guardRingDistance: Spacing between the antenna body and guard ring in microns.

    Returns:
        gdsfactory.Component: The generated antenna component.
    """

    c = gf.Component()

    wmin = float(tech["dantenna_minW"].rstrip("u"))
    lmin = float(tech["dantenna_minL"].rstrip("u"))

    if width < wmin:
        width = wmin
    if length < lmin:
        length = lmin

    layer_metal1: LayerSpec = "Metal1drawing"
    ndiff_layer: LayerSpec = "Activdrawing"
    pdiff_layer: LayerSpec = "Activdrawing"
    pdiffx_layer: LayerSpec = "pSDdrawing"
    cont_layer: LayerSpec = "Contdrawing"
    diods_layer: LayerSpec = "Recogdiode"
    layer_text: LayerSpec = "TEXTdrawing"

    cont_size = tech["Cnt_a"]
    cont_dist = tech["Cnt_b"]
    cont_diff_over = tech["Cnt_c"]
    pdiffx_over = tech["pSD_a"]
    diods_over = float(tech["dantenna_dov"].rstrip("u"))

    typ = "N"

    x_min, y_min, x_max, y_max = DrawContArray(
        c,
        cont_layer,
        0,
        0,
        width,
        length,
        cont_size,
        cont_dist,
        cont_diff_over,
    )

    # Metal1 encloses the contacts
    metal1_ref = c << gf.components.rectangle(
        size=(x_max - x_min, y_max - y_min), layer=layer_metal1
    )

    metal1_ref.move((x_min, y_min))

    if typ == "N":
        c.add_ref(gf.components.rectangle(size=(width, length), layer=ndiff_layer))
    else:
        c.add_ref(gf.components.rectangle(size=(width, length), layer=pdiff_layer))
        c.add_ref(
            gf.components.rectangle(
                size=(width + 2 * pdiffx_over, length + 2 * pdiffx_over),
                layer=pdiffx_layer,
            )
        ).move((-pdiffx_over, -pdiffx_over))

    c.add_label(
        "dant",
        layer=layer_text,
        position=(
            width / 2,
            length / 2,
        ),
    )

    if addRecLayer == "t":
        c.add_ref(
            gf.components.rectangle(
                size=(width + 2 * diods_over, length + 2 * diods_over),
                layer=diods_layer,
            )
        ).move((-diods_over, -diods_over))

    return c


@gf.cell
def dpantenna(
    width: float = 0.78,
    length: float = 0.78,
    addRecLayer: Literal["t", "f"] = "t",
    guardRingType: Literal["none", "nwell"] = "none",
    guardRingDistance: float = 1.0,
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

    c = gf.Component()

    wmin = float(tech["dantenna_minW"].rstrip("u"))
    lmin = float(tech["dantenna_minL"].rstrip("u"))

    if width < wmin:
        width = wmin
    if length < lmin:
        length = lmin

    layer_metal1: LayerSpec = "Metal1drawing"
    pdiff_layer: LayerSpec = "Activdrawing"
    pdiffx_layer: LayerSpec = "pSDdrawing"
    cont_layer: LayerSpec = "Contdrawing"
    diods_layer: LayerSpec = "Recogdiode"
    layer_text: LayerSpec = "TEXTdrawing"
    layer_nwell: LayerSpec = "NWelldrawing"

    cont_size = tech["Cnt_a"]
    cont_dist = tech["Cnt_b"]
    cont_diff_over = tech["Cnt_c"]
    pdiffx_over = tech["pSD_c"]
    diods_over = float(tech["dpantenna_dov"].rstrip("u"))
    NW_c = tech["NW_c"]

    x_min, y_min, x_max, y_max = DrawContArray(
        c,
        cont_layer,
        0,
        0,
        width,
        length,
        cont_size,
        cont_dist,
        cont_diff_over,
    )

    # Metal1 encloses the contacts
    metal1_ref = c << gf.components.rectangle(
        size=(x_max - x_min, y_max - y_min), layer=layer_metal1
    )

    metal1_ref.move((x_min, y_min))

    c.add_ref(gf.components.rectangle(size=(width, length), layer=pdiff_layer))
    c.add_ref(
        gf.components.rectangle(
            size=(width + 2 * pdiffx_over, length + 2 * pdiffx_over),
            layer=pdiffx_layer,
        )
    ).move((-pdiffx_over, -pdiffx_over))

    c.add_label(
        "dant",
        layer=layer_text,
        position=(
            width / 2,
            length / 2,
        ),
    )

    if addRecLayer == "t":
        c.add_ref(
            gf.components.rectangle(
                size=(width + 2 * diods_over, length + 2 * diods_over),
                layer=diods_layer,
            )
        ).move((-diods_over, -diods_over))

    c.add_ref(
        gf.components.rectangle(
            size=(width + 2 * NW_c, length + 2 * NW_c),
            layer=layer_nwell,
        )
    ).move((-NW_c, -NW_c))

    return c


if __name__ == "__main__":
    from gdsfactory.difftest import xor

    from ihp import PDK, cells2

    PDK.activate()
    c1 = dpantenna()
    c0 = cells2.dpantenna(guardRingType="nwell")
    c = xor(c0, c1)
    c.show()
