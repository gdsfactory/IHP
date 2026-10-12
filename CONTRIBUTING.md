# Contributing to IHP GDSFactory PDK

The IHP GDSFactory PDK is a Python-based Process Design Kit for the [IHP SG13G2](https://github.com/IHP-GmbH/IHP-Open-PDK) 130nm BiCMOS open-source technology. Built on top of [GDSFactory](https://gdsfactory.github.io/gdsfactory/), it provides fully parametric layout cells (transistors, resistors, capacitors, inductors, diodes, and more), design rule constants, SAX-compatible simulation models, and VLSIR/SPICE netlist export — everything needed to generate tape-out-ready GDSII from Python.

The PDK targets a real foundry process with SiGe HBTs, standard and high-voltage MOSFETs, RF devices, MIM/MOM capacitors, spiral inductors, and various passives. Contributions that improve cell accuracy, expand device coverage, add simulation models, or improve documentation are all welcome.

This guide covers everything you need to get started.

## Getting started

### Prerequisites

- Python 3.11, 3.12, or 3.13
- [uv](https://docs.astral.sh/uv/) package manager (recommended)
- [KLayout](https://www.klayout.de/) for viewing generated GDS files
- Git

### Development setup

```bash
git clone https://github.com/gdsfactory/ihp.git
cd ihp
uv venv --python 3.12
uv sync --extra docs --extra dev --extra simulation
python install_tech.py
```

Install the pre-commit hooks:

```bash
pre-commit install
```

Verify everything works:

```bash
make test
```

## Project structure

```
ihp/
├── cells/          # Pure GDSFactory parametric layout cells (@gf.cell functions)
├── models/         # SAX S-parameter models and VLSIR bridge
├── gds/            # Pre-built GDS files for complex cells
├── tech.py         # Layer map, design rules, layer stack, cross-sections
├── layers.yaml     # Layer definitions
└── config.py       # Paths and PDK configuration
tests/
├── test_cells.py           # GDS regression & settings tests
├── test_port_layers.py     # Port layer verification
└── gds_ref/                # Golden reference GDS files
docs/               # Jupyter Book documentation
```

### Key conventions

- **`cells/`** contains the actively developed pure-Python parametric cells. Each cell is a function decorated with `@gf.cell` that builds geometry using `add_polygon` and design rule constants from `tech.py`.
- Design rule constants live in `tech.py` (the `TechIHP` Pydantic model and `LayerMapIHP` class).

## Making changes

### Workflow

1. Fork the repository and create a feature branch from `main`.
2. Make your changes (see guidelines below).
3. Run the pre-commit hooks and tests.
4. Push your branch and open a pull request against `main`.

### Adding or modifying a cell

1. Implement the cell function in the appropriate file under `ihp/cells/` (e.g., `fet_transistors.py`, `resistors.py`).
2. Decorate it with `@gf.cell` and document it with a Google-style docstring.
3. Export it from `ihp/cells/__init__.py` if it is a new cell.
4. Add or update tests in `tests/test_cells.py`.
5. Regenerate golden reference GDS files if needed: `make test-force`.

### Adding a simulation model

Add SAX-compatible models to `ihp/models/` and export them from `ihp/models/__init__.py`.

## Code style

Code formatting and linting are enforced automatically by pre-commit hooks. The key tools are:

| Tool | Purpose |
|---|---|
| **Ruff** | Linting (pycodestyle, pyflakes, isort, bugbear, comprehensions) and formatting |
| **Codespell** | Spell checking |
| **nbstripout** | Strips output from Jupyter notebooks |
| **yamlfmt** | YAML formatting |
| **actionlint** | GitHub Actions validation |

### Rules

- **Docstrings:** Google style (`Args:`, `Returns:`, etc.).
- **Type hints:** Use modern Python syntax (`list[...]`, not `List[...]`). Strict mypy is enabled.
- **Naming:** snake_case for cell functions and parameters. CamelCase for layer specs.
- **Imports:** Relative imports within the package (`from ..tech import TECH`). Star imports are only permitted in `__init__.py` aggregation files.
- **Geometry:** Use `add_polygon()` directly instead of sub-cell references where possible (avoids rounding issues). Use `_grid_fix()` for manufacturing grid alignment.

### Running the checks manually

```bash
pre-commit run --all-files    # run all hooks
uv run ruff check .           # lint only
uv run ruff format .          # format only
```

**You must run `pre-commit run --all-files` before every commit.** All hooks must pass.

## Testing

```bash
make test              # run the full test suite
make test-force        # run tests and regenerate reference GDS files
```

To run specific subsets:

```bash
uv run pytest tests/test_cells.py -v            # GDS regression + settings
uv run pytest tests/test_port_layers.py -v       # port layer checks
```

### What the tests cover

- **GDS regression tests** compare generated layouts against golden reference files in `tests/gds_ref/`. If your change intentionally modifies a cell's geometry, regenerate the references with `make test-force` and include the updated `.gds` files in your PR.
- **Port layer tests** ensure ports use the correct pin sublayers and `port_type="electrical"`.

## Changelog

This project uses [towncrier](https://towncrier.readthedocs.io/) to manage changelog entries. When your PR makes a user-visible change, add a fragment file to `.changelog.d/`:

```bash
# Format: <PR-number>.<type>.md
# Types: added, changed, deprecated, removed, fixed, security
echo "Short description of the change." > .changelog.d/123.added.md
```

For example, if your PR number is `#105` and you added a new cell:

```bash
echo "New \`my_cell\` parametric layout cell." > .changelog.d/105.added.md
```

The changelog is compiled automatically at release time via `towncrier build`.

## Building documentation

```bash
make docs          # build the Jupyter Book docs
make docs-serve    # build and serve locally at http://localhost:8000
```

Documentation source lives in `docs/` and uses Jupyter Book (Sphinx). Cell reference pages are auto-generated from docstrings by `.github/write_cells.py`.

## Useful Makefile targets

| Target | Description |
|---|---|
| `make install` | Install all dependencies (docs + dev + simulation) |
| `make test` | Run the full pytest suite |
| `make test-force` | Run tests and regenerate reference GDS files |
| `make tech` | Run `install_tech.py` (installs KLayout technology) |
| `make docs` | Build documentation |
| `make docs-serve` | Build and serve docs locally on port 8000 |
| `make update-pre` | Update pre-commit hook versions |
| `make build` | Build wheel and sdist |

## Pull request guidelines

- Keep PRs focused on a single concern.
- Include a changelog fragment in `.changelog.d/` for user-visible changes.
- All CI checks must pass (pre-commit hooks + pytest).
- If you modify cell geometry, include updated golden reference GDS files.
- Link to any relevant issues in the PR description.

## License

By contributing, you agree that your contributions will be licensed under the [Apache 2.0 License](LICENSE).
