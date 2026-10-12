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
import re
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
from ihp.cells.inductors import inductor2_schematic
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
    inductor2_schematic,
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
    for name in ("sg13g2_moslv_mod.lib", "sg13g2_moshv_mod.lib"):
        assert "parameters swsoa=0" in (VACASK_MODELS / name).read_text()
    for rel in VA_LOADS:
        assert f'load "{rel}"' in common, f"common file missing load of {rel}"
        assert (VACASK_MODELS / rel).resolve().is_file(), f"missing VA source {rel}"


def test_common_lib_is_safe_to_include_repeatedly() -> None:
    # Every converted lib includes the common file, so one netlist reads it many
    # times. VACASK accepts a repeated load but not a repeated parameters/model.
    for line in COMMON_LIB.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        assert stripped.startswith("load "), f"common file has non-load line: {line}"


@pytest.mark.parametrize(
    "lib", sorted(VACASK_MODELS.glob("*.lib")), ids=lambda p: p.name
)
def test_lib_defines_the_default_models_it_uses(lib: Path) -> None:
    text = lib.read_text()
    assert "sg13g2_default_mod_" not in text, "shared default model name"
    defined = set(re.findall(r"^model (\w+_default_mod_\w+) ", text, re.MULTILINE))
    used = set(re.findall(r"\b(\w+_default_mod_\w+)\b", text))
    assert used <= defined, f"used but not defined here: {sorted(used - defined)}"
    for name in defined:
        assert name.startswith(f"{lib.stem}_default_mod_"), f"{name} is not per-lib"


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
    corner = VACASK_MODELS / "cornerRES.lib"
    assert corner.is_file()

    _run_vacask_op(
        "rsil_op",
        f"""rsil operating point smoke test

model vsource vsource

include "{corner}" section=res_typ

ground 0
v1 (1 0) vsource dc=1.0
xr (1 0 0) rsil w=1e-6 l=1e-6

control
  analysis op1 op
endc
""",
    )


def test_several_libs_in_one_deck_solve_via_vacask() -> None:
    """A circuit using several device families includes the common file once
    per lib (and twice through ``cornerCAP``); it must still parse and solve.
    """
    _run_vacask_op(
        "mixed_op",
        f"""mixed libs operating point smoke test

model vsource vsource

include "{VACASK_MODELS / "cornerCAP.lib"}" section=cap_typ
include "{VACASK_MODELS / "cornerRES.lib"}" section=res_typ
include "{VACASK_MODELS / "cornerMOSlv.lib"}" section=mos_tt
include "{VACASK_MODELS / "sg13g2_esd.lib"}"
include "{VACASK_MODELS / "ihp_inductor_rl.lib"}"

ground 0
v1 (1 0) vsource dc=1.2
xc (1 0) cap_cmim w=10e-6 l=10e-6
xr (1 2 0) rsil w=1e-6 l=1e-6
xm (2 2 0 0) sg13_lv_nmos w=1e-6 l=0.13e-6
xd (1 2 0) diodevss_2kv
xl (1 3) ihp_inductor_rl inductance=1e-9 resistance=5
xcl (3 0) cap_cmim w=10e-6 l=10e-6

control
  analysis op1 op
endc
""",
    )


def _run_vacask_op(name: str, deck: str) -> None:
    """Run an operating-point deck through vacask-bin and assert it solved."""
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

    env = {**os.environ, "SIM_OPENVAF": openvaf}
    with tempfile.TemporaryDirectory() as tmp:
        sim_path = Path(tmp) / f"{name}.sim"
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


def test_generated_common_definitions_are_repeatable(tmp_path, monkeypatch):
    """Mixed/HV libraries must not redeclare shared parameters or model names."""
    import importlib.util
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    monkeypatch.setenv("VACASK_DIR", str(tmp_path))
    monkeypatch.setenv("PDK_ROOT", str(tmp_path))
    spec = importlib.util.spec_from_file_location(
        "converter", root / "scripts/convert_vacask_models.py"
    )
    converter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(converter)
    for stem in ["first", "second"]:
        (tmp_path / f"{stem}.lib").write_text(
            'include "sg13g2_vacask_common.lib"\n'
            f"subckt {stem}(p n)\nmodel rm psp103va swsoa=swsoa\n"
            "r1 (p n) sg13g2_default_mod_r r=1k\nends\n"
        )
    converter.localize_common_definitions(tmp_path, [("r", "sp_resistor")])
    first = (tmp_path / "first.lib").read_text()
    second = (tmp_path / "second.lib").read_text()
    assert "model first_default_mod_r sp_resistor" in first
    assert "model second_default_mod_r sp_resistor" in second
    assert "parameters swsoa=0" in first
    converter.localize_common_definitions(tmp_path, [("r", "sp_resistor")])
    assert (tmp_path / "first.lib").read_text() == first
