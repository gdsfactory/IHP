# Cell Metadata Annotation Conventions

## Tags
- First tag is the PDK name, using official casing: `"IHP"`
- Technical terms stay lowercase even if acronyms: `"mos"`, `"lv"`, `"hv"`
- Keep tags minimal: `["IHP", "mos", "lv"]` is sufficient, no need for `"transistor"` etc.
- Example: `tags=["IHP", "mos", "lv"]`

## Ports (symbol layout)
- Use standard MOSFET symbol orientation: D top, S bottom, G left, B right
- Port names match the layout port names (uppercase for transistors): `"D"`, `"G"`, `"S"`, `"B"`
- Example: `ports={"top": ["D"], "bottom": ["S"], "left": ["G"], "right": ["B"]}`

## Models
- `library` points to the **corner file** (e.g. `cornerMOSlv.lib`), not the model file — the corner file has the `.LIB`/`.ENDL` sections and includes the model file internally
- `sections` lists the base PVT corners from the corner file (e.g. `["mos_tt", "mos_ss", "mos_ff", "mos_sf", "mos_fs"]`)
- `port_order` uses symbol port names (uppercase), matching the positional order from the `.subckt` definition
- `params` values are **string expressions** over the function's kwargs (e.g. `"width * 1e-6"`)

## Removed
- `model` parameter from function signature — was dead code (never referenced in body, vlsir dict hardcoded the name)
- `c.info["vlsir"]` block — replaced entirely by `@gf.cell()` kwargs

**Why:** Moving metadata to decorator kwargs allows gfp2-server to extract it statically via AST parsing (no Python execution needed).

**How to apply:** When converting any `@gf.cell` + `c.info["vlsir"]` pattern, follow these conventions. Study the actual spice corner files for correct `library`, `sections`, and `port_order`.
