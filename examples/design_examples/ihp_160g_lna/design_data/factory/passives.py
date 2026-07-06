from typing import Literal

import gdsfactory as gf
import numpy as np
from gdsfactory import Component
from gdsfactory.typings import LayerSpec
from numpy import floor, round

from ihp import cells, tech

type FloatLike = np.float32 | np.float64 | float
type Point = tuple[FloatLike, FloatLike]


@gf.cell
def guard_ring(
    width: float = 0.5,
    guardRingSpacing: float = 0.14,
    guardRingType: Literal["psub", "nwell"] = "psub",
    bbox: tuple[Point, Point] | None = None,
    path: list[tuple[Point, Point]] | None = None,
    layer_activ: LayerSpec = "Activdrawing",
    layer_cont: LayerSpec = "Contdrawing",
    layer_metal1: LayerSpec = "Metal1drawing",
    layer_psd: LayerSpec = "pSDdrawing",
    layer_nwell: LayerSpec = "NWelldrawing",
    layer_nsd: LayerSpec = "nSDdrawing",
    **kwargs,
) -> Component:
    """
    Create an N-Well (NW) and N-Plus (NP) or a P-Plus (PP)
    guard ring around a boundary box, or, if `bbox` is not provided,
    along a provided `path` of points.

    Args:
        width: Width of the guard ring group path,
            defining the width of the Metal1 Path.
        guardRingSpacing: Spacing between the Metal1 Path and the component BBox.
        guardRingType: Literal["psub", 'nwell'] Type of Guard-Ring (NP = nwell or PP = psub).
        bbox: Encapsulated component bounding box.
        path: Path point for the group path defining the Guard Ring,
        layer_activ: Activ drawing layer.
        layer_cont: Contact Via drawing layer.
        layer_metal1: Metal1 drawing layer.
        layer_psd: pSD / P-Plus drawing layer.
        layer_nwell: NWell drawing layer.
        layer_nsd: nSD / N-Plus drawing layer.
    Returns:
        c - Component containing the Guard-Ring group path.
    Raises:
    """

    gr_drc = {
        # metals
        "m1_min_width": tech.TECH.metal1_width,
        # active regions and contact
        "cont_min_size": tech.TECH.cont_size,
        "cont_min_spacing": tech.TECH.cont_spacing,
        "cont_min_enclose_active": tech.TECH.cont_enc_active,
        "cont_min_enclose_metal": tech.TECH.cont_enc_metal,
        # TODO: add in the original tech struct
        "active_min_enclose_np": 0.14,
        "active_min_enclose_pp": 0.14,
        "np_min_enclose_nw": 0.14,
    }

    min_width = gr_drc["cont_min_size"] + 2 * max(
        gr_drc["cont_min_enclose_active"], gr_drc["cont_min_enclose_metal"]
    )
    min_width = max(min_width, gr_drc["m1_min_width"])
    assert width >= min_width, (
        f"Guard Ring width >= {min_width} to comply with Min cont enclosure and metal width"
    )

    # define nrows and ncols of the required tap
    nrows = int(floor(width / min_width))
    c = Component()

    # define the path
    if bbox is not None:
        path = [
            (
                bbox[0][0] - guardRingSpacing - width / 2,
                bbox[1][1] + guardRingSpacing + width / 2,
            ),
            (
                bbox[1][0] + guardRingSpacing + width / 2,
                bbox[1][1] + guardRingSpacing + width / 2,
            ),
            (
                bbox[1][0] + guardRingSpacing + width / 2,
                bbox[0][1] - guardRingSpacing - width / 2,
            ),
            (
                bbox[0][0] - guardRingSpacing - width / 2,
                bbox[0][1] - guardRingSpacing - width / 2,
            ),
            (
                bbox[0][0] - guardRingSpacing - width / 2,
                bbox[1][1] + guardRingSpacing + width,
            ),
        ]
        enclosure = max(
            gr_drc["cont_min_enclose_active"], gr_drc["cont_min_enclose_metal"]
        )
        cont_path = [
            (
                bbox[0][0] - guardRingSpacing - enclosure,
                bbox[1][1] + guardRingSpacing + enclosure,
            ),
            (
                bbox[1][0] + guardRingSpacing + enclosure,
                bbox[1][1] + guardRingSpacing + enclosure,
            ),
            (
                bbox[1][0] + guardRingSpacing + enclosure,
                bbox[0][1] - guardRingSpacing - enclosure,
            ),
            (
                bbox[0][0] - guardRingSpacing - enclosure,
                bbox[0][1] - guardRingSpacing - enclosure,
            ),
            (bbox[0][0] - guardRingSpacing - enclosure, bbox[1][1] + guardRingSpacing),
        ]

    assert path is not None, "Neither path or bbox was provided."
    # place taps around path
    tap_layers = [layer_activ, layer_metal1]
    main = None
    for layer_spec in tap_layers:
        p = gf.path.extrude(gf.path.Path(path), width=width, layer=layer_spec)
        main = c.add_ref(p)
    if guardRingType == "psub":
        sep = gr_drc["active_min_enclose_pp"]
        last_point = list(path[-1])
        last_edge = (path[-1][0] - path[-2][0], path[-1][1] - path[-2][1])
        norm = np.linalg.norm(last_edge)
        dir_vec = np.array(last_edge) / norm
        # manhattan
        dir_vec[0] = round(dir_vec[0])
        dir_vec[1] = round(dir_vec[1])
        last_point[0] += sep * dir_vec[0]
        last_point[1] += sep * dir_vec[1]
        new_path = path.copy()
        new_path[-1] = tuple(last_point)
        p = gf.path.extrude(
            gf.path.Path(new_path), width=width + 2 * sep, layer=layer_psd
        )
        c.add_ref(p)
    if guardRingType == "nwell":
        sep = gr_drc["active_min_enclose_np"]
        last_point = list(path[-1])
        last_edge = (path[-1][0] - path[-2][0], path[-1][1] - path[-2][1])
        norm = np.linalg.norm(last_edge)
        dir_vec = np.array(last_edge) / norm
        # manhattan
        dir_vec[0] = round(dir_vec[0])
        dir_vec[1] = round(dir_vec[1])
        last_point[0] += sep * dir_vec[0]
        last_point[1] += sep * dir_vec[1]
        new_path = path.copy()
        new_path[-1] = tuple(last_point)
        p = gf.path.extrude(
            gf.path.Path(new_path), width=width + 2 * sep, layer=layer_nsd
        )

        sep += gr_drc["np_min_enclose_nw"]
        last_point = list(path[-1])
        last_point[0] += sep * dir_vec[0]
        last_point[1] += sep * dir_vec[1]
        new_path = path.copy()
        new_path[-1] = tuple(last_point)
        nwl = gf.path.extrude(
            gf.path.Path(new_path), width=width + 2 * sep, layer=layer_nwell
        )
        c.add_ref(p)
        c.add_ref(nwl)

    cont_tap = cells.via_array(
        via_type=layer_cont.split("drawing")[0],
        via_size=gr_drc["cont_min_size"],
        via_spacing=gr_drc["cont_min_size"] + gr_drc["cont_min_spacing"],
        via_enclosure=gr_drc["cont_min_enclose_active"],
        columns=1,
        rows=nrows,
    )

    conts = gf.path.along_path(
        gf.path.Path(cont_path if bbox is not None else path),
        cont_tap,
        gr_drc["cont_min_spacing"] + gr_drc["cont_min_size"],
        0.0,
    )
    cont_ref = c.add_ref(conts)
    cont_ref.x = main.x
    cont_ref.y = main.y
    c.info["model"] = f"{guardRingType}-guard-ring"
    c.info["width"] = width
    c.info["rows"] = nrows
    c.info["guardRingSpacing"] = guardRingSpacing

    return c
