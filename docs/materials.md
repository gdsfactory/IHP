# RF material cards

`ihp.PDK.material_cards` (also exported as `ihp.MATERIAL_CARDS`) contains
`pdk_schema.MaterialCard` objects for SG13G2 RF simulation. Known materials
appear in the card name and layer-stack key: `alcu_sg13g2_metal1`,
`tungsten_sg13g2_via1`, `silicon_sg13g2_epi`, and
`si3n4_sg13g2_passivation`, for example. `card.info` provides a readable
`display_name`, the physical `composition`, its `composition_source_url`, and
any `composition_note`.

The SG13G2 layer suffix distinguishes effective electrical models: Metal1
and TopMetal2 have the same constituent materials but different conductivities.
Consumers must resolve each key through the PDK cards; a generic bulk material
would discard these process-specific values. The schema requires `card.name`
to match its registry key.

Physical compositions come from the standard BEOL description in Section II of
the [IHP-authored SG13G2 paper](https://doi.org/10.1109/TCPMT.2022.3172502),
before its MEMS-specific process modifications:

| Regions | Physical composition |
| --- | --- |
| Metal1–5, TopMetal1–2 | Ti/TiN/AlCu/Ti/TiN, bottom to top; aluminum-copper alloy with titanium/titanium-nitride films |
| Via1–4, TopVia1–2 | Tungsten (W) with Ti/TiN liners |
| Interlayer oxide | Silicon dioxide (SiO₂), with region-specific deposition recipes |
| Passivation | 1.5 µm SiO₂ under a 0.4 µm silicon-nitride (Si₃N₄) cap |

The exact SG13G2 compositions of `Cont`, `Vmim`, and the MIM top electrode
have **not been verified in the cited sources**. Only those conductor cards
retain opaque `sg13g2_*` names, with `composition=None` and an explicit
“composition unverified” display name. This is not a claim that IHP withholds
their compositions. Intermetal-via chemistry is not automatically assigned to
FEOL contacts or MIM-specific structures.

Values are transcribed from the
[public SG13G2 Palace EM stack](https://github.com/VolkerMuehlhaus/gds2palace_ihp_sg13g2/blob/df29aa608be858f53fbce46f81238b5534812d9b/workflow/SG13G2_200um.xml),
which is pinned as a submodule in
[IHP-Open-PDK](https://github.com/IHP-GmbH/IHP-Open-PDK/tree/5e6d592e4002946a4616f798c357f0f3c06cf3b6/ihp-sg13g2/libs.tech/palace).
Each card retains both revisions and the source material name.

| Material | Conductivity (S/m) |
| --- | ---: |
| Metal1 | 21,640,000 |
| Metal2–5 | 23,190,000 |
| TopMetal1 | 27,800,000 |
| TopMetal2 | 30,300,000 |
| Contact | 2,390,000 |
| Via1–4 | 1,660,000 |
| TopVia1 / Vmim | 2,191,000 |
| TopVia2 | 3,143,000 |
| MIM electrode | 500,000 |

Metal conductivities agree, within published rounding, with `1 / (R_sheet * t)`
from the nominal sheet resistances and thicknesses in §§2.13 and 2.16 of the
[SG13G2 process specification](https://github.com/IHP-GmbH/IHP-Open-PDK/blob/5e6d592e4002946a4616f798c357f0f3c06cf3b6/ihp-sg13g2/libs.doc/doc/SG13G2_os_process_spec.pdf).
Via/contact numbers are effective EM parameters, not bulk tungsten constants.

The oxide card (`sio2`) has relative permittivity 4.1. The bulk substrate card
(`silicon`) has relative permittivity 11.9 and conductivity 2 S/m, corresponding
to the specified 50 ohm cm resistivity. Air is also provided. Separate epitaxial
silicon (`silicon_sg13g2_epi`: 11.9, 5 S/m) and silicon-nitride passivation
(`si3n4_sg13g2_passivation`: 6.6, 0 S/m) cards are available for explicitly
constructed stacks. The latter models only the XML's 0.4 µm nitride cap;
the underlying 1.5 µm oxide belongs to the XML's SiO2 region. It must not be
applied to the combined 1.9 µm passivation as though that were all nitride.
These cards do not add or change regions in the current layer stack.

These are constant, nominal RF models. The source assumes zero dielectric loss
tangent and supplies no frequency validity band or temperature dependence.
They are not optical models or a foundry qualification of broadband accuracy.
FEOL wells, implants, polysilicon, and heater materials are not assigned these
cards. The existing combined passivation and MIM dielectric geometry/material
approximations also remain unchanged; do not substitute the bulk substrate card
for doped device regions.
