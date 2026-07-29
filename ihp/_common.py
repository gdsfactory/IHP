from __future__ import annotations

from functools import partial

from gdsfactory.add_pins import add_electric_pins

from ihp.tech import LAYER

# NOTE: pin_layer_map values are set to None to skip Pin geometry drawing
# on the respective Pin layers, avoiding XOR-diff test failures for now.
# Only logical schematic pin aggregation of the ports is performed via
# component.create_pin(). A future pass will add actual Pin geometry on
# the PDK's pin drawing layers.
_add_pins = partial(
    add_electric_pins,
    pin_layer_map={
        LAYER.Metal1drawing: None,
        LAYER.Metal2drawing: None,
        LAYER.Metal3drawing: None,
        LAYER.Metal4drawing: None,
        LAYER.Metal5drawing: None,
        LAYER.TopMetal1drawing: None,
        LAYER.TopMetal2drawing: None,
    },
)
