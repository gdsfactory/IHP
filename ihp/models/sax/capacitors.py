"""
SAX capacitor models for IHP SG13G2.

Covers cmim (MIM), rfcmim (RF MIM with parasitics), and cmom (finger cap).
Capacitance formulas match the IHP SPICE model libraries and PCell extractors.
"""

from collections.abc import Sequence
from functools import partial

import jax
import jax.numpy as jnp
import sax
import scipy.constants
from sax.models.rf import capacitor, impedance

from ihp.models.sax.constants import (
    CMIM_CASPEC,
    CMIM_CPSPEC,
    CMIM_LWD,
    CMIM_SERIES_R,
    CMOM_DIELECTRIC_CONSTANT,
    CMOM_FRINGE_FACTOR,
    CMOM_LAYER_THICKNESS,
    DEFAULT_FREQUENCY,
    RFCMIM_CASPEC,
    RFCMIM_CPSPEC,
    RFCMIM_LWD,
    Z0_DEFAULT,
)

__all__ = [
    "cmim",
    "cmim_capacitance",
    "cmom",
    "cmom_capacitance",
    "rfcmim",
    "rfcmim_capacitance",
]

EPS_0 = scipy.constants.epsilon_0


# -- capacitance extraction ------------------------------------------------


def cmim_capacitance(
    length: float = 7.0,
    width: float = 7.0,
    caspec: float = CMIM_CASPEC,
    cpspec: float = CMIM_CPSPEC,
    lwd: float = CMIM_LWD,
) -> float:
    """MIM capacitance from drawn dimensions (area + perimeter model).

    C = Leff * Weff * caspec + 2*(Leff + Weff) * cpspec

    Returns capacitance in Farads.
    """
    l_eff = length + lwd
    w_eff = width + lwd
    c_ff = l_eff * w_eff * caspec + 2.0 * (l_eff + w_eff) * cpspec
    return c_ff * 1e-15  # fF -> F


def rfcmim_capacitance(
    length: float = 7.0,
    width: float = 7.0,
) -> float:
    """RF MIM core capacitance. Same formula as cmim."""
    return cmim_capacitance(
        length=length,
        width=width,
        caspec=RFCMIM_CASPEC,
        cpspec=RFCMIM_CPSPEC,
        lwd=RFCMIM_LWD,
    )


def cmom_capacitance(
    nfingers: int = 1,
    length: float = 4.0,
    spacing: float = 0.26,
    min_width: float = 0.2,
    mom_metals: Sequence[str] = ("Metal1", "Metal2", "Metal3"),
) -> float:
    """CMOM finger capacitance. Matches cmom_extractor in cells/capacitors.py.

    Returns capacitance in Farads.
    """
    eps0_um = EPS_0 * 1e-6  # F/m -> F/um
    total = 0.0
    for metal in mom_metals:
        th = CMOM_LAYER_THICKNESS.get(metal, 0.49)
        total += (
            CMOM_DIELECTRIC_CONSTANT
            * eps0_um
            * (th / spacing)
            * ((nfingers * 2) * (length + spacing) + min_width * (nfingers * 2 + 1))
        )
    return total * (1 + CMOM_FRINGE_FACTOR)


# -- SAX models ------------------------------------------------------------


@partial(jax.jit, inline=True)
def cmim(
    *,
    f: sax.FloatArrayLike = DEFAULT_FREQUENCY,
    length: float = 6.0,
    width: float = 6.0,
    series_resistance: float = CMIM_SERIES_R,
    z0: sax.ComplexLike = Z0_DEFAULT,
) -> sax.SDict:
    """MIM capacitor with series resistance from top plate.

    Args:
        f: Frequency in Hz.
        length: Drawn length in um (7-75 typical).
        width: Drawn width in um (7-75 typical).
        series_resistance: Top plate resistance in Ohm.
        z0: Reference impedance in Ohm.
    """
    f_arr = jnp.asarray(f)
    cap = cmim_capacitance(length=length, width=width)
    z_cap = 1.0 / (1j * 2 * jnp.pi * f_arr * cap)
    return impedance(f=f_arr, z=z_cap + series_resistance, z0=z0)


@partial(jax.jit, inline=True)
def rfcmim(
    *,
    f: sax.FloatArrayLike = DEFAULT_FREQUENCY,
    length: float = 7.0,
    width: float = 7.0,
    wfeed: float = 2.0,
    z0: sax.ComplexLike = Z0_DEFAULT,
) -> sax.SDict:
    """RF MIM capacitor with parasitic inductances and resistances.

    Parasitic values from empirical curve fits in capacitors_mod.lib.
    Series chain: Lskin + Rskin + Lmim + Rmim + Cmim + Lfeed.

    Args:
        f: Frequency in Hz.
        length: Drawn length in um (7-75).
        width: Drawn width in um (7-75).
        wfeed: Feed width in um (1-30, max = width - 1.2).
        z0: Reference impedance in Ohm.
    """
    f_arr = jnp.asarray(f)
    omega = 2 * jnp.pi * f_arr

    # parasitic values from SPICE empirical expressions (dimensions in um)
    lplate = (0.353158 * length + 0.485684 * length / width) * 1e-12
    lfeed = (
        6.03468 + 0.0814268 * width - 0.821243 * jnp.log(wfeed) / jnp.log(1.55)
    ) * 1e-12
    lskin = 1.18545e-12 + 6.95462e-14 * length
    rmim = (
        0.0463973
        + 0.00219577 * length / width
        + 0.961292 / wfeed
        + 0.00307712 * length
        + 0.000217076 * length * length / width
    )
    rskin = 0.154618 + 0.00702016 * length

    cap = rfcmim_capacitance(length=length, width=width)

    z_total = (
        rskin
        + 1j * omega * lskin
        + 1j * omega * jnp.maximum(lplate - lskin, 1e-18)
        + rmim
        + 1.0 / (1j * omega * cap)
        + 1j * omega * jnp.maximum(lfeed, 1e-18)
    )
    return impedance(f=f_arr, z=z_total, z0=z0)


def cmom(
    *,
    f: sax.FloatArrayLike = DEFAULT_FREQUENCY,
    nfingers: int = 1,
    length: float = 4.0,
    spacing: float = 0.26,
    min_width: float = 0.2,
    mom_metals: Sequence[str] = ("Metal1", "Metal2", "Metal3"),
    z0: sax.ComplexLike = Z0_DEFAULT,
) -> sax.SDict:
    """Metal-oxide-metal finger capacitor.

    Args:
        f: Frequency in Hz.
        nfingers: Number of fingers.
        length: Finger length in um.
        spacing: Finger spacing in um.
        min_width: Finger width in um.
        mom_metals: Metal layers to include.
        z0: Reference impedance in Ohm.
    """
    cap = cmom_capacitance(
        nfingers=nfingers,
        length=length,
        spacing=spacing,
        min_width=min_width,
        mom_metals=mom_metals,
    )
    return capacitor(f=f, capacitance=cap, z0=z0)
