"""LVS configuration for the IHP SG13G2 BiCMOS PDK.

Layer data sourced from IHP SG13G2 process documentation and validated
against gflvs/tests/conftest.py (IHP_TECH_GDS_TABLE reference).

CONFIDENCE annotations:
  HIGH   — layer stack unambiguous, matches proven patterns
  MEDIUM — layer stack inferred from connectivity; single plausible interpretation
  LOW    — multiple interpretations possible; manual verification required
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from gflvs.gflvs_schema import (
    DeviceTemplate,
    DeviceTerminalTemplate,
    DeviceTerminalType,
    LayerBooleanOperation,
    LayerComposedOperation,
    LayerGds,
    LayerRef,
    LvsRunConfig,
    LvsRunMode,
)
from gflvs.gflvs_schema.lvs_config import ConnectivityKeyValuePair
from gflvs.helpers import lr
from gflvs.lvs import LvsResult, run_lvs

if TYPE_CHECKING:
    from gdsfactory import Component
    from gdstk import Library
    from gflvs.gflvs_schema.circuit import Circuit
    from gflvs.gflvs_schema.layout_to_netlist import Device
    from gflvs.gflvs_schema.layout_to_netlist import Port as SchemaPort
    from gflvs.tech import GdsTable

# ── GDS Layer Table ───────────────────────────────────────────────────────────
# Validated against IHP_TECH_GDS_TABLE in gflvs/tests/conftest.py.

GDS_TABLE: dict[str, LayerGds] = {
    "Activdrawing": LayerGds(layer=1, datatype=0),
    "Polydrawing": LayerGds(layer=5, datatype=0),
    "Contdrawing": LayerGds(layer=6, datatype=0),
    "Metal1drawing": LayerGds(layer=8, datatype=0),
    "Metal1label": LayerGds(layer=8, datatype=25),
    "Metal1pin": LayerGds(layer=8, datatype=2),
    "Via1drawing": LayerGds(layer=19, datatype=0),
    "Metal2drawing": LayerGds(layer=10, datatype=0),
    "Metal2label": LayerGds(layer=10, datatype=25),
    "Metal2pin": LayerGds(layer=10, datatype=2),
    "Via2drawing": LayerGds(layer=29, datatype=0),
    "Metal3drawing": LayerGds(layer=30, datatype=0),
    "Metal3label": LayerGds(layer=30, datatype=25),
    "Metal3pin": LayerGds(layer=30, datatype=2),
    "Via3drawing": LayerGds(layer=49, datatype=0),
    "Metal4drawing": LayerGds(layer=50, datatype=0),
    "Metal4label": LayerGds(layer=50, datatype=25),
    "Metal4pin": LayerGds(layer=50, datatype=2),
    "Via4drawing": LayerGds(layer=66, datatype=0),
    "Metal5drawing": LayerGds(layer=67, datatype=0),
    "Metal5label": LayerGds(layer=67, datatype=25),
    "Metal5pin": LayerGds(layer=67, datatype=2),
    "TopVia1drawing": LayerGds(layer=125, datatype=0),
    "TopMetal1drawing": LayerGds(layer=126, datatype=0),
    "TopMetal1label": LayerGds(layer=126, datatype=25),
    "TopMetal1pin": LayerGds(layer=126, datatype=2),
    "TopVia2drawing": LayerGds(layer=133, datatype=0),
    "TopMetal2drawing": LayerGds(layer=134, datatype=0),
    "TopMetal2label": LayerGds(layer=134, datatype=25),
    "TopMetal2pin": LayerGds(layer=134, datatype=2),
    "MIMdrawing": LayerGds(layer=36, datatype=0),
    "Vmimdrawing": LayerGds(layer=129, datatype=0),
    # Device label layer used for terminal intersection
    "DeviceLabel": LayerGds(layer=63, datatype=0),
}

# ── Layer Lists ───────────────────────────────────────────────────────────────

DRAWING_LAYERS: list[str] = [
    "Metal1drawing",
    "Metal2drawing",
    "Metal3drawing",
    "Metal4drawing",
    "Metal5drawing",
    "TopMetal1drawing",
    "TopMetal2drawing",
]

VIA_DRAWING_LAYERS: list[str] = [
    "Contdrawing",
    "Via1drawing",
    "Via2drawing",
    "Via3drawing",
    "Via4drawing",
    "TopVia1drawing",
    "TopVia2drawing",
    "Vmimdrawing",
    "MIMdrawing",
]

PIN_LOGIC_LAYERS: list[str] = [
    "Metal1pin",
    "Metal2pin",
    "Metal3pin",
    "Metal4pin",
    "Metal5pin",
    "TopMetal1pin",
    "TopMetal2pin",
]

LABEL_LOGIC_LAYERS: list[str] = [
    "Metal1label",
    "Metal2label",
    "Metal3label",
    "Metal4label",
    "Metal5label",
    "TopMetal1label",
    "TopMetal2label",
]

# ── Layer Connectivity ────────────────────────────────────────────────────────

LAYER_CONNECTIVITY: dict[str, list[str]] = {
    # pin → drawing
    "Metal1pin": ["Metal1drawing"],
    "Metal2pin": ["Metal2drawing"],
    "Metal3pin": ["Metal3drawing"],
    "Metal4pin": ["Metal4drawing"],
    "Metal5pin": ["Metal5drawing"],
    "TopMetal1pin": ["TopMetal1drawing"],
    "TopMetal2pin": ["TopMetal2drawing"],
    # substrate/gate → contact
    "Activdrawing": ["Contdrawing"],
    "Polydrawing": ["Contdrawing"],
    # contact/via → metal above
    "Contdrawing": ["Metal1drawing"],
    "Via1drawing": ["Metal2drawing"],
    "Via2drawing": ["Metal3drawing"],
    "Via3drawing": ["Metal4drawing"],
    "Via4drawing": ["Metal5drawing"],
    "TopVia1drawing": ["TopMetal1drawing"],
    "TopVia2drawing": ["TopMetal2drawing"],
    "Vmimdrawing": ["TopMetal1drawing"],
    # metal → via above
    "Metal1drawing": ["Via1drawing"],
    "Metal2drawing": ["Via2drawing"],
    "Metal3drawing": ["Via3drawing"],
    "Metal4drawing": ["Via4drawing"],
    "Metal5drawing": ["TopVia1drawing"],
    "TopMetal1drawing": ["TopVia2drawing"],
    "MIMdrawing": ["Vmimdrawing"],
}

# ── Device Family Switches ────────────────────────────────────────────────────

INCLUDE_NPN = True
INCLUDE_RFCMIM = True
INCLUDE_CMIM = True
INCLUDE_RESISTORS = True
INCLUDE_VIA_CELLS = True

# ── Terminal Helpers ──────────────────────────────────────────────────────────

_DEVICE_LABEL = LayerGds(layer=63, datatype=0)
_M1_PIN = LayerGds(layer=8, datatype=2)
_M2_PIN = LayerGds(layer=10, datatype=2)
_M5_PIN = LayerGds(layer=67, datatype=2)
_TM1_PIN = LayerGds(layer=126, datatype=2)
_M1_DRW = LayerGds(layer=8, datatype=0)
_M5_DRW = LayerGds(layer=67, datatype=0)
_TM1_DRW = LayerGds(layer=126, datatype=0)


def _label_intersection_terminal(uid: int, terminal_name: str, pin_layer_name: str, pin_layer_gds: LayerGds) -> DeviceTerminalTemplate:
    return DeviceTerminalTemplate(
        uid=uid,
        terminal_name=terminal_name,
        terminal_type=DeviceTerminalType.PIN,
        layer_composed_op=[
            LayerComposedOperation(
                layer_a_ref=LayerRef(canonical_layer_name=pin_layer_name, layer_gds=pin_layer_gds),
                layer_b_ref=LayerRef(canonical_layer_name="DeviceLabel", layer_gds=_DEVICE_LABEL),
                bool_op=LayerBooleanOperation.AND,
            ),
        ],
    )


def _pin_layer_terminal(uid: int, terminal_name: str, pin_layer_name: str, pin_layer_gds: LayerGds) -> DeviceTerminalTemplate:
    return DeviceTerminalTemplate(
        uid=uid,
        terminal_name=terminal_name,
        terminal_type=DeviceTerminalType.PIN,
        layer_composed_op=[
            LayerComposedOperation(
                layer_a_ref=LayerRef(canonical_layer_name=pin_layer_name, layer_gds=pin_layer_gds),
            ),
        ],
    )


# ── Device Templates ──────────────────────────────────────────────────────────

# CONFIDENCE: HIGH — validated against IHP 160GHz LNA test data in gflvs/tests/conftest.py
NPN13G2_TEMPLATE = DeviceTemplate(
    device_name="npn13G2",
    device_class_name="npn13G2",
    device_terminal_template=[
        _label_intersection_terminal(0, "Metal1_terminals", "Metal1pin", _M1_PIN),
        _label_intersection_terminal(1, "Metal2_terminals", "Metal2pin", _M2_PIN),
    ],
)

# CONFIDENCE: HIGH
RFCMIM_TEMPLATE = DeviceTemplate(
    device_name="rfcmim",
    device_class_name="rfcmim",
    device_terminal_template=[
        _label_intersection_terminal(0, "TopMetal1_terminals", "TopMetal1pin", _TM1_PIN),
        _label_intersection_terminal(1, "Metal5_terminals", "Metal5pin", _M5_PIN),
        _label_intersection_terminal(2, "Metal1_terminals", "Metal1pin", _M1_PIN),
    ],
)

# CONFIDENCE: HIGH
CMIM_TEMPLATE = DeviceTemplate(
    device_name="cmim",
    device_class_name="cmim",
    device_terminal_template=[
        _pin_layer_terminal(0, "MINUS", "Metal5drawing", _M5_DRW),
        _pin_layer_terminal(1, "PLUS", "TopMetal1drawing", _TM1_DRW),
    ],
)

# CONFIDENCE: HIGH
RHIGH_TEMPLATE = DeviceTemplate(
    device_name="rhigh",
    device_class_name="rhigh",
    device_terminal_template=[
        _pin_layer_terminal(0, "P1", "Metal1drawing", _M1_DRW),
        _pin_layer_terminal(1, "P2", "Metal1drawing", _M1_DRW),
    ],
)

# CONFIDENCE: HIGH
RSIL_TEMPLATE = DeviceTemplate(
    device_name="rsil",
    device_class_name="rsil",
    device_terminal_template=[
        _pin_layer_terminal(0, "P1", "Metal1drawing", _M1_DRW),
        _pin_layer_terminal(1, "P2", "Metal1drawing", _M1_DRW),
    ],
)

# CONFIDENCE: HIGH
VIA_TEMPLATE = DeviceTemplate(device_name="via_stack", device_class_name="via")

# ── Template Groups ───────────────────────────────────────────────────────────

NPN_TEMPLATES: list[DeviceTemplate] = [NPN13G2_TEMPLATE]
RFCMIM_TEMPLATES: list[DeviceTemplate] = [RFCMIM_TEMPLATE]
CMIM_TEMPLATES: list[DeviceTemplate] = [CMIM_TEMPLATE]
RESISTOR_TEMPLATES: list[DeviceTemplate] = [RHIGH_TEMPLATE, RSIL_TEMPLATE]
VIA_TEMPLATES: list[DeviceTemplate] = [VIA_TEMPLATE]

DEVICE_TEMPLATES: list[DeviceTemplate] = [
    *(NPN_TEMPLATES if INCLUDE_NPN else []),
    *(RFCMIM_TEMPLATES if INCLUDE_RFCMIM else []),
    *(CMIM_TEMPLATES if INCLUDE_CMIM else []),
    *(RESISTOR_TEMPLATES if INCLUDE_RESISTORS else []),
    *(VIA_TEMPLATES if INCLUDE_VIA_CELLS else []),
]

# ── Connectivity Pairs ────────────────────────────────────────────────────────

_CONNECTIVITY_PAIRS: list[ConnectivityKeyValuePair] = [
    ConnectivityKeyValuePair(source_layer=lr(src, GDS_TABLE), to=lr(dst, GDS_TABLE))
    for src, dsts in LAYER_CONNECTIVITY.items()
    for dst in dsts
    if src in GDS_TABLE and dst in GDS_TABLE
]

# ── Default LVS Config ────────────────────────────────────────────────────────

DEFAULT_LVS_CONFIG = LvsRunConfig(
    run_mode=LvsRunMode.HIERARCHICAL,
    drawing_layers=DRAWING_LAYERS,
    via_drawing_layers=VIA_DRAWING_LAYERS,
    pin_logic_layers=PIN_LOGIC_LAYERS,
    label_logic_layers=LABEL_LOGIC_LAYERS,
    layer_connectivity=_CONNECTIVITY_PAIRS,
    device_templates=DEVICE_TEMPLATES,
    dbu=1e3,
    precision=1e-3,
)

# ── Convenience Runner ────────────────────────────────────────────────────────


def run_lvs_ihp(
    lib: Library | Component,
    circuit: Circuit,
    *,
    config: LvsRunConfig | None = None,
    devices: list[Device] | None = None,
    components: list[Component] | None = None,
    device_ports: dict[str, dict[str, SchemaPort]] | None = None,
    tech_gds_table: GdsTable | None = None,
    original_file: str = "",
) -> LvsResult:
    """Run LVS for the IHP SG13G2 BiCMOS PDK with default configuration."""
    return run_lvs(
        lib,
        circuit,
        config or DEFAULT_LVS_CONFIG,
        devices=devices,
        components=components,
        device_ports=device_ports,
        tech_gds_table=tech_gds_table or GDS_TABLE,
        original_file=original_file,
    )
