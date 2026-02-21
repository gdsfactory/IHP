"""Debug cells with port position issues in library."""

import gdsfactory as gf

from ihp import PDK

if __name__ == "__main__":
    PDK.activate()
    cell_name = "add_pads_top"
    cell_name = "bipolar"
    cell_name = "capacitor"
    cell_name = "cccs"
    cell_name = "ccvs"
    cell_name = "cmom"
    cell_name = "CuPillarPad"
    cell_name = "diode"
    cell_name = "inductor"
    cell_name = "isource"
    cell_name = "mos"
    cell_name = "npn13G2"
    cell_name = "pnpMPA"
    cell_name = "resistor"
    cell_name = "rfnmosHV"
    cell_name = "rfpmosHV"
    cell_name = "tline"
    cell_name = "vccs"
    cell_name = "vcvs"
    cell_name = "vsource"
    c = gf.get_component(cell_name)
    c.show()
