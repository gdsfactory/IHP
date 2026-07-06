########################################################################
#
# Copyright 2025 IHP PDK Authors
#
# Licensed under the GNU General Public License, Version 3.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.gnu.org/licenses/gpl-3.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
########################################################################

import pya

from cni.box import *
from cni.layer import *
from cni.point import *
from cni.pointlist import *
from cni.shape import *
from cni.tech import Tech

# import copy


class Ellipse(Shape):
    def __init__(self, layer: Layer, box: Box) -> None:
        self._polygon = pya.DSimplePolygon.ellipse(
            pya.DBox(box.left, box.bottom, box.right, box.top), 64
        )
        super().__init__(layer, box)
        self.set_shape(Shape.getCell().shapes(layer.number).insert(self._polygon))

    @classmethod
    def genPolygonPoints(cls, box: Box, numPoints: int, gridSize: float) -> PointList:
        polygon = pya.DSimplePolygon.ellipse(
            pya.DBox(box.left, box.bottom, box.right, box.top), numPoints
        )
        region = pya.Region(polygon)

        decimalGrid = int(gridSize / Tech.get(Tech.techInUse).dataBaseUnits)
        region.snap(decimalGrid, decimalGrid)
        snappedPolygon = region[0].to_simple_polygon()

        pointList = PointList()
        [
            pointList.append(Point(point.x, point.y))
            for point in snappedPolygon.each_point()
        ]
        return pointList

    def addToRegion(self, region: pya.Region, filter: ShapeFilter):
        if filter.isIncluded(self._layer):
            region.insert(
                self._polygon.to_itype(Tech.get(Tech.techInUse).dataBaseUnits)
            )

    def clone(
        self, nameMap: NameMapper = NameMapper(), netMap: NameMapper = NameMapper()
    ):
        poly = copy.deepcopy(self)
        poly.__internalInit(poly.getLayer())
        return poly

    """
    def destroy(self):
        if not self._polygon._destroyed():
            Shape.getCell().shapes(self.getShape().layer).erase(self.getShape())
            self._polygon._destroy()
            super().destroy()
        else:
            pya.Logger.warn(f"Polygon.destroy: already destroyed!")

    def getPoints(self) -> PointList:
        pointList = PointList()
        [pointList.append(Point(point.x, point.y)) for point in self._polygon.each_point()]
        return pointList
    """

    def moveBy(self, dx: float, dy: float) -> None:
        movedPolygon = pya.DTrans(float(dx), float(dy)) * self._polygon
        # movedPolygon = (pya.DTrans(float(dx), float(dy)) * self._polygon).to_itype(Tech.get(Tech.techInUse).
        #    dataBaseUnits).to_simple_polygon().to_dtype(Tech.get(Tech.techInUse).dataBaseUnits)
        shape = Shape.getCell().shapes(self._shape.layer).insert(movedPolygon)
        self.destroy()
        self._polygon = movedPolygon
        self.set_shape(shape)
        self.addShape()

    def toString(self) -> str:
        return f"Ellipse: {self._polygon.to_s()}"

    def transform(self, transform: Transform) -> None:
        transformedPolygon = self._polygon.transformed(transform.transform)
        shape = Shape.getCell().shapes(self.getShape().layer).insert(transformedPolygon)
        self.destroy()
        self._polygon = transformedPolygon
        self.set_shape(shape)
        self.addShape()
