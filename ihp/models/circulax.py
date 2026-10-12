"""Shared parameterized native models for IHP schematic simulation.

Imported by model resolution, never by ordinary PDK or metadata imports.
"""

from __future__ import annotations

import inspect
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from circulax.netlist_io import Library, LibraryModel, NetlistError
from circulax.netlist_io.expressions import evaluate_source

from ihp._schematic import BONDPAD_SHAPES, native_port_map
from ihp.cells import (
    antennas,
    bjt_transistors,
    bondpads,
    capacitors,
    fet_transistors,
    passives,
    resistors,
    rf_transistors,
)

try:
    import vacask_bin
except ImportError:
    vacask_bin = None

_ROOT = Path(__file__).resolve().parents[2]
_FACTORIES = (
    antennas.dantenna_schematic,
    antennas.dpantenna_schematic,
    bondpads.bondpad_schematic,
    passives.svaricap_schematic,
    passives.esd_nmos_schematic,
    passives.ptap1_schematic,
    passives.ntap1_schematic,
    fet_transistors.nmos_schematic,
    fet_transistors.pmos_schematic,
    fet_transistors.nmos_hv_schematic,
    fet_transistors.pmos_hv_schematic,
    rf_transistors.rfnmos_schematic,
    rf_transistors.rfpmos_schematic,
    rf_transistors.rfnmos_hv_schematic,
    rf_transistors.rfpmos_hv_schematic,
    bjt_transistors.npn13G2_schematic,
    bjt_transistors.npn13G2L_schematic,
    bjt_transistors.npn13G2V_schematic,
    bjt_transistors.pnpMPA_schematic,
    capacitors.cmim_schematic,
    capacitors.rfcmim_schematic,
    resistors.rsil_schematic,
    resistors.rppd_schematic,
    resistors.rhigh_schematic,
)


def _library_model(factory) -> LibraryModel:
    """Reuse native declarations, separating micrometer units from expressions.

    @tags circulax-simulation
    """
    declaration = next(
        entry
        for entry in factory().info["models"]
        if entry.get("implementation") == "NgSpice"
    )
    defaults = {
        name: parameter.default
        for name, parameter in inspect.signature(factory).parameters.items()
        if isinstance(parameter.default, float | int)
    }
    params_map = {}
    units = {}
    expressions = {}
    for target, expression in declaration.get("params", {}).items():
        match = re.fullmatch(r"([A-Za-z_]\w*) \* 1e-6", expression)
        if match:
            source = match.group(1)
            params_map[source] = target
            units[source] = ("um", "m")
        elif expression.isidentifier():
            params_map[expression] = target
        else:
            expressions[target] = expression
    # Keep unknown layout-only settings out of the native parameter dictionary.
    # Identity expressions let LibraryModel select only explicitly mapped inputs.
    for source, target in params_map.items():
        expressions[target] = source
    parameter_values = {}
    if factory is bondpads.bondpad_schematic:
        defaults["shape"] = inspect.signature(factory).parameters["shape"].default
        parameter_values["shape"] = BONDPAD_SHAPES
        params_map["shape"] = "shape"
        expressions["shape"] = "shape"
    module_paths = tuple(
        Path(path)
        for path in os.environ.get("IHP_CIRCULAX_MODULE_PATHS", "").split(os.pathsep)
        if path
    )
    if not module_paths and vacask_bin is not None:
        module_paths = (Path(vacask_bin.MOD_DIR),)
    compiler = os.environ.get("IHP_CIRCULAX_COMPILER")
    if compiler is None and vacask_bin is not None:
        compiler = str(vacask_bin.OPENVAF_CMD)
    osdi_modules = tuple(
        Path(path)
        for path in os.environ.get("IHP_CIRCULAX_OSDI_MODULES", "").split(os.pathsep)
        if path
    )
    sections = tuple(declaration.get("sections", ()))
    return LibraryModel.from_file(
        _ROOT / declaration["library"],
        declaration["name"],
        section=sections[0] if sections else None,
        sections=sections,
        dialect="ngspice",
        defaults=defaults,
        params_map=params_map,
        parameter_units=units,
        parameter_values=parameter_values,
        expressions=expressions,
        port_map=native_port_map(
            factory.__name__.removesuffix("_schematic"), declaration["port_order"]
        ),
        module_paths=module_paths,
        compiler=compiler,
        osdi_modules=osdi_modules,
        state_policy="limiting_only",
    )


for _factory in _FACTORIES:
    globals()[_factory.__name__.removesuffix("_schematic")] = _library_model(_factory)


def resolve_component(
    models: list[dict[str, Any]],
    properties: Mapping[str, float],
    connections: Mapping[str, str],
    *,
    corner: str | None = None,
    name: str = "X1",
    temperature_c: float = 27.0,
):
    """Retain the card-resolution adapter for non-solver library inspection.

    @tags circulax-simulation
    """
    entries = [entry for entry in models if entry.get("implementation") == "NgSpice"]
    if len(entries) != 1:
        raise NetlistError(
            f"expected one NgSpice library declaration, found {len(entries)}"
        )
    model = entries[0]
    sections = model.get("sections", [])
    selected = corner if corner is not None else (sections[0] if sections else None)
    if selected is not None and selected not in sections:
        raise NetlistError(f"unsupported corner {selected!r}; choose from {sections}")
    nodes = tuple(connections[port] for port in model["port_order"])
    settings = {
        key: evaluate_source(str(expression), dict(properties))
        for key, expression in model.get("params", {}).items()
    }
    library = Library.from_file(
        _ROOT / model["library"],
        section=selected,
        temperature_c=temperature_c,
        dialect="ngspice",
    )
    return library.instantiate(model["name"], nodes, settings, name=name)
