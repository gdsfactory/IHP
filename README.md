# IHP GDSFactory PDK

IHP's SG13G2 is an open-source 130nm SiGe BiCMOS technology for RF/mmWave electronics.

<!-- BADGES:START -->
[![Docs](https://github.com/gdsfactory/ihp/actions/workflows/pages.yml/badge.svg)](https://github.com/gdsfactory/ihp/actions/workflows/pages.yml)
[![Tests](https://github.com/gdsfactory/ihp/actions/workflows/test_code.yml/badge.svg)](https://github.com/gdsfactory/ihp/actions/workflows/test_code.yml)
[![DRC](https://github.com/gdsfactory/ihp/raw/badges/drc.svg)](https://github.com/gdsfactory/ihp/actions/workflows/drc.yml)
[![Model Regression](https://github.com/gdsfactory/ihp/actions/workflows/model_regression.yml/badge.svg)](https://github.com/gdsfactory/ihp/actions/workflows/model_regression.yml)
[![Test Coverage](https://github.com/gdsfactory/ihp/raw/badges/coverage.svg)](https://github.com/gdsfactory/ihp/actions/workflows/test_coverage.yml)
[![Model Coverage](https://github.com/gdsfactory/ihp/raw/badges/model_coverage.svg)](https://github.com/gdsfactory/ihp/actions/workflows/model_coverage.svg)
[![Issues](https://github.com/gdsfactory/ihp/raw/badges/issues.svg)](https://github.com/gdsfactory/ihp/issues)
[![PRs](https://github.com/gdsfactory/ihp/raw/badges/prs.svg)](https://github.com/gdsfactory/ihp/pulls)
<!-- BADGES:END -->


[![Test code](https://github.com/gdsfactory/ihp/actions/workflows/test_code.yml/badge.svg)](https://github.com/gdsfactory/ihp/actions/workflows/test_code.yml)
[![Build docs](https://github.com/gdsfactory/ihp/actions/workflows/pages.yml/badge.svg)](https://github.com/gdsfactory/ihp/actions/workflows/pages.yml)
[![PyPI](https://img.shields.io/pypi/v/ihp-gdsfactory)](https://pypi.org/project/ihp-gdsfactory/)
[![Python](https://img.shields.io/pypi/pyversions/ihp-gdsfactory)](https://pypi.org/project/ihp-gdsfactory/)
[![License](https://img.shields.io/github/license/gdsfactory/ihp)](https://github.com/gdsfactory/ihp/blob/main/LICENSE)

A [GDSFactory](https://gdsfactory.github.io/gdsfactory/)-based Process Design Kit for the [IHP SG13G2](https://github.com/IHP-GmbH/IHP-Open-PDK) 130nm BiCMOS open-source technology. It provides parametric layout cells, design rule constants, simulation models, and example designs for tape-out-ready integrated circuits.

## Quick start

Use Python 3.11, 3.12 or 3.13. We recommend [VSCode](https://code.visualstudio.com/) as an IDE.

```
uv pip install ihp-gdsfactory --upgrade
```

Then you need to restart Klayout to make sure the new technology installed appears and start generating IHP-SG13G2 GDSII immediately!

```python
import gdsfactory as gf
from ihp import PDK
from ihp.cells import nmos, rfnmos, npn13G2, rsil, cmim

PDK.activate()

# Create a parametric NMOS transistor
c = nmos(width=1.0, length=0.13, nf=4)
c.write_gds("my_nmos.gds")
c.show()  # opens in KLayout
```

## Available devices

| Category | Device | Function |
|---|---|---|
| **FET** | nmos | `nmos` |
| | pmos | `pmos` |
| | nmos_hv | `nmos_hv` |
| | pmos_hv | `pmos_hv` |
| **RF FET** | rfnmos | `rfnmos` |
| | rfpmos | `rfpmos` |
| | rfnmos_hv | `rfnmos_hv` |
| | rfpmos_hv | `rfpmos_hv` |
| **Bipolar** | npn13G2 | `npn13G2` |
| | npn13G2L | `npn13G2L` |
| | npn13G2V | `npn13G2V` |
| | pnpMPA | `pnpMPA` |
| **Resistor** | rsil (silicided poly) | `rsil` |
| | rppd (p-poly) | `rppd` |
| | rhigh (high-R) | `rhigh` |
| **Capacitor** | cmim (MIM) | `cmim` |
| | rfcmim (RF MIM) | `rfcmim` |
| | cmom (MOM) | `cmom` |
| **Inductor** | inductor2 | `inductor2` |
| | inductor3 | `inductor3` |
| **Passive** | svaricap (MOS varicap) | `svaricap` |
| | ESD protection | `esd_nmos` |
| | ntap1 / ptap1 | `ntap1` / `ptap1` |
| | guard_ring | `guard_ring` |
| | sealring | `sealring` |
| **Diode** | diodevdd 2kV/4kV | `diodevdd_2kv` / `diodevdd_4kv` |
| | diodevss 2kV/4kV | `diodevss_2kv` / `diodevss_4kv` |
| | schottky_nbl1 | `schottky_nbl1` |
| **Antenna** | dantenna / dpantenna | `dantenna` / `dpantenna` |
| **Bondpad** | bondpad | `bondpad` |

## Project structure

```
ihp/
├── cells/                  # Pure GDSFactory parametric layout cells
│   ├── fet_transistors.py  #   NMOS/PMOS (standard & HV)
│   ├── rf_transistors.py   #   RF-MOSFETs with guard/gate rings
│   ├── bjt_transistors.py  #   SiGe HBTs (npn13G2, npn13G2L, npn13G2V, pnpMPA)
│   ├── resistors.py        #   Polysilicon & metal resistors
│   ├── capacitors.py       #   MIM & MOS capacitors
│   ├── inductors.py        #   Spiral inductors
│   ├── passives.py         #   Diodes, varactors, guard rings
│   ├── via_stacks.py       #   Via stack generators
│   └── bondpads.py         #   Bondpad cells
├── models/                 # Compact models & SAX S-parameter models
├── gds/                    # Pre-built GDS files for some cells
├── tech.py                 # Layer map, design rules, technology parameters
├── layers.yaml             # Layer properties and colors for KLayout LYP
└── config.py               # Paths and PDK configuration
tests/
├── test_cells.py           # GDS regression & settings tests for all cells
└── gds_ref/                # Golden reference GDS files
docs/                       # Documentation
```

**Key architectural concepts:**

- **`cells/`** contains pure GDSFactory implementations — each `@gf.cell` function builds geometry from scratch using `add_polygon` and design rule constants from `tech.py`. No external layout tools are needed at runtime.
- **`models/`** provides SAX-compatible S-parameter models for circuit simulation.

## Installation

We recommend `uv`

```bash
# On macOS and Linux.
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
# On Windows.
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Installation for contributors

```bash
git clone https://github.com/gdsfactory/ihp.git
cd ihp
uv venv --python 3.12
uv sync --extra docs --extra dev
python install_tech.py
```

## Running tests

```bash
make test              # run full test suite
make test-force        # run tests and regenerate reference GDS files
```

To run specific test subsets:

```bash
uv run pytest tests/test_cells.py -v          # GDS regression + settings tests
```

## Documentation

- [gdsfactory docs](https://gdsfactory.github.io/gdsfactory/)
- [IHP docs from GDSFactory](https://gdsfactory.github.io/IHP/) and [code](https://github.com/gdsfactory/ihp)
- [IHP documentation](https://ihp-open-pdk-docs.readthedocs.io/en/latest/#)
- [IHP component diagrams](https://ihp-open-pdk-docs.readthedocs.io/en/latest/verification/lvs/04_01_fets.html)

## License

[Apache 2.0](LICENSE)

## Pre-commit

Pre-commit hooks are centrally maintained in [pdk-ci-workflow-public](https://github.com/doplaydo/pdk-ci-workflow-public). `make dev` fetches the canonical config and installs the git hook.

```bash
make dev
```

## Release

1. Bump the version:

    ```bash
    tbump 0.0.1
    ```

2. Push the tag:

    ```bash
    git push --tags
    ```
    This triggers the release workflow that builds wheels and uploads them.

3. Create a pull request with the updated changelog since last release.
