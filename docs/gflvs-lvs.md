# LVS with gflvs — IHP SG13G2

## Installation

```bash
uv pip install gflvs
```

## Usage

```python
from ihp.lvs import DEFAULT_LVS_CONFIG, run_lvs_ihp

result = run_lvs_ihp(lib_or_component, circuit)
```

## Configuration flags

| Flag | Default | Devices |
|---|---|---|
| `INCLUDE_NPN` | `True` | npn13G2 |
| `INCLUDE_RFCMIM` | `True` | rfcmim |
| `INCLUDE_CMIM` | `True` | cmim |
| `INCLUDE_RESISTORS` | `True` | rhigh, rsil |
| `INCLUDE_VIA_CELLS` | `True` | via_stack |

## Running LVS tests

```bash
make test-lvs
```
