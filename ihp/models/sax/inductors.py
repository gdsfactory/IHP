"""
SAX inductor models for IHP SG13G2.

Models inductor2 and inductor3 as lossy R+jωL series impedance.
Default values match the PCell defaults in cells/inductors.py.
"""

from functools import partial

import jax
import jax.numpy as jnp
import sax
from sax.models.rf import impedance

from ihp.models.sax.constants import DEFAULT_FREQUENCY, Z0_DEFAULT

__all__ = ["inductor_with_loss", "inductor2", "inductor3"]


@partial(jax.jit, inline=True)
def inductor_with_loss(
    *,
    f: sax.FloatArrayLike = DEFAULT_FREQUENCY,
    inductance: float = 1e-9,
    resistance: float = 0.0,
    z0: sax.ComplexLike = Z0_DEFAULT,
) -> sax.SDict:
    """Two-port inductor with series DC resistance.

    Z = R + j*omega*L

    Args:
        f: Frequency in Hz.
        inductance: Inductance in Henries.
        resistance: Series resistance in Ohm.
        z0: Reference impedance in Ohm.
    """
    f_arr = jnp.asarray(f)
    z = resistance + 1j * 2 * jnp.pi * f_arr * inductance
    return impedance(f=f_arr, z=z, z0=z0)


@partial(jax.jit, inline=True)
def inductor2(
    *,
    f: sax.FloatArrayLike = DEFAULT_FREQUENCY,
    inductance: float = 33.303e-12,
    resistance: float = 0.5777,
    z0: sax.ComplexLike = Z0_DEFAULT,
) -> sax.SDict:
    """IHP inductor2 PCell — 2-terminal spiral on TopMetal1/TopMetal2.

    Args:
        f: Frequency in Hz.
        inductance: Inductance in Henries (default: 33.3 pH from PCell).
        resistance: Series DC resistance in Ohm (default: 0.578 from PCell).
        z0: Reference impedance in Ohm.
    """
    return inductor_with_loss(f=f, inductance=inductance, resistance=resistance, z0=z0)


@partial(jax.jit, inline=True)
def inductor3(
    *,
    f: sax.FloatArrayLike = DEFAULT_FREQUENCY,
    inductance: float = 221.5e-12,
    resistance: float = 1.386,
    z0: sax.ComplexLike = Z0_DEFAULT,
) -> sax.SDict:
    """IHP inductor3 PCell — 3-terminal (centre-tapped) spiral.

    The 2-port model represents the full inductance between outer terminals.
    For centre-tap use, split into two inductor_with_loss in series.

    Args:
        f: Frequency in Hz.
        inductance: Total inductance in Henries (default: 221.5 pH from PCell).
        resistance: Total series resistance in Ohm (default: 1.386 from PCell).
        z0: Reference impedance in Ohm.
    """
    return inductor_with_loss(f=f, inductance=inductance, resistance=resistance, z0=z0)
