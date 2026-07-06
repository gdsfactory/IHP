import base64
import inspect
import warnings

import kwasm.embed
import matplotlib as mpl
import matplotlib.pyplot as plt

from ihp import PDK
from ihp.config import PATH
from ihp.tech import LAYER_STACK, LAYER_VIEWS

mpl.use("Agg")
warnings.filterwarnings("ignore", category=DeprecationWarning)

PDK.activate()

filepath_cells = PATH.repo / "docs" / "cells.md"
filepath_3d = PATH.repo / "docs" / "_static" / "3d"
filepath_3d.mkdir(parents=True, exist_ok=True)

kwasm_dir = PATH.repo / "docs" / "kwasm"
gds_dir = kwasm_dir / "gds"

skip = {
    "LIBRARY",
    "circuit_names",
    "component_factory",
    "component_names",
    "container_names",
    "component_names_test_ports",
    "component_names_skip_test",
    "component_names_skip_test_ports",
    "dataclasses",
    "library",
    "waveguide_template",
    # utilities, not cells
    "import_gds",
}

skip_plot: tuple[str, ...] = ("",)
skip_settings: tuple[str, ...] = ("flatten", "safe_cell_names")

cells = PDK.cells


def _setup_kwasm_viewer() -> None:
    gds_dir.mkdir(parents=True, exist_ok=True)
    viewer_path = kwasm_dir / "viewer.html"
    if viewer_path.exists():
        return
    template = kwasm.embed._read_artifacts()
    template = template.replace("KWASM_GDS_B64", "")
    lyp_path = PATH.lyp
    if lyp_path.exists():
        lyp_b64 = base64.b64encode(lyp_path.read_bytes()).decode("ascii")
        template = template.replace("KWASM_LYP_B64", lyp_b64)
    else:
        template = template.replace("KWASM_LYP_B64", "")
    template = template.replace("KWASM_LYRDB_B64", "")
    template = template.replace("KWASM_NETLIST_B64", "")
    viewer_path.write_text(template)


def make_3d_glb(name, cell_dict):
    """Export a cell's 3D scene as a binary GLB file.

    Returns the filename relative to _static/3d/, or None on failure.
    """
    try:
        cell_fn = cell_dict[name]
        sig = inspect.signature(cell_fn)
        params = {}
        for p in sig.parameters:
            default = sig.parameters[p].default
            if (
                isinstance(default, int | float | str | tuple)
                and p not in skip_settings
            ):
                params[p] = default
        c = cell_fn(**params)
        scene = c.to_3d(layer_views=LAYER_VIEWS, layer_stack=LAYER_STACK)
        filename = f"{name}.glb"
        scene.export(str(filepath_3d / filename))
        return filename
    except Exception as e:
        print(f"  [3D skip] {name}: {e}")
        return None


def write_cell_entry(f, name, cell_dict, module_path="ihp.cells", import_alias="cells"):
    """Write a single cell's RST entry (autofunction + plot + 3D viewer)."""
    sig = inspect.signature(cell_dict[name])
    kwargs = ", ".join(
        [
            f"{p}={repr(sig.parameters[p].default)}"
            for p in sig.parameters
            if isinstance(sig.parameters[p].default, int | float | str | tuple)
            and p not in skip_settings
        ]
    )
    if name in skip_plot:
        f.write(
            f"""

## {name}


::: {module_path}.{name}

"""
        )
    else:
        f.write(
            f"""

## {name}


::: {module_path}.{name}

"""
        )

        # Generate 3D GLB before writing tabs
        glb_file = make_3d_glb(name, cell_dict)

        # Write GDS and save PNG for Static/Dynamic/3D tabs
        try:
            c = cell_dict[name]()
            c.write_gds(gds_dir / f"{name}.gds")
            c.plot()
            plt.savefig(gds_dir / f"{name}.png")
            plt.close()

            f.write('=== "Static"\n\n')
            f.write(f"    ![{name}](kwasm/gds/{name}.png)\n\n")
            f.write('=== "Dynamic"\n\n')
            f.write(
                f'    <iframe src="kwasm/viewer.html?url=gds/{name}.gds"'
                f' loading="lazy" width="100%" height="400"'
                f' style="border:none"></iframe>\n\n'
            )
            if glb_file:
                f.write('=== "3D"\n\n')
                f.write(
                    f'    <iframe class="viewer-3d"'
                    f' src="_static/3d/viewer.html?file={glb_file}"'
                    f' width="100%" height="500px" frameborder="0"'
                    f' loading="lazy"></iframe>\n\n'
                )
        except Exception as e:
            print(f"  [kwasm skip] {name}: {e}")

        f.write(
            f"""```python
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from ihp import PDK
from ihp import {import_alias}

PDK.activate()

c = {import_alias}.{name}({kwargs}).copy()
c.draw_ports()
c.plot()
```
"""
        )


_setup_kwasm_viewer()


# Write parametric cells page
with open(filepath_cells, "w+") as f:
    f.write(
        """

Parametric Cells
=============================

Here are the parametric components available in the PDK.
"""
    )

    for name in sorted(cells.keys()):
        if name in skip or name.startswith("_"):
            continue
        print(name)
        write_cell_entry(f, name, cells, "ihp.cells", "cells")
