"""A cell may only use a built-in GDSFactory+ editor symbol if its pins match.

For a built-in ``symbol`` type the editor draws that type's own pins and writes
the schematic's nets under those pin names (e.g. ``P``/``N`` for a capacitor).
A cell whose ports are named differently (``PLUS``/``MINUS``, a third ``BN``
pin, ...) then netlists with missing pins. Such cells must leave ``symbol``
unset so the editor uses the cell's own ports.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil

import pytest

import ihp.cells

# Pins of the editor's built-in symbols (gdsfactoryplus mosaic editor).
BUILTIN_SYMBOL_PINS = {
    "resistor": {"P", "N"},
    "capacitor": {"P", "N"},
    "inductor": {"P", "N"},
    "diode": {"P", "N"},
    "vsource": {"P", "N"},
    "isource": {"P", "N"},
    "nmos": {"D", "G", "S", "B"},
    "pmos": {"D", "G", "S", "B"},
    "npn": {"C", "B", "E"},
    "pnp": {"C", "B", "E"},
}


def _schematic_functions():
    for info in pkgutil.iter_modules(ihp.cells.__path__):
        module = importlib.import_module(f"ihp.cells.{info.name}")
        for name, fn in inspect.getmembers(module, inspect.isfunction):
            if name.endswith("_schematic") and not name.startswith("_"):
                if fn.__module__ == module.__name__:
                    yield pytest.param(fn, id=f"{info.name}.{name}")


@pytest.mark.parametrize("schematic_function", list(_schematic_functions()))
def test_builtin_symbol_matches_cell_pins(schematic_function) -> None:
    info = schematic_function().info
    symbol = info.get("symbol")
    if symbol not in BUILTIN_SYMBOL_PINS:
        return
    pins = {port["name"] for port in info.get("ports", [])}
    assert pins == BUILTIN_SYMBOL_PINS[symbol], (
        f"symbol {symbol!r} has pins {sorted(BUILTIN_SYMBOL_PINS[symbol])}, "
        f"cell has {sorted(pins)}"
    )
