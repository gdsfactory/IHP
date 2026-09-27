"""Nominal SG13G2 RF materials from the public, IHP-linked Palace stack.

These are effective EM model values, not bulk elemental constants or a
broadband/temperature qualification. No optical models are supplied.
"""

from pdk_schema import MaterialCard, Permittivity, Provenance, Regime, ScalarValue

IHP_REVISION = "5e6d592e4002946a4616f798c357f0f3c06cf3b6"
EM_REVISION = "df29aa608be858f53fbce46f81238b5534812d9b"
EM_SOURCE_URL = (
    "https://github.com/VolkerMuehlhaus/gds2palace_ihp_sg13g2/blob/"
    f"{EM_REVISION}/workflow/SG13G2_200um.xml"
)
IHP_SOURCE_URL = (
    f"https://github.com/IHP-GmbH/IHP-Open-PDK/tree/{IHP_REVISION}"
    "/ihp-sg13g2/libs.tech/palace"
)
PROCESS_SPEC_URL = (
    f"https://github.com/IHP-GmbH/IHP-Open-PDK/blob/{IHP_REVISION}"
    "/ihp-sg13g2/libs.doc/doc/SG13G2_os_process_spec.pdf"
)


def _card(
    name: str,
    source_material: str,
    conductivity: float,
    permittivity: float | None = None,
) -> MaterialCard:
    """Transcribe one constant material from the pinned EM stack."""
    sigma = ScalarValue(value=conductivity, unit="S/m")
    model = (
        None
        if permittivity is None
        else Permittivity(
            eps_real=ScalarValue(value=permittivity, unit=""),
            eps_imag=None,
            conductivity=sigma,
            validity=None,
            variation=None,
        )
    )
    return MaterialCard(
        name=name,
        optical=None,
        rf=Regime(
            temperature_ref=None,
            provenance=Provenance(
                source="literature",
                label="IHP-linked SG13G2 Palace EM stack",
                maturity=None,
                citations=[],
                comment=(
                    "Nominal effective EM parameters transcribed from the public "
                    "Palace workflow linked by IHP-Open-PDK. The source assumes "
                    "constant conductivity and zero dielectric loss tangent; "
                    "it does not specify temperature or a validity band."
                ),
                url=IHP_SOURCE_URL,
                data_url=EM_SOURCE_URL,
                info={
                    "ihp_revision": IHP_REVISION,
                    "em_revision": EM_REVISION,
                    "source_material": source_material,
                    "process_spec_url": PROCESS_SPEC_URL,
                },
            ),
            permittivity=model,
            conductivity=sigma if model is None else None,
            permeability=None,
            perturbations=[],
            info={"model": "constant RF effective material"},
        ),
        info={"process": "SG13G2", "source_material": source_material},
    )


# Keep the published rounding. Metal values agree with sigma=1/(Rs*t)
# using nominal sheet resistance and thickness (process spec §§2.13, 2.16).
# Via/contact values are effective plug parameters, not bulk tungsten.
_CONDUCTORS = {
    "metal1": ("Metal1", 21_640_000.0),
    "metal2": ("Metal2", 23_190_000.0),
    "metal3": ("Metal3", 23_190_000.0),
    "metal4": ("Metal4", 23_190_000.0),
    "metal5": ("Metal5", 23_190_000.0),
    "topmetal1": ("TopMetal1", 27_800_000.0),
    "topmetal2": ("TopMetal2", 30_300_000.0),
    "cont": ("Cont", 2_390_000.0),
    "via1": ("Via1", 1_660_000.0),
    "via2": ("Via2", 1_660_000.0),
    "via3": ("Via3", 1_660_000.0),
    "via4": ("Via4", 1_660_000.0),
    "topvia1": ("TopVia1", 2_191_000.0),
    "topvia2": ("TopVia2", 3_143_000.0),
    "vmim": ("Vmim", 2_191_000.0),
    "mim": ("MIM", 500_000.0),
}

MATERIAL_CARDS: dict[str, MaterialCard] = {
    f"sg13g2_{layer}": _card(f"sg13g2_{layer}", source, sigma)
    for layer, (source, sigma) in _CONDUCTORS.items()
}
MATERIAL_CARDS.update(
    {
        "sio2": _card("sio2", "SiO2", 0.0, 4.1),
        # Palace's legacy synthesized substrate uses the token 'silicon'.
        # This is bulk substrate data, not a model for wells or implants.
        "silicon": _card("silicon", "Substrate", 2.0, 11.9),
        "sg13g2_epi": _card("sg13g2_epi", "EPI", 5.0, 11.9),
        "sg13g2_passivation": _card("sg13g2_passivation", "Passive", 0.0, 6.6),
        "air": _card("air", "AIR", 0.0, 1.0),
    }
)

__all__ = ["MATERIAL_CARDS"]
