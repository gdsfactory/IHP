# RF material cards

`ihp.PDK.material_cards` (also exported as `ihp.MATERIAL_CARDS`) contains
`pdk_schema.MaterialCard` objects for SG13G2 RF simulation. The layer stack uses
distinct `sg13g2_*` tokens for Metal1–5, TopMetal1–2, contacts, vias, and the MIM
top electrode. Consumers must resolve these tokens through the PDK cards.

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
to the specified 50 ohm cm resistivity. Air is also provided. Separate EPI
(11.9, 5 S/m) and passivation (6.6, 0 S/m) cards are available for explicitly
constructed stacks; they do not add or change regions in the current layer stack.

These are constant, nominal RF models. The source assumes zero dielectric loss
tangent and supplies no frequency validity band or temperature dependence.
They are not optical models or a foundry qualification of broadband accuracy.
FEOL wells, implants, polysilicon, and heater materials are not assigned these
cards. The existing combined passivation and MIM dielectric geometry/material
approximations also remain unchanged; do not substitute the bulk substrate card
for doped device regions.
