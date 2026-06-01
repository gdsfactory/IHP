import inspect
import warnings

from gdsfactory.get_factories import get_cells

from ihp import PDK
from ihp import cells2 as cells2_module
from ihp import cells_fixed as cells_fixed_module
from ihp.config import PATH
from ihp.tech import LAYER_STACK, LAYER_VIEWS

warnings.filterwarnings("ignore", category=DeprecationWarning)

PDK.activate()

filepath_cells = PATH.repo / "docs" / "cells.md"
filepath_fixed = PATH.repo / "docs" / "cells_fixed.md"
filepath_cells2 = PATH.repo / "docs" / "cells2_reference.md"
filepath_3d = PATH.repo / "docs" / "_static" / "3d"
filepath_3d.mkdir(parents=True, exist_ok=True)

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

```python
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

        # Generate 3D GLB and embed via shared viewer
        glb_file = make_3d_glb(name, cell_dict)
        if glb_file:
            f.write(
                f"""
<iframe class="viewer-3d" src="_static/3d/viewer.html?file={glb_file}" width="100%" height="500px" frameborder="0" loading="lazy"></iframe>

"""
            )


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
