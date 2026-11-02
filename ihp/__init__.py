"""IHP PDK."""

from typing import cast

from gdsfactory.get_factories import get_cells
from gdsfactory.pdk import Pdk
from gdsfactory.typings import (
    ConnectivitySpec,
)
from pdk_schema import MaterialCard

from ihp import cells, tech
from ihp.material_cards import MATERIAL_CARDS
from ihp.models import models
from ihp.tech import (
    LAYER,
    LAYER_STACK,
    LAYER_VIEWS,
    cross_sections,
    routing_strategies,
)

from .config import PATH

components = cells

__version__ = "2.0.1"
__all__ = [
    "PATH",
    "components",
    "tech",
    "LAYER",
    "cells",
    "cross_sections",
    "PDK",
    "MATERIAL_CARDS",
    "__version__",
]

# Connectivity stacks, named after the layers `LayerMapIHP` carries. A declared
# name is resolved against the layer map by every consumer that reads it
# (`gf.get_layer_info`), so the names have to be map members: the previous
# `METAL1`/`VIA1`/`CONT` spellings were members only until the map was renamed
# to the foundry's layer names (`64062f3`), and `POLY`/`ACTIVE` never were.
#
# Stack order and layer identity follow the foundry tech file checked in at
# `ihp/klayout/tech/sg13g2.lyt`, but only its base layers: the deck's symbols
# are region algebra as well (`Activ='1/0-Salblock'`, `Diff='Activ-GatPoly'`,
# `Metal1='8/0-8/29'`), which one (layer, datatype) name cannot express. The
# second stack is where that shows: extraction over raw `Activdrawing` merges
# the two contacted diffusions through the channel (2 nets) where the deck's
# `Diff` keeps them apart (3 nets).
connectivity = cast(
    list[ConnectivitySpec],
    [
        ("GatPolydrawing", "Contdrawing", "Metal1drawing"),
        ("Activdrawing", "Contdrawing", "Metal1drawing"),
        ("Metal1drawing", "Via1drawing", "Metal2drawing"),
        ("Metal2drawing", "Via2drawing", "Metal3drawing"),
        ("Metal3drawing", "Via3drawing", "Metal4drawing"),
        ("Metal4drawing", "Via4drawing", "Metal5drawing"),
        ("Metal5drawing", "TopVia1drawing", "TopMetal1drawing"),
        ("TopMetal1drawing", "TopVia2drawing", "TopMetal2drawing"),
    ],
)


class IhpPdk(Pdk):
    """IHP PDK with schema-backed material cards."""

    material_cards: dict[str, MaterialCard]

    def __init__(self, *, material_cards: dict[str, MaterialCard], **pdk_data):
        super().__init__(**pdk_data)
        self.material_cards = material_cards


_cells = get_cells(cells)
PDK = IhpPdk(
    name="IHP",
    cells=_cells,
    cross_sections=cross_sections,
    models=models,
    layers=LAYER,
    layer_stack=LAYER_STACK,
    layer_views=LAYER_VIEWS,
    connectivity=connectivity,
    routing_strategies=routing_strategies,
    material_cards=MATERIAL_CARDS,
)
