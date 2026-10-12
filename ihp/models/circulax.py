"""Circulax adapters using the same native libraries and metadata as VACASK."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any


def with_circulax_models(models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Advertise Circulax beside VACASK without duplicating geometry equations."""
    result = list(models)
    for model in models:
        if model.get("implementation") == "VACASK":
            entry = deepcopy(model)
            entry["implementation"] = "Circulax"
            entry["dialect"] = "vacask"
            result.append(entry)
    return result


def resolve_component(
    models: list[dict[str, Any]],
    properties: Mapping[str, float],
    connections: Mapping[str, str],
    *,
    corner: str | None = None,
    name: str = "X1",
    temperature_c: float = 27.0,
):
    """Resolve schematic properties, pin order and corner to compact-model leaves.

    Circulax and NetlistParse are optional dependencies, imported only on use.
    `models` is the schematic's info["models"], and properties use cell units.
    Unknown corner names or missing terminals are errors.
    """
    from circulax.netlist_io import Library, NetlistError
    from circulax.netlist_io.expressions import evaluate_source

    available = [model for model in models if model.get("implementation") == "Circulax"]
    if len(available) != 1:
        raise NetlistError(f"expected one Circulax model, found {len(available)}")
    model = available[0]
    sections = model.get("sections", [])
    selected = corner if corner is not None else (sections[0] if sections else None)
    if selected is not None and selected not in sections:
        raise NetlistError(f"unsupported corner {selected!r}; choose from {sections}")
    nodes = tuple(connections[port] for port in model["port_order"])
    settings = {
        key: evaluate_source(str(expression), dict(properties))
        for key, expression in model.get("params", {}).items()
    }
    root = Path(__file__).resolve().parents[2]
    library = Library.from_file(
        root / model["library"],
        section=selected,
        temperature_c=temperature_c,
        dialect=model.get("dialect", "vacask"),
    )
    return library.instantiate(model["name"], nodes, settings, name=name)
