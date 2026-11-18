# PEX with gfpex — IHP SG13G2

`ihp/pex/rules.py` holds the default [gfpex](https://github.com/doplaydo/gf-pex) parasitic-extraction techfile for
IHP SG13G2: the electrical layers and their GDS pairs, the KLayout-LVS computed layers, the process stack (z,
thickness, dielectric k) and the resistance and capacitance coefficients. The data is carried over from gf-pex
`gfpexconfg/ihp_sg13g2.py`, which derives from the KPEX (klayout-pex) SG13G2 definition and the IHP-Open-PDK Magic
tech file. Departures from that source: the MiM top plate (`MIM`, 36/0) and its via to TopMetal1 (`Vmim`, 129/0) are
drawing layers that the `cmim_top` and `mim_via` computed layers map to, and the thick-oxide Activ overlap and
side-overlap entries are dropped (gfpex can't tell them from LV Activ, and they overwrote the LV values). The
`ildtm1` dielectric the source repeats after each Metal5 variant is named `ildtm1`, `ildtm1_cap` and `ildtm1_cmim`,
so stack names are unique.

## Installation

gfpex is an optional dependency, the `pex` extra (gf-pex `dev/diogo-main`):

```bash
uv sync --extra dev --extra pex
```

gfpex is private: installing it needs read access to `doplaydo/gf-pex`, git authenticated for github.com
(for example `gh auth login && gh auth setup-git`) and a Rust toolchain to build it.

The `pex` and `simulation` extras are mutually exclusive: gfpex needs protobuf >= 7 (git kfnetlist) and gsim needs
protobuf < 5 (vlsir).

## Usage

```python
from ihp.pex.rules import DEFAULT_PEX_RULES_CONFIG  # a gfpex.gfpex.Techfile
```

## Provenance tags

| Tag | Meaning |
|---|---|
| `FOUNDRY <source>` | value stated by a foundry document |
| `DERIVED <formula>` | computed from foundry values |
| `ASSUMED <source>` | borrowed from the closest open PDK or literature |
| `PALACE-FIT` | fitted with gf-pex `benchmarks/palace_benchmark.py` |

In this file the stack is FOUNDRY (SG13G2 process spec, page 5), the z coordinates are DERIVED from it, and the
parasitic coefficients are FOUNDRY (IHP-Open-PDK Magic tech file).

Palace-fit values (fringe, sidewall, side-overlap) are pending.

## Running the tests

```bash
make test-pex
```

The tests skip when gfpex is not installed (`pytest.importorskip("gfpex.gfpex")`). The `Test PEX rules with gfpex`
workflow runs them on demand and needs the `GFPEX_TOKEN` secret.
