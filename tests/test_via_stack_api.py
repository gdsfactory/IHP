from __future__ import annotations

from ihp import PDK
from ihp.cells.via_stacks import via_stack


def test_default_call_settings_snapshot() -> None:
    """Pin the zero-arg default settings so the API rework can't silently change them."""
    PDK.activate()
    c = via_stack()
    d = c.to_dict(with_ports=True)
    assert d["settings"]["bottom_layer"] == "Metal1"
    assert d["settings"]["top_layer"] == "Metal2"
    assert d["settings"]["size"] == (10.0, 10.0)
    assert sorted(p.name for p in c.ports) == sorted(
        f"{label}_{direction}"
        for label in ("Metal1", "Metal2")
        for direction in ("N", "S", "E", "W")
    )
