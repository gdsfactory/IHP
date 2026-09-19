# GFLVS LVS Config Plan — IHP SG13G2

## PDK Info
- Package: `ihp`
- Classification: electronic (BiCMOS — SiGe HBT + CMOS 130nm)
- Technology: IHP SG13G2 BiCMOS process — SiGe HBTs, MOSFETs, passive components, MIM caps
- Layers file: `ihp/tech.py` (LayerMap class: `LayerMapIHP`)
- Dev branch: dev/gflvs-config

## Namespace Note
DO NOT create a `gflvs/` directory inside the package — it would shadow the
installed `gflvs` library. Use `ihp/lvs/` instead.

## Files to Create
- `ihp/lvs/__init__.py`   — re-exports (3 lines)
- `ihp/lvs/lvs.py`        — GDS_TABLE, LAYER_CONNECTIVITY, flag switches,
                             DEVICE_TEMPLATES, DEFAULT_LVS_CONFIG, run_lvs_ihp()
- `tests/gflvs/test_lvs_ihp.py` — integration test; pytest.importorskip("gflvs")
- `docs/gflvs-lvs.md`     — installation, config flags, usage example
- `Makefile`: add `test-lvs` recipe → `uv run pytest tests/gflvs/ -v`

## Layer Extraction
Read `ihp/tech.py` statically (do NOT import the PDK).
Key layers from LayerMapIHP (canonical names used by gflvs):
```python
GDS_TABLE = {
    "Activdrawing":    LayerGds(layer=1,   datatype=0),
    "Polydrawing":     LayerGds(layer=5,   datatype=0),
    "Contdrawing":     LayerGds(layer=6,   datatype=0),
    "Metal1drawing":   LayerGds(layer=8,   datatype=0),
    "Metal1label":     LayerGds(layer=8,   datatype=25),
    "Metal1pin":       LayerGds(layer=8,   datatype=2),
    "Via1drawing":     LayerGds(layer=19,  datatype=0),
    "Metal2drawing":   LayerGds(layer=10,  datatype=0),
    "Metal2label":     LayerGds(layer=10,  datatype=25),
    "Metal2pin":       LayerGds(layer=10,  datatype=2),
    "Via2drawing":     LayerGds(layer=29,  datatype=0),
    "Metal3drawing":   LayerGds(layer=30,  datatype=0),
    "Metal3label":     LayerGds(layer=30,  datatype=25),
    "Metal3pin":       LayerGds(layer=30,  datatype=2),
    "Via3drawing":     LayerGds(layer=49,  datatype=0),
    "Metal4drawing":   LayerGds(layer=50,  datatype=0),
    "Metal4label":     LayerGds(layer=50,  datatype=25),
    "Metal4pin":       LayerGds(layer=50,  datatype=2),
    "Via4drawing":     LayerGds(layer=66,  datatype=0),
    "Metal5drawing":   LayerGds(layer=67,  datatype=0),
    "Metal5label":     LayerGds(layer=67,  datatype=25),
    "Metal5pin":       LayerGds(layer=67,  datatype=2),
    "TopVia1drawing":  LayerGds(layer=125, datatype=0),
    "TopMetal1drawing":LayerGds(layer=126, datatype=0),
    "TopMetal1label":  LayerGds(layer=126, datatype=25),
    "TopMetal1pin":    LayerGds(layer=126, datatype=2),
    "TopVia2drawing":  LayerGds(layer=133, datatype=0),
    "TopMetal2drawing":LayerGds(layer=134, datatype=0),
    "TopMetal2label":  LayerGds(layer=134, datatype=25),
    "TopMetal2pin":    LayerGds(layer=134, datatype=2),
    "MIMdrawing":      LayerGds(layer=36,  datatype=0),
    "Vmimdrawing":     LayerGds(layer=129, datatype=0),
    "BasPolydrawing":  LayerGds(layer=13,  datatype=0),
}
```
(These are the verified layer numbers used in gflvs tests/conftest.py for IHP.)

## Connectivity
From the verified IHP technology configuration in gflvs:
```python
LAYER_CONNECTIVITY = {
    # pin → drawing
    "Metal1pin": ["Metal1drawing"],
    "Metal2pin": ["Metal2drawing"],
    "Metal3pin": ["Metal3drawing"],
    "Metal4pin": ["Metal4drawing"],
    "Metal5pin": ["Metal5drawing"],
    "TopMetal1pin": ["TopMetal1drawing"],
    "TopMetal2pin": ["TopMetal2drawing"],
    # substrate/gate → contact
    "Activdrawing": ["Contdrawing"],
    "Polydrawing": ["Contdrawing"],
    # contact/via → metal above
    "Contdrawing": ["Metal1drawing"],
    "Via1drawing": ["Metal2drawing"],
    "Via2drawing": ["Metal3drawing"],
    "Via3drawing": ["Metal4drawing"],
    "Via4drawing": ["Metal5drawing"],
    "TopVia1drawing": ["TopMetal1drawing"],
    "TopVia2drawing": ["TopMetal2drawing"],
    "Vmimdrawing": ["TopMetal1drawing"],
    # metal → via above
    "Metal1drawing": ["Via1drawing"],
    "Metal2drawing": ["Via2drawing"],
    "Metal3drawing": ["Via3drawing"],
    "Metal4drawing": ["Via4drawing"],
    "Metal5drawing": ["TopVia1drawing"],
    "TopMetal1drawing": ["TopVia2drawing"],
    "MIMdrawing": ["Vmimdrawing"],
}
```

## Flag Switches
```python
INCLUDE_FET         = True  # nMOS + pMOS (fet_transistors.py)
INCLUDE_BJT         = True  # npn/pnp SiGe HBTs (bjt_transistors.py)
INCLUDE_CAPACITORS  = True  # MIM caps (capacitors.py)
INCLUDE_INDUCTORS   = True  # inductors (inductors.py)
INCLUDE_RESISTORS   = True  # resistors / passives (passives.py)
INCLUDE_ANTENNAS    = True  # antenna diodes (antennas.py)
INCLUDE_BONDPADS    = True  # bondpads (bondpads.py)
```

Group templates conditionally:
```python
DEVICE_TEMPLATES: list[DeviceTemplate] = [
    *(FET_TEMPLATES if INCLUDE_FET else []),
    *(BJT_TEMPLATES if INCLUDE_BJT else []),
    *(CAPACITOR_TEMPLATES if INCLUDE_CAPACITORS else []),
    *(INDUCTOR_TEMPLATES if INCLUDE_INDUCTORS else []),
    *(RESISTOR_TEMPLATES if INCLUDE_RESISTORS else []),
    *(ANTENNA_TEMPLATES if INCLUDE_ANTENNAS else []),
    *(BONDPAD_TEMPLATES if INCLUDE_BONDPADS else []),
]
```

## Device Templates
For each PCell in `ihp/cells/`:
- `fet_transistors.py`: nMOS/pMOS — terminal from Activdrawing/Polydrawing/Metal1pin (CONFIDENCE: HIGH — verified in gflvs IHP tests)
- `bjt_transistors.py`: npn/pnp HBT — terminal from BasPolydrawing/collector/emitter (CONFIDENCE: MEDIUM)
  # TODO: verify HBT terminal layers from IHP PDK documentation
- `capacitors.py`: MIM cap — terminal from MIMdrawing + TopMetal1pin (CONFIDENCE: MEDIUM)
- `inductors.py`: spiral inductor — terminal from Metal5pin/TopMetal1pin (CONFIDENCE: MEDIUM)
- `passives.py`: resistors — terminal from Polydrawing/Metal1pin (CONFIDENCE: MEDIUM)
- `antennas.py`: antenna diodes — terminal from Activdrawing (CONFIDENCE: LOW)
  # TODO: antenna diode terminal extraction may require Activpin layer
- `bondpads.py`: bondpads — terminal from TopMetal2pin (CONFIDENCE: HIGH)

## Test Circuit (Inverter)
File: `tests/gflvs/test_lvs_ihp.py`
```python
pytest.importorskip("gflvs")
# pfet (M1, ihp PMOS, w=1.0µm, l=0.13µm, nf=1)
# nfet (M2, ihp NMOS, w=0.5µm, l=0.13µm, nf=1)
# Metal1 net connecting M1 drain to M2 drain (net "out")
# run_lvs_ihp(lib, circuit) — smoke assertion (no raise)
```

## CI Workflow
File: `.github/workflows/test_lvs.yml`
Trigger: `workflow_dispatch` only (skipped by default in CI).
```yaml
name: Test LVS (gflvs)
on:
  workflow_dispatch:
jobs:
  test-lvs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync --all-extras
      - run: uv pip install gflvs
      - run: make test-lvs
```

## Makefile Recipe
```makefile
test-lvs:
	uv run pytest tests/gflvs/ -v
```

## Verification Checklist
- [ ] `python -c "from ihp.lvs import DEFAULT_LVS_CONFIG, INCLUDE_FET"` succeeds
- [ ] Setting `INCLUDE_FET = False` removes FET templates from `DEVICE_TEMPLATES`
- [ ] Test skips cleanly when gflvs not installed (`pytest.importorskip`)
- [ ] `ruff check ihp/lvs/` passes
- [ ] Layer numbers match gflvs/tests/conftest.py IHP_TECH_GDS_TABLE
