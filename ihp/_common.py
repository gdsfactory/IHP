from __future__ import annotations

import gdsfactory as gf
from gdsfactory.add_pins import add_pin_rectangle_inside


def _add_pins(c: gf.Component) -> None:
    """Draw pin rectangles and register logical pins for all electrical ports."""
    by_name: dict[str, list] = {}
    for port in c.ports:
        if port.port_type == "electrical":
            by_name.setdefault(port.name, []).append(port)
    for name, ports in by_name.items():
        for port in ports:
            add_pin_rectangle_inside(c, port, layer=port.layer, layer_label=None)
        c.create_pin(ports=ports, name=name)
