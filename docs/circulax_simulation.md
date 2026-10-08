# Circulax schematic models

IHP schematic factories register Circulax models through
`ihp._schematic.circulax_model()`. Each entry contains the module and qualified
name of a shared `circulax.netlist_io.LibraryModel` in `ihp.models.circulax`.
Reading schematic metadata does not import Circulax or load native code.
Existing VACASK and NgSpice entries remain available.

The library models reuse the native NgSpice card declarations and corner sections,
using the parser's supported `ngspice` dialect. VACASK metadata remains available
for VACASK simulation; its converted library syntax is not treated as Spectre.
Factory defaults and individual schematic instance settings supply widths,
lengths, finger counts, and multiplicities. Micrometer values have explicit
`um` to `m` conversions in `LibraryModel.parameter_units`; other existing
parameter expressions stay in the library adapter. Native card coefficients
are retained in their original library files. Layout extraction is outside
this interface.

`corner` selects one of the existing metadata sections, defaulting to the first
section. Unknown corners fail rather than silently using typical values.
Wrapper cells retain their devices and connections as kfnetlist subcircuits.
Native module provisioning must cover each requested card family; successful MOS
and RF capacitor execution alone does not establish HBT parity. The native
NgSpice HBT cards use HICUM, which requires its own compatible module; the
converted VACASK cards use a different model family.
Circulax flattens those internally and shares OSDI descriptors across instances,
with individual leaf parameters forming rows of the same native device batch.
Public port aliases match IHP symbols, including `P1`/`P2` on resistors.
The metadata references those public ports without a `port_map`. The
`LibraryModel` alone maps them to native NgSpice terminals (for example,
public `D` to native `d`), so client connections retain the wrapper's public
terminal names until Circulax flattens it.

The native NgSpice bondpad subcircuit is an empty placeholder with an unconnected
`PAD` terminal. Its registration preserves categorical shape settings, but does
not provide solver support. Elaboration rejects the disconnected terminal rather
than inventing an electrical model.

The native `svaricap` wrapper contains voltage-dependent behavioral expressions
using `v(...)`. The current library evaluator rejects that function; registration
does not provide solver support for this wrapper. Registration covers the
existing modeled families, while native solver parity across every IHP device
remains unproven.

## Runtime setup

The optional `circulax` extra selects Circulax's `verilog-a` extra (bosdi), pins the NetlistParse
Python dispatcher to the same immutable revision as Circulax, and declares
vacask-bin. This integration requires the coordinated Circulax release providing
`LibraryModel.from_file`, corner selection, unit declarations, and public port
aliases; an older published Circulax version is insufficient. Until that release
is available, install the corresponding local Circulax development checkout.

Native NgSpice cards do not declare OSDI load directives. Supply compatible
modules explicitly through `IHP_CIRCULAX_OSDI_MODULES`, a path-separated list
covering the requested leaf model families. Installing the extra alone does not
provision those modules or establish ABI compatibility.

The adapter records vacask-bin's `MOD_DIR` and `OPENVAF_CMD` when available.
`IHP_CIRCULAX_MODULE_PATHS` (directories separated by the OS path separator) and
`IHP_CIRCULAX_COMPILER` override these paths. Module directories and the compiler
are options for libraries with load declarations; they do not automatically
enumerate modules for the native NgSpice cards. IHP models use the audited
`limiting_only` state policy for compact models whose state slots store Newton
limiting history rather than physical transient state. Circulax owns compilation and caching of Verilog-A sources.
OSDI modules must match the installed bosdi ABI; discovery of a module path
alone does not verify compatibility. Missing or incompatible native modules
remain simulation errors and do not prevent schematic metadata from loading.

The simulation window and its result presentation are unchanged. Model and
mixed-circuit checks can run through the SDK and Circulax compiler directly.
