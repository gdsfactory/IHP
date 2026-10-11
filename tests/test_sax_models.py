"""Tests for IHP SAX models."""

import inspect

import jax.numpy as jnp
import pytest

from ihp import cells
from ihp.models.sax import models
from ihp.models.sax.capacitors import (
    cmim,
    cmim_capacitance,
    cmom,
    cmom_capacitance,
    rfcmim,
)
from ihp.models.sax.inductors import inductor2, inductor3, inductor_with_loss
from ihp.models.sax.resistors import resistor, rhigh, rppd, rsil

# -- helpers ---------------------------------------------------------------

F = jnp.linspace(1e9, 20e9, 101)
F_SINGLE = jnp.array([5e9])

TWO_PORT_KEYS = {("o1", "o1"), ("o1", "o2"), ("o2", "o1"), ("o2", "o2")}


def _check_two_port(result):
    """Shared sanity checks: keys, reciprocity, passivity, finiteness."""
    assert set(result.keys()) == TWO_PORT_KEYS

    # reciprocity
    assert jnp.allclose(result[("o1", "o2")], result[("o2", "o1")], atol=1e-9)

    # passivity: |S11|^2 + |S21|^2 <= 1
    power = jnp.abs(result[("o1", "o1")]) ** 2 + jnp.abs(result[("o2", "o1")]) ** 2
    assert jnp.all(power <= 1.0 + 1e-6)

    # no NaN/Inf
    for v in result.values():
        assert jnp.all(jnp.isfinite(v))


# -- resistor --------------------------------------------------------------


class TestResistor:
    def test_basics(self):
        _check_two_port(resistor(f=F, resistance=100.0))

    def test_50ohm_in_50ohm_system(self):
        """S11 = Z/(Z+2*Z0) = 50/150 = 1/3."""
        s = resistor(f=F_SINGLE, resistance=50.0, z0=50.0)
        assert abs(float(jnp.abs(s[("o1", "o1")])[0]) - 1 / 3) < 1e-6

    def test_zero_resistance(self):
        s = resistor(f=F_SINGLE, resistance=0.0)
        assert abs(float(jnp.abs(s[("o1", "o2")])[0]) - 1.0) < 1e-6

    def test_output_length(self):
        s = resistor(f=F, resistance=100.0)
        assert len(s[("o1", "o1")]) == len(F)


class TestRsil:
    def test_basics(self):
        _check_two_port(rsil(f=F, width=1.0, length=10.0))

    def test_one_square_is_7_ohm(self):
        s = rsil(f=F_SINGLE, width=1.0, length=1.0)
        expected = 7.0 / (7.0 + 2 * 50.0)
        assert abs(float(jnp.abs(s[("o1", "o1")])[0]) - expected) < 1e-6

    def test_longer_means_more_reflection(self):
        s1 = rsil(f=F_SINGLE, width=1.0, length=1.0)
        s2 = rsil(f=F_SINGLE, width=1.0, length=2.0)
        assert float(jnp.abs(s2[("o1", "o1")])[0]) > float(jnp.abs(s1[("o1", "o1")])[0])


class TestRppd:
    def test_basics(self):
        _check_two_port(rppd(f=F, width=1.0, length=10.0))

    def test_higher_rsh_than_rsil(self):
        s_lo = rsil(f=F_SINGLE, width=1.0, length=1.0)
        s_hi = rppd(f=F_SINGLE, width=1.0, length=1.0)
        assert float(jnp.abs(s_hi[("o1", "o1")])[0]) > float(
            jnp.abs(s_lo[("o1", "o1")])[0]
        )


class TestRhigh:
    def test_basics(self):
        _check_two_port(rhigh(f=F, width=0.5, length=10.0))

    def test_highest_rsh(self):
        s_mid = rppd(f=F_SINGLE, width=1.0, length=1.0)
        s_hi = rhigh(f=F_SINGLE, width=1.0, length=1.0)
        assert float(jnp.abs(s_hi[("o1", "o1")])[0]) > float(
            jnp.abs(s_mid[("o1", "o1")])[0]
        )


# -- capacitors ------------------------------------------------------------


class TestCmimCapacitance:
    def test_known_value(self):
        """7x7 um MIM should be ~74.8 fF."""
        c = cmim_capacitance(length=7.0, width=7.0)
        assert 70e-15 < c < 80e-15

    def test_scales_with_area(self):
        """Doubling both dimensions ~ 4x capacitance."""
        c1 = cmim_capacitance(length=10.0, width=10.0)
        c2 = cmim_capacitance(length=20.0, width=20.0)
        assert 3.5 < c2 / c1 < 4.5

    def test_positive(self):
        assert cmim_capacitance() > 0


class TestCmim:
    def test_basics(self):
        _check_two_port(cmim(f=F, length=10.0, width=10.0))

    def test_more_transparent_at_higher_freq(self):
        s = cmim(f=jnp.array([1e9, 10e9]), length=10.0, width=10.0)
        assert float(jnp.abs(s[("o1", "o2")])[1]) > float(jnp.abs(s[("o1", "o2")])[0])

    def test_bigger_cap_more_transparent(self):
        s_small = cmim(f=F_SINGLE, length=7.0, width=7.0)
        s_big = cmim(f=F_SINGLE, length=50.0, width=50.0)
        assert float(jnp.abs(s_big[("o1", "o2")])[0]) > float(
            jnp.abs(s_small[("o1", "o2")])[0]
        )


class TestRfcmim:
    def test_basics(self):
        _check_two_port(rfcmim(f=F, length=10.0, width=10.0, wfeed=2.0))

    def test_differs_from_ideal(self):
        """Parasitics should visibly shift S-params from ideal cmim."""
        s_ideal = cmim(f=F, length=10.0, width=10.0)
        s_rf = rfcmim(f=F, length=10.0, width=10.0, wfeed=2.0)
        diff = jnp.max(jnp.abs(s_ideal[("o1", "o1")] - s_rf[("o1", "o1")]))
        assert float(diff) > 1e-4


class TestCmom:
    def test_basics(self):
        _check_two_port(cmom(f=F, nfingers=4, length=10.0))

    def test_more_fingers_more_capacitance(self):
        s1 = cmom(f=F_SINGLE, nfingers=2, length=10.0)
        s2 = cmom(f=F_SINGLE, nfingers=8, length=10.0)
        assert float(jnp.abs(s2[("o1", "o2")])[0]) > float(jnp.abs(s1[("o1", "o2")])[0])


class TestCmomCapacitance:
    def test_positive(self):
        assert cmom_capacitance(nfingers=4, length=10.0) > 0

    def test_scales_with_fingers(self):
        assert cmom_capacitance(nfingers=8) > cmom_capacitance(nfingers=2)


# -- inductors -------------------------------------------------------------


class TestInductorWithLoss:
    def test_basics(self):
        _check_two_port(inductor_with_loss(f=F, inductance=1e-9, resistance=1.0))

    def test_reflection_increases_with_freq(self):
        s = inductor_with_loss(
            f=jnp.array([1e9, 10e9]), inductance=1e-9, resistance=0.5
        )
        assert float(jnp.abs(s[("o1", "o1")])[1]) > float(jnp.abs(s[("o1", "o1")])[0])

    def test_transparent_near_dc(self):
        s = inductor_with_loss(f=jnp.array([1e3]), inductance=1e-12, resistance=0.0)
        assert float(jnp.abs(s[("o1", "o2")])[0]) > 0.99

    def test_resistance_reduces_transmission(self):
        s_lo = inductor_with_loss(f=jnp.array([1e6]), inductance=1e-12, resistance=0.0)
        s_hi = inductor_with_loss(f=jnp.array([1e6]), inductance=1e-12, resistance=10.0)
        assert float(jnp.abs(s_hi[("o1", "o2")])[0]) < float(
            jnp.abs(s_lo[("o1", "o2")])[0]
        )


class TestInductor2:
    def test_basics(self):
        _check_two_port(inductor2(f=F))

    def test_runs_with_defaults(self):
        s = inductor2(f=F_SINGLE)
        assert isinstance(s, dict) and len(s) == 4


class TestInductor3:
    def test_basics(self):
        _check_two_port(inductor3(f=F))


# -- models dict -----------------------------------------------------------


class TestModelsDict:
    def test_expected_keys(self):
        expected = {
            "resistor",
            "rsil",
            "rppd",
            "rhigh",
            "cmim",
            "rfcmim",
            "cmom",
            "inductor2",
            "inductor3",
            "inductor_with_loss",
        }
        assert set(models.keys()) == expected

    def test_all_run_with_defaults(self):
        for name, fn in models.items():
            result = fn()
            assert isinstance(result, dict) and len(result) == 4, name


def _defaults(func) -> dict:
    func = getattr(func, "__wrapped__", func)
    return {
        name: p.default
        for name, p in inspect.signature(func).parameters.items()
        if p.default is not inspect.Parameter.empty
    }


@pytest.mark.parametrize(
    "name", sorted(name for name in models if hasattr(cells, name))
)
def test_model_defaults_match_cell(name):
    """A model's defaults must describe the default layout of the matching cell."""
    model_defaults = _defaults(models[name])
    cell_defaults = _defaults(getattr(cells, name))
    shared = model_defaults.keys() & cell_defaults.keys()
    mismatched = {
        k: (model_defaults[k], cell_defaults[k])
        for k in shared
        if model_defaults[k] != pytest.approx(cell_defaults[k])
    }
    assert not mismatched, f"(model, cell) defaults differ: {mismatched}"
