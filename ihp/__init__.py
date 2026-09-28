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

__version__ = "2.0.0"
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

connectivity = cast(
    list[ConnectivitySpec],
    [
        ("POLY", "CONT", "METAL1"),
        ("ACTIVE", "CONT", "METAL1"),
        ("METAL1", "VIA1", "METAL2"),
        ("METAL2", "VIA2", "METAL3"),
        ("METAL3", "VIA3", "METAL4"),
        ("METAL4", "VIA4", "METAL5"),
        ("METAL5", "TOPVIA1", "TOPMETAL1"),
        ("TOPMETAL1", "TOPVIA2", "TOPMETAL2"),
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
