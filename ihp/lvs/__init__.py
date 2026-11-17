"""gflvs LVS rules for IHP SG13G2: ``gflvs.lvs(netlist, lib, DEFAULT_LVS_CONFIG)``.

Importing this package needs the ``gflvs`` library; importing ``ihp`` itself never does.
"""

from ihp.lvs.rules import (
    DEFAULT_LVS_CONFIG,
    DEVICE_TEMPLATES,
    LAYER_CONNECTIVITY,
    PARAMETER_EXTRACTORS,
    build_lvs_config,
)

__all__ = [
    "DEFAULT_LVS_CONFIG",
    "DEVICE_TEMPLATES",
    "LAYER_CONNECTIVITY",
    "PARAMETER_EXTRACTORS",
    "build_lvs_config",
]
