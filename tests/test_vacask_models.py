"""Validate the VACASK model metadata, the on-the-fly common include, and that
the shipped models actually compile + solve via ``vacask-bin``.

These tests are independent of the Mosaic netlister selector (which has a bug
that drops ``language="spectre"`` entries -- see ``test_vacask_op.py``). They
verify the per-cell dual NgSpice/VACASK entries, the generated common file, the
absence of committed ``.osdi``, and -- end to end -- that a converted ``.lib``
drives an operating-point solve with the Verilog-A sources compiled on the fly.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from ihp.cells.antennas import dantenna_schematic
from ihp.cells.bjt_transistors import npn13G2_schematic
from ihp.cells.bondpads import bondpad_schematic
from ihp.cells.capacitors import cmim_schematic
from ihp.cells.fet_transistors import nmos_schematic
from ihp.cells.passives import svaricap_schematic
from ihp.cells.resistors import rsil_schematic
from ihp.cells.rf_transistors import rfnmos_schematic

ROOT = Path(__file__).resolve().parents[1]
VACASK_MODELS = ROOT / "ihp" / "models" / "vacask" / "models"
COMMON_LIB = VACASK_MODELS / "sg13g2_vacask_common.lib"

# Verilog-A sources the common file compiles on the fly (relative to the
# converted-lib directory), per scripts/convert_vacask_models.py.
VA_LOADS = [
    "../../ngspice/va/psp103/psp103.va",
    "../../ngspice/va/psp103/psp103_nqs.va",
    "../../ngspice/va/r3_cmc/r3_cmc.va",
    "../../ngspice/va/mosvar/mosvar.va",
]

REPRESENTATIVE_FACTORIES = [
    rsil_schematic,
    nmos_schematic,
    npn13G2_schematic,
    cmim_schematic,
    dantenna_schematic,
    bondpad_schematic,
    rfnmos_schematic,
    svaricap_schematic,
]


@pytest.mark.parametrize(
    "schematic_factory",
    REPRESENTATIVE_FACTORIES,
    ids=lambda f: f.__name__,
)
def test_schematic_has_matching_ngspice_and_vacask_entries(schematic_factory) -> None:
    models = schematic_factory().info["models"]

    ngspice = [m for m in models if m["implementation"] == "NgSpice"]
    vacask = [m for m in models if m["implementation"] == "VACASK"]
    assert len(ngspice) == 1, "expected exactly one NgSpice entry"
    assert len(vacask) == 1, "expected exactly one VACASK entry"

    ng, vc = ngspice[0], vacask[0]
    assert ng["language"] == "spice"
    assert vc["language"] == "spectre"

    # The two entries describe the same device, only the backend differs.
    for key in ("name", "spice_type", "port_order", "params", "sections"):
        assert vc[key] == ng[key], f"{key} differs between NgSpice and VACASK"

    assert ng["library"].startswith("ihp/models/ngspice/models/")
    assert vc["library"] == ng["library"].replace(
        "ihp/models/ngspice/models/", "ihp/models/vacask/models/", 1
    )

    # The VACASK library file must actually be shipped.
    assert (ROOT / vc["library"]).is_file(), f"missing {vc['library']}"


def test_common_lib_loads_existing_verilog_a_sources() -> None:
    common = COMMON_LIB.read_text()
    assert "parameters swsoa=0" in common
    for rel in VA_LOADS:
        assert f'load "{rel}"' in common, f"common file missing load of {rel}"
        assert (VACASK_MODELS / rel).resolve().is_file(), f"missing VA source {rel}"


def test_no_committed_osdi_under_vacask() -> None:
    # .osdi are compiled at runtime and must never be committed.
    assert not list((ROOT / "ihp" / "models" / "vacask").rglob("*.osdi"))


def _working_openvaf() -> str | None:
    """Return a path to an openvaf-r that actually runs, or None.

    Prefers ``$SIM_OPENVAF``, then vacask-bin's bundled compiler, then any
    ``openvaf-r`` on PATH. The bundled binary can fail to load on systems whose
    ICU major version differs from what it was linked against (see the InSpice
    vacask-bin packaging issue), so we probe each candidate by executing it.
    """
    import vacask_bin

    candidates = [
        os.environ.get("SIM_OPENVAF"),
        vacask_bin.OPENVAF_CMD,
        shutil.which("openvaf-r"),
    ]
    for cand in candidates:
        if not cand or not os.path.exists(cand):
            continue
        try:
            proc = subprocess.run([cand, "--version"], capture_output=True, timeout=60)
        except OSError:
            continue
        if proc.returncode == 0:
            return cand
    return None


def test_converted_lib_compiles_and_solves_via_vacask() -> None:
    """Selector-independent end-to-end proof.

    Builds a tiny VACASK deck that includes a converted corner ``.lib`` section
    and runs an operating-point analysis. This exercises the whole shipped
    chain: section -> ``include "..._mod.lib"`` -> ``include common`` ->
    ``load "../../ngspice/va/..."`` (Verilog-A compiled on the fly to ``.osdi``)
    -> solve. It does NOT go through the Mosaic netlister, so it is unaffected
    by the selector bug.
    """
    vacask_bin = pytest.importorskip("vacask_bin")
    vacask_cmd = vacask_bin.VACASK_CMD
    if not os.path.exists(vacask_cmd):
        pytest.skip("vacask binary not available")

    openvaf = _working_openvaf()
    if openvaf is None:
        pytest.skip(
            "no working openvaf-r available (bundled vacask-bin compiler cannot "
            "run on this system, e.g. ICU major-version mismatch); set "
            "SIM_OPENVAF to a working openvaf-r to enable this test"
        )

    corner = VACASK_MODELS / "cornerRES.lib"
    assert corner.is_file()

    deck = f"""rsil operating point smoke test

model vsource vsource

include "{corner}" section=res_typ

ground 0
v1 (1 0) vsource dc=1.0
xr (1 0 0) rsil w=1e-6 l=1e-6

control
  analysis op1 op
endc
"""

    env = {**os.environ, "SIM_OPENVAF": openvaf}
    with tempfile.TemporaryDirectory() as tmp:
        sim_path = Path(tmp) / "rsil_op.sim"
        sim_path.write_text(deck)
        # cwd is a writable temp dir: vacask writes the compiled .osdi here, not
        # into the (possibly read-only) installed package.
        proc = subprocess.run(
            [vacask_cmd, str(sim_path)],
            cwd=tmp,
            env=env,
            capture_output=True,
            text=True,
            timeout=600,
        )

    output = proc.stdout + proc.stderr
    assert proc.returncode == 0, f"vacask failed:\n{output}"
    assert "Running analysis 'op1'" in output, output
    assert "error while loading shared libraries" not in output
    assert "Failed to compile" not in output
