# PEX with gfpex — IHP SG13G2

`ihp/pex/rules.py` holds the default [gfpex](https://github.com/doplaydo/gf-pex) parasitic-extraction techfile for
IHP SG13G2: the electrical layers and their GDS pairs, the KLayout-LVS computed layers, the process stack (z,
thickness, dielectric k) and the resistance and capacitance coefficients. The data is carried over unchanged from
gf-pex `gfpexconfg/ihp_sg13g2.py`, which derives from the KPEX (klayout-pex) SG13G2 definition and the IHP-Open-PDK
Magic tech file.

## Installation

gfpex is optional and not a dependency of this package:

```bash
uv pip install networkx "kfnetlist @ git+https://github.com/gdsfactory/kfnetlist" \
  "gfpex @ git+https://github.com/doplaydo/gf-pex@dev/diogo-main"
```

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

The tests skip when gfpex is not installed. The `Test PEX rules with gfpex` workflow runs them on demand and needs
the `GFPEX_TOKEN` secret.
