# TODO: move this to sample project
import gdsfactory as gf
from gdsfactory.typings import CrossSectionSpec

from ihp import cells

# from ihp import cells, LAYERS
# PDK.activate()
from ihp.tech import LayerMapIHP


@gf.cell
def palace_test_straight(
    length: float = 880,
    cross_section: CrossSectionSpec = "metal_routing",
    width: float = 15,
) -> gf.Component:
    """Returns a Straight waveguide.

    Args:
        length: straight length (um).
        cross_section: specification (CrossSection, string or dict).
        width: width of the waveguide. If None, it will use the width of the cross_section.
    """
    c = gf.Component()
    ref1 = c << gf.c.straight(
        length=length, cross_section=cross_section, width=width, npoints=2
    )
    ref2 = c << gf.c.rectangle(size=(960, 220), layer="Metal1drawing")
    ref2.move((-40, -110))
    c.add_ports(ref1.ports)
    return c


@gf.cell
def palace_test_straight_short(
    length: float = 180,
    cross_section: CrossSectionSpec = "metal_routing",
    width: float = 15,
) -> gf.Component:
    """Returns a Straight waveguide.

    Args:
        length: straight length (um).
        cross_section: specification (CrossSection, string or dict).
        width: width of the waveguide. If None, it will use the width of the cross_section.
    """
    c = gf.Component()
    ref1 = c << gf.c.straight(
        length=length, cross_section=cross_section, width=width, npoints=2
    )
    ref2 = c << gf.c.rectangle(size=(180 + 80, 220), layer="Metal1drawing")
    ref2.move((-40, -110))
    c.add_ports(ref1.ports)
    return c


@gf.cell
def palace_filter1(
    line_width: float = 20.0, coupler_length: float = 700.0, gap: float = 2.0
):
    """Test filter."""

    y_shift = (line_width + gap) / 2

    c = gf.Component()
    p = gf.Path(
        [
            (0, 100),
            (200, 100),
            (400, 0),
            (400 + coupler_length, 0),
            (400 + coupler_length + 200, 100),
            (400 + coupler_length + 400, 100),
        ]
    )
    # p.plot()

    s0 = gf.Section(
        width=20,
        layer="TopMetal2drawing",
        port_names=("e1", "e2"),
        port_types=("electrical", "electrical"),
    )
    x = gf.CrossSection(
        sections=[
            s0,
        ]
    )
    cc = gf.path.extrude(p, x)

    c = gf.Component()
    upper = c << cc
    lower = c << cc
    upper.move((0, y_shift))
    lower.mirror_y().move((0, -y_shift))

    c.add_port("P1", port=lower.ports["e1"])
    c.add_port("P2", port=upper.ports["e1"])
    c.add_port("P3", port=upper.ports["e2"])
    c.add_port("P4", port=lower.ports["e2"])

    r = c.get_region("TopMetal2drawing")
    r_sized = r.sized(+150000)
    r_sized.merge()
    c.add_polygon(r_sized, layer="Metal1drawing")

    return c


@gf.cell
def palace_GSG(line_width: float = 20.0, gap: float = 10.0):
    """Test lines."""
    c = gf.Component()
    _line1 = c << cells.straight_metal(length=500, width=line_width)

    line2 = c << cells.straight_metal(length=500, width=line_width)
    line2.move((0, gap + line_width))

    line3 = c << cells.straight_metal(length=500, width=line_width)
    line3.move((0, 2 * (gap + line_width)))

    # c.flatten()
    # c.add_port("P1", port=line1["e1"])
    # c.add_port("P2", port=line2["e2"])

    return c


@gf.cell
def palace_lowpass_filter1(pixel_size: float = 125.0):
    """Create a lowpass filter with pixelated pattern on TopMetal2.

    https://ieeexplore.ieee.org/abstract/document/11103838

    Args:
        pixel_size: Size of each pixel in micrometers.

    Returns:
        Component with pixelated filter pattern.
    """
    import numpy as np

    c = gf.Component()

    FILTER = """
0100101010111010
1100100111100010
0010000001101100
0100011101100001
0010111101010000
1001110111110000
1100000101001010
1010001111000101
1110010101100100
1100011100001010
1110011111111010
0110011001010101
0001100110010010
1001101001000010
0010110110010110
1010101111001111
"""

    arr = np.array([[int(ch) for ch in line] for line in FILTER.strip().split("\n")])
    arr = 1 - arr

    rows, cols = arr.shape
    for row in range(rows):
        for col in range(cols):
            if arr[row, col] == 1:
                rect = gf.components.rectangle(
                    size=(pixel_size, pixel_size),
                    layer=LayerMapIHP.TopMetal2drawing,
                )
                ref = c.add_ref(rect)
                ref.move((col * pixel_size, (rows - 1 - row) * pixel_size))

    input_pixel = c << rect
    input_pixel.move((-pixel_size, 3 * pixel_size))
    output_pixel = c << rect
    output_pixel.move((16 * pixel_size, 2 * pixel_size))

    input_line = c << cells.straight_metal(length=1000, width=3 * pixel_size)
    input_line.move((-1000 - pixel_size, 3.5 * pixel_size))

    output_line = c << cells.straight_metal(length=1000, width=3 * pixel_size)
    output_line.move((17 * pixel_size, 2.5 * pixel_size))

    # c.flatten()
    c.add_port("P1", port=input_line["e1"])
    c.add_port("P2", port=output_line["e2"])

    return c


if __name__ == "__main__":
    pass
