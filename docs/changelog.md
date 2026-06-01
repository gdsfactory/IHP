# [Changelog](https://keepachangelog.com/en/1.0.0/)
## [Unreleased](https://github.com/gdsfactory/ihp/compare/v0.2.0...main)

<!-- towncrier release notes start -->

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
