from __future__ import annotations

import pytest

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


def test_layers_kwarg_maps_to_bottom_top_layer() -> None:
    """The gdsfactory-shaped `layers` kwarg should pick bottom/top from its ends.

    gdsfactory's @cell decorator captures settings before the body runs, so
    we verify the translation by checking the resulting ports rather than
    d["settings"]["top_layer"] (which reflects the formal parameter default).
    """
    PDK.activate()
    c = via_stack(layers=("Metal1", "Metal3"))
    port_names = [p.name for p in c.ports]
    assert any("Metal1" in n for n in port_names), (
        f"Expected Metal1 ports, got {port_names}"
    )
    assert any("Metal3" in n for n in port_names), (
        f"Expected Metal3 ports, got {port_names}"
    )


@pytest.mark.parametrize(
    "kwarg,value",
    [
        ("vias", ("via1", "via2", None)),
        ("layer_offsets", (0.0, 0.0)),
        ("layer_to_port_orientations", {}),
        ("correct_size", True),
        ("slot_horizontal", True),
        ("slot_vertical", True),
        ("port_orientations", (0, 180)),
    ],
)
def test_unsupported_generic_kwargs_raise_not_implemented(kwarg, value) -> None:
    """Generic features IHP's via_stack cannot honor must fail loudly, not silently."""
    PDK.activate()
    with pytest.raises(NotImplementedError):
        via_stack(**{kwarg: value})


def test_layers_and_explicit_layers_raises_value_error() -> None:
    """Specifying both layers and explicit bottom_layer/top_layer should raise ValueError."""
    PDK.activate()
    with pytest.raises(ValueError):
        via_stack(layers=("Metal1", "Metal3"), bottom_layer="Metal2")
