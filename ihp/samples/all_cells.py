"""This script generates a reticle with all the cells in the library."""

import gdsfactory as gf

from ihp import LAYER, PDK

skip = {"all_cells", "extend_ports"}
skip.update(gf.gpdk.PDK.cells.keys())


@gf.cell
def all_cells() -> gf.Component:
    """Returns a sample reticle with all cells."""
    c = gf.Component()
    cells = []

    for cell_name, cell in PDK.cells.items():
        if cell_name in skip:
            continue
        try:
            cell_instance = cell()
            cells.append(cell_instance)
        except Exception as e:
            print(f"Error instantiating cell {cell_name}: {e}")

    cell_matrix = c << gf.pack(cells)[0]
    floorplan = c << gf.c.rectangle(
        size=(cell_matrix.xsize + 20, cell_matrix.ysize + 20),
        layer=LAYER.Recogdrawing,
    )
    floorplan.center = cell_matrix.center
    return c


if __name__ == "__main__":
    PDK.activate()
    c = all_cells()
    gdspath = c.write_gds()
    gf.show(gdspath)
