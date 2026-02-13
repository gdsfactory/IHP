import os

import gdsfactory as gf  # to have gf.Component
import pya  # KLayout Python API

from cni.dlo import PCellWrapper  # to wrap the PyCell
from cni.tech import Tech  # to get the technology


def generate_gf_from_ihp(cell_name, cell_params, function_name) -> gf.Component:
    # ----------------------------------------------------------------
    # Step 1: Get the technology object
    # ----------------------------------------------------------------
    tech = Tech.get("SG13_dev")  # Must match the name registered in SG13_Tech

    # ----------------------------------------------------------------
    # Step 2: Create a layout and a cell
    # ----------------------------------------------------------------
    layout = pya.Layout()  # new empty layout
    cell = layout.create_cell(cell_name)  # new cell for your transistor

    # ----------------------------------------------------------------
    # Step 3: Wrap the PyCell
    # ----------------------------------------------------------------
    # PCellWrapper acts like the 'specs' object in KLayout
    # It handles parameter declarations and calls defineParamSpecs internally
    device = PCellWrapper(impl=function_name, tech=tech)

    # Convert params into a list in the order of device.param_decls
    param_values = [cell_params[p.name] for p in device.param_decls]

    # ----------------------------------------------------------------
    # Step 4: Produce the layout
    # ----------------------------------------------------------------
    device.produce(
        layout=layout,
        layers={},  # can pass layer map if needed
        parameters=param_values,
        cell=cell,
    )

    # ----------------------------------------------------------------
    # Step 5: Bring to GDSFactory
    # ----------------------------------------------------------------
    layout.write("temp.gds")
    print(f"{cell_name} PyCell placed successfully and GDS written.")
    c = gf.read.import_gds(gdspath="temp.gds")
    os.remove("temp.gds")
    # ----------------------------------------------------------------

    return c


def add_port_group(c: gf.component, ref, ports: list, prefix: str = ""):
    """
    Add a group of ports from a reference component to a target component,
    optionally renaming them with a prefix.

    Parameters
    ----------
    c : gf.Component
        The component to which the ports will be added.
    ref : gf.ComponentReference or similar
        The referenced component from which ports are copied.
    ports : list of str
        A list of port names to copy from `ref` to `c`.
    prefix : str, optional
        A string to prepend to each added port's name, by default "".

    Returns
    -------
    gf.Component
        The updated component `c` with the copied ports added.

    Notes
    -----
    - Each port in `ports` must exist in `ref.ports`.
    - Port objects are not deep-copied; the function attaches the same
      `ref.ports[p]` objects to `c` under new names.
    """
    for p in ports:
        c.add_port(name=prefix + p, port=ref.ports[p])

    return c


def change_port_orientation(c: gf.component, ports, orientation: int):
    """
    Change the orientation value of one or more ports in a component.

    Parameters
    ----------
    c : gf.Component
        The component whose port orientations will be modified.
    ports : iterable of str
        Names of the ports in `c` whose orientation should be updated.
    orientation : int
        The new orientation angle (in degrees) to assign to each port.

    Returns
    -------
    gf.Component
        The updated component `c` with modified port orientations.

    Notes
    -----
    - Each port name in `ports` must exist in `c.ports`.
    - Orientation is typically one of {0, 90, 180, 270} in gdsfactory
      conventions, but arbitrary integer angles are allowed.
    """
    for p in ports:
        c.ports[p].orientation = orientation

    return c
