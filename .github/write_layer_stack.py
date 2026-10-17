"""Generate the interactive layer-stack documentation from the active PDK."""

from __future__ import annotations

import json
import math
from html import escape
from pathlib import Path

import gdsfactory as gf

from ihp import PDK
from ihp.config import PATH

BANDS = [("", PDK)]
ASSET_DIRECTORY = Path(__file__).with_name("layer_stack_assets")
MATERIAL_COLORS = {
    "si": "#a0a0a0",
    "silicon": "#a0a0a0",
    "poly_si": "#76889a",
    "sio2": "#fff8dc",
    "sin": "#8fbc8f",
    "tin": "#dda0dd",
    "alcu": "#c7b07b",
    "al": "#4caf50",
    "cu": "#d0a050",
    "tungsten": "#9e9e9e",
    "sg13g2_cont": "#9e9e9e",
    "sg13g2_mim": "#c7b07b",
    "sg13g2_vmim": "#9e9e9e",
}


def _gds_layer(layer_reference):
    """Resolve physical layer/datatype pairs rather than KLayout indices."""
    if layer_reference is None:
        return None
    if isinstance(layer_reference, gf.technology.LogicalLayer):
        layer_reference = layer_reference.layer
    try:
        return gf.get_layer_tuple(layer_reference)
    except (TypeError, ValueError, KeyError):
        return None


def _material_color(material):
    material = material.lower()
    return next(
        (
            color
            for prefix, color in MATERIAL_COLORS.items()
            if material == prefix or material.startswith(prefix + "_")
        ),
        "#d0d0d0",
    )


def _layer_type(name, material):
    if "via" in name or name in {"cont", "vmim"}:
        return "via"
    material = material.lower()
    if (
        name.startswith(("metal", "topmetal"))
        or name == "mim"
        or material in {"al", "cu", "w", "tin"}
        or material.startswith(("alcu_", "tungsten_"))
    ):
        return "conductor"
    if material in {"si", "silicon", "poly_si"}:
        return "semiconductor"
    return "dielectric"


def _extract_layers(layer_stack):
    layers = []
    for name, level in layer_stack.layers.items():
        thickness = float(level.thickness or 0)
        if abs(thickness) < 1e-9:
            continue
        bottom, top = sorted(
            (float(level.zmin or 0), float(level.zmin or 0) + thickness)
        )
        material = level.material or ""
        layer_pair = _gds_layer(level.layer)
        layers.append(
            {
                "name": name,
                "gds": f"{layer_pair[0]}/{layer_pair[1]}" if layer_pair else None,
                "layer_pair": layer_pair,
                "material": material,
                "type": _layer_type(name.lower(), material),
                "zmin": round(bottom, 4),
                "zmax": round(top, 4),
                "thickness": round(abs(thickness), 4),
                "color": _material_color(material),
            }
        )
    return sorted(layers, key=lambda layer: layer["zmin"])


def _assign_columns(layers):
    """Give every connected overlap cluster one consistent column grid."""
    cluster = []
    cluster_top = -math.inf

    def assign_cluster():
        column_ends = []
        for layer in cluster:
            column = next(
                (
                    index
                    for index, end in enumerate(column_ends)
                    if end <= layer["zmin"]
                ),
                len(column_ends),
            )
            if column == len(column_ends):
                column_ends.append(layer["zmax"])
            else:
                column_ends[column] = layer["zmax"]
            layer["col"] = column
        for layer in cluster:
            layer["ncols"] = len(column_ends)

    for layer in layers:
        if cluster and layer["zmin"] >= cluster_top:
            assign_cluster()
            cluster = []
            cluster_top = -math.inf
        cluster.append(layer)
        cluster_top = max(cluster_top, layer["zmax"])
    assign_cluster()


def _compute_layout(layers):
    """Place uniform rows and physically scaled rows on a common canvas."""
    if not layers:
        return [], []
    _assign_columns(layers)
    top_margin, plot_height = 45, 700
    bottom = min(layer["zmin"] for layer in layers)
    top = max(layer["zmax"] for layer in layers)
    depth = top - bottom or 1
    row_height = plot_height / len(layers)

    def vertical_position(z_coordinate):
        return top_margin + plot_height * (top - z_coordinate) / depth

    for index, layer in enumerate(layers):
        layer.update(
            uy=round(top_margin + (len(layers) - index - 1) * row_height, 2),
            uh=round(row_height * 0.93, 2),
            sy=round(vertical_position(layer["zmax"]), 2),
            sh=round(max(plot_height * layer["thickness"] / depth, 1), 2),
        )
    raw_step = depth / 10
    magnitude = 10 ** math.floor(math.log10(raw_step))
    step = (
        next(
            multiplier
            for multiplier in (1, 2, 5, 10)
            if multiplier * magnitude >= raw_step
        )
        * magnitude
    )
    ticks = []
    tick = math.ceil(bottom / step) * step
    while tick <= top + step * 1e-6:
        ticks.append({"z": round(tick, 4), "py": vertical_position(tick)})
        tick += step
    return layers, ticks


def _extract_cross_sections(pdk, layers):
    layers_by_pair = {
        tuple(layer["layer_pair"]): layer
        for layer in layers
        if layer["layer_pair"] is not None
    }
    cross_sections = []
    for name in pdk.cross_sections:
        try:
            cross_section = pdk.get_cross_section(name)
        except (TypeError, ValueError):
            continue
        sections = []
        for section in cross_section.sections:
            layer = layers_by_pair.get(_gds_layer(section.layer))
            if layer is not None:
                sections.append(
                    {
                        **layer,
                        "width": float(section.width),
                        "offset": float(section.offset),
                    }
                )
        if sections:
            cross_sections.append({"name": name, "layers": sections})
    return cross_sections


def _embed_data(data):
    """Keep JSON text from terminating its containing HTML script element."""
    return json.dumps(data).replace("<", "\\u003c")


def render_page(bands=None):
    """Render one page with shared styles and behavior for all PDK bands."""
    stylesheet = (ASSET_DIRECTORY / "viewers.css").read_text()
    javascript = (ASSET_DIRECTORY / "viewers.js").read_text()
    parts = [
        "# Layer Stack\n",
        "Hover for details, Ctrl+scroll to zoom, drag to pan, and double-click to reset.\n",
        "Layer heights come from the PDK stack. Cross-sections show registered default "
        "widths and offsets, with an independent horizontal scale for each cross-section. "
        "Lateral mask patterns are not shown.\n",
        f"<style>\n{stylesheet}\n</style>\n",
    ]
    for band_label, pdk in BANDS if bands is None else bands:
        pdk.activate()
        if pdk.layer_stack is None:
            continue
        layers, ticks = _compute_layout(_extract_layers(pdk.layer_stack))
        if not layers:
            continue
        data = {
            "layers": layers,
            "ticks": ticks,
            "cross_sections": _extract_cross_sections(pdk, layers),
        }
        if band_label:
            parts.append(f"\n## {escape(band_label)}\n")
        parts.append(
            '<div class="layer-stack-viz">\n'
            "<h2>Layer Stack</h2>\n"
            '<div class="stack-controls"><button type="button" data-mode="uniform" '
            'aria-pressed="true">Uniform</button> '
            '<button type="button" data-mode="scale" aria-pressed="false">To Scale</button></div>\n'
            '<div class="stack-viewer"><svg class="stack-svg" width="600" height="780" '
            'role="img" aria-label="PDK layer stack"></svg><div class="stack-tooltip" hidden></div></div>\n'
            "<h2>Cross-Sections</h2>\n"
            '<div class="stack-viewer"><svg class="cross-section-svg" width="1000" height="500" '
            'role="img" aria-label="PDK cross-sections"></svg><div class="stack-tooltip" hidden></div></div>\n'
            f'<script type="application/json" class="stack-data">{_embed_data(data)}</script>\n'
            "</div>\n"
        )
    parts.append(f"<script>\n{javascript}\n</script>\n")
    return "\n".join(parts)


def main():
    filepath = PATH.repo / "docs" / "layer_stack.md"
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(render_page())
    print(f"Wrote {filepath}")


if __name__ == "__main__":
    main()
