"""Äntenna components for IHP PDK."""

import math

import gdsfactory as gf
from gdsfactory.typings import LayerSpec

from cni.tech import Tech

tech_name = "SG13_dev"
tech = Tech.get("SG13_dev").getTechParams()


def fix(value):
    if type(value) is float:
        return int(math.floor(value))
    else:
        return value


def GridFix(x):
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
):
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
    addRecLayer: str = "t",
    guardRingType: str = "none",
    # guardRingDistance: float = 1.0,
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

    layer_metal1: LayerSpec = "Metal1drawing"
    ndiff_layer: LayerSpec = "Activdrawing"
    # pdiff_layer: LayerSpec = "Activ"
    # pdiffx_layer: LayerSpec = "pSD"
    cont_layer: LayerSpec = "Contdrawing"
    diods_layer: LayerSpec = "Recogdiode"
    layer_text: LayerSpec = "TEXTdrawing"

    cont_size = tech["Cnt_a"]
    cont_dist = tech["Cnt_b"]
    cont_diff_over = tech["Cnt_c"]
    # pdiffx_over = tech["pSD_a"]
    # wmin = tech["dantenna_minW"]
    # lmin = tech["dantenna_minL"]
    diods_over = float(tech["dantenna_dov"].rstrip("u"))

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

    c.add_ref(gf.components.rectangle(size=(width, length), layer=ndiff_layer))

    c.add_label(
        "dant",
        layer=layer_text,
        position=(
            length / 2,
            width / 2,
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


if __name__ == "__main__":
    from gdsfactory.difftest import xor

    from ihp import PDK, cells2

    PDK.activate()
    c1 = dantenna()
    c0 = cells2.dantenna()
    c = xor(c0, c1)
    c.show()  # pragma: no cover
