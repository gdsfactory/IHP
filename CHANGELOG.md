# [Changelog](https://keepachangelog.com/en/1.0.0/)
## [Unreleased](https://github.com/gdsfactory/ihp/compare/v2.0.1...main)

<!-- towncrier release notes start -->

## [2.0.1](https://github.com/gdsfactory/ihp/releases/tag/v2.0.1) - 2026-10-18


### Added

- SG13G2 standard-cell library with ports. [#215](https://github.com/gdsfactory/IHP/pull/215)
- Logical electrical pins across PCells for SPICE export, without adding pin geometry. [#230](https://github.com/gdsfactory/IHP/pull/230)
- Schema-backed SG13G2 RF material cards with composition metadata, layer-specific electrical properties, and source provenance. [#254](https://github.com/gdsfactory/IHP/pull/254)
- Bundled sample projects in the published wheel for GDSFactory+ project scaffolding. [#221](https://github.com/gdsfactory/IHP/pull/221)
- Documentation with 3D component views, Palace simulation notebooks, SPICE converter examples, and an LNA notebook. [#206](https://github.com/gdsfactory/IHP/pull/206), [#207](https://github.com/gdsfactory/IHP/pull/207), [#209](https://github.com/gdsfactory/IHP/pull/209), [#210](https://github.com/gdsfactory/IHP/pull/210)
- ESD protection diode cells `diodevdd_2kv`, `diodevdd_4kv`, `diodevss_2kv` and `diodevss_4kv` (imported from the PDK GDS, with `VDD`/`PAD`/`VSS` ports placed from the pin labels) and NgSpice/VACASK schematic models with an `m` multiplier.
- `cmim` takes an `m` multiplier (number of parallel devices) that is passed to the NgSpice and VACASK netlists.
- `inductor2` has a schematic and a series R-L netlist model (`ihp_inductor_rl`, NgSpice and VACASK) that matches the SAX `inductor_with_loss` model. The PDK ships no compact inductor model.


### Changed

- Split the MIM layer stack into separate dielectric and metal levels, with corresponding Vmim placement updates. [#225](https://github.com/gdsfactory/IHP/pull/225)
- Require Python 3.12 (`>=3.12,<3.13`). [#209](https://github.com/gdsfactory/IHP/pull/209)
- Update dependencies to `gdsfactory~=9.51.0` and `pdk-schema~=0.3.0`, and align the bundled sample project's GDSFactory requirement. [#276](https://github.com/gdsfactory/IHP/pull/276), [#277](https://github.com/gdsfactory/IHP/pull/277)
- Require `gsim~=0.7` for simulation in both the root package and bundled sample project. [#277](https://github.com/gdsfactory/IHP/pull/277)


### Fixed

- Correct CPW port orientation and add lateral air padding in the Palace documentation examples. [#276](https://github.com/gdsfactory/IHP/pull/276)
- Cells whose ports don't match a built-in GDSFactory+ editor symbol (`cmim`, `rfcmim`, `rsil`, `rppd`, `rhigh`, `npn13G2*`, `dantenna`, `dpantenna`, `esd_nmos`) no longer set `symbol`. Before, the editor wrote nets under the symbol's pin names and the netlist was missing pins. A new test checks that symbols and cell pins match.
- SAX `inductor3` and `cmim` models now default to the same geometry as their PCells (`inductor3`: 221.5 pH / 1.386 Ohm instead of the `inductor2` values; `cmim`: 6x6 um instead of 7x7 um). The model regression test now sweeps frequency instead of wavelength, so it actually runs.
- VACASK decks that use more than one device library now load. `sg13g2_vacask_common.lib` now holds only `load` statements, because VACASK rejects a repeated `parameters` or `model` statement. Each converted lib defines its own default primitive models, and `swsoa` is inlined as `0`. `scripts/convert_vacask_models.py` applies these changes and gains a `--postprocess-only` mode.

## [2.0.0](https://github.com/gdsfactory/ihp/releases/tag/v2.0.0) - 2026-07-04

### Removed

- `ihp.cells2` — CNI-based PyCell reference implementations removed. Use `ihp.cells` pure-Python parametric cells.
- `ihp.cells_fixed` — deprecated fixed-GDS wrapper cells removed. Equivalent parametric cells exist in `ihp.cells`.
- `cni` — CNI runtime package removed (was only required by `cells2`).
- `test_xor_transistors.py` — XOR regression tests against `cells2` removed.
- `CuPillarPad_fixed` renamed to `CuPillarPad` and moved to `ihp.cells.bondpads`.

### Changed

- `add_pads_top` default pad changed from `CuPillarPad_fixed` to `CuPillarPad`.


## [0.3.0](https://github.com/gdsfactory/ihp/releases/tag/v0.3.0) - 2026-06-26

No significant changes.


## [0.2.8](https://github.com/gdsfactory/ihp/releases/tag/v0.2.8) - 2026-04-19


### Added

- SAX frequency-domain models for resistors (rsil, rppd, rhigh), capacitors (cmim, rfcmim, cmom), and inductors (inductor2, inductor3). [#105](https://github.com/gdsfactory/ihp/issues/105)

## [0.2.0](https://github.com/gdsfactory/ihp/releases/tag/v0.2.0) - 2026-02-15

### Deprecated

- Fixed-GDS cells (`*_fixed`) are now deprecated in favour of the equivalent pure-Python parametric cells. They remain available but will be removed in a future release.

### Added

- Pure GDSFactory RF-MOSFETs (`nfet_rf`, `pfet_rf`) with full layout generation, split from the transistors module [#90](https://github.com/gdsfactory/ihp/pull/90)
- `TechIHP` Pydantic model centralizing all FET + RF geometry design-rule constants [#90](https://github.com/gdsfactory/ihp/pull/90)
- `cells2` PyCell reference page in documentation, documenting the CNI-ported reference implementations
- Technology page (`docs/tech.rst`) documenting `ihp.tech`: layer map, layer stack, design rules, cross-sections, and routing strategies
- 5 GHz up-converter mixer demo (`mixer5ghz`) added to documentation
- Palace EM simulation notebooks added to docs [#80](https://github.com/gdsfactory/ihp/pull/80)
- Scheme-to-YAML tools and source netlist converter [#87](https://github.com/gdsfactory/ihp/pull/87)
- SPICE-to-YAML converter module with examples [#84](https://github.com/gdsfactory/ihp/pull/84)
- 160 GHz LNA design example [#71](https://github.com/gdsfactory/ihp/pull/71)
- Port overlap test [#94](https://github.com/gdsfactory/ihp/pull/94)
- `make docs-clean` and `make docs-serve` targets for local doc previewing

### Changed

- Documentation restructured: "PDK Reference" section with separate pages for parametric cells, deprecated fixed cells, and cells2 reference
- Documentation generation script now produces three RST pages instead of one

### Fixed

- Port layers now use pin sublayers with `port_type="electrical"` across all cells [#94](https://github.com/gdsfactory/ihp/pull/94)
- Double `_fixed_fixed` naming bug on `cmim_fixed` and `inductor2_fixed`
- MOSFET layout improved and fuzzed against PyCell reference [#88](https://github.com/gdsfactory/ihp/pull/88)
- `import_gds` (`functools.partial`) no longer leaks into the cell catalog documentation

### Removed

- Obsolete `bipolar.py` and `transistors.py` shims

## [0.1.5](https://github.com/gdsfactory/ihp/releases/tag/v0.1.5) - 2026-01-24

No significant changes.


## [0.1.0](https://github.com/gdsfactory/ihp/releases/tag/v0.1.0) - 2025-11-21

- add cni [#45](https://github.com/gdsfactory/ihp/pull/45)
- fix tests2 [#43](https://github.com/gdsfactory/ihp/pull/43)
- add reference pycells from ihp [#42](https://github.com/gdsfactory/ihp/pull/42)
- improve resistors [#29](https://github.com/gdsfactory/ihp/pull/29)
- add tests [#5](https://github.com/gdsfactory/ihp/pull/5)
- fix tests2 [#43](https://github.com/gdsfactory/ihp/pull/43)
- fix tests [#36](https://github.com/gdsfactory/ihp/pull/36)
- fix stack [#31](https://github.com/gdsfactory/ihp/pull/31)
- fix inductors [#28](https://github.com/gdsfactory/ihp/pull/28)
- fix bumps [#22](https://github.com/gdsfactory/ihp/pull/22)
- Resistor bug fix + bondpad fix  [#41](https://github.com/gdsfactory/ihp/pull/41)
- Fixing resistors [#39](https://github.com/gdsfactory/ihp/pull/39)
- Adding inductor  [#35](https://github.com/gdsfactory/ihp/pull/35)
- Fix inductor [#24](https://github.com/gdsfactory/ihp/pull/24)


## [0.0.6](https://github.com/gdsfactory/ihp/releases/tag/v0.0.6) - 2025-09-14

- first release
