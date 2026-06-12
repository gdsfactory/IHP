import base64
import inspect
import warnings

import kwasm.embed
import matplotlib as mpl
import matplotlib.pyplot as plt
from gdsfactory.get_factories import get_cells

from ihp import PDK
from ihp import cells2 as cells2_module
from ihp import cells_fixed as cells_fixed_module
from ihp.config import PATH
from ihp.tech import LAYER_STACK, LAYER_VIEWS

mpl.use("Agg")
warnings.filterwarnings("ignore", category=DeprecationWarning)

PDK.activate()

filepath_cells = PATH.repo / "docs" / "cells.md"
filepath_fixed = PATH.repo / "docs" / "cells_fixed.md"
filepath_cells2 = PATH.repo / "docs" / "cells2_reference.md"
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

        # Write GDS and save PNG for Static/Dynamic tabs
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
        except Exception as e:
            print(f"  [kwasm skip] {name}: {e}")

        # Generate 3D GLB and embed via shared viewer
        glb_file = make_3d_glb(name, cell_dict)
        if glb_file:
            f.write(
                f"""
<iframe class="viewer-3d" src="_static/3d/viewer.html?file={glb_file}" width="100%" height="500px" frameborder="0" loading="lazy"></iframe>

"""
            )

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


# Write deprecated fixed cells page
cells_fixed = get_cells(cells_fixed_module)

with open(filepath_fixed, "w+") as f:
    f.write(
        """

Fixed Cells (Deprecated)
=============================

.. deprecated:: v0.2.0
   The fixed-GDS cells below are deprecated. Use the equivalent pure-Python
   parametric cells from the :doc:`cells` page instead.
"""
    )

    for name in sorted(cells_fixed.keys()):
        if name in skip or name.startswith("_"):
            continue
        print(name)
        write_cell_entry(f, name, cells_fixed, "ihp.cells_fixed", "cells_fixed")


# Write cells2 PyCell reference page
cells2 = get_cells(cells2_module)

with open(filepath_cells2, "w+") as f:
    f.write(
        """

PyCell Reference (cells2)
=============================

These are reference implementations of the IHP SG13G2 PyCells, ported from the
original CNI (Cadence PyCell) library to GDSFactory. The ``ihp_pycell`` subfolder
contains the original CNI-based source code.

These cells serve as a validation reference for the primary parametric cells in
:doc:`cells`. They can also be used directly if needed.
"""
    )

    for name in sorted(cells2.keys()):
        if name in skip or name.startswith("_"):
            continue
        print(name)
        write_cell_entry(f, name, cells2, "ihp.cells2", "cells2")
