########################################################################
#
# Copyright 2024 IHP PDK Authors
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

import copy
from functools import singledispatchmethod

import pya

from cni.layer import *
from cni.pointlist import *
from cni.shape import *
from cni.tech import Tech


class Polygon(Shape):
    @singledispatchmethod
    def __init__(self, arg1, arg2, arg3=None):
        pass

    @__init__.register
    def _(self, arg1: Layer, arg2: PointList) -> None:
        pyaPoints = []
        [pyaPoints.append(point.point) for point in arg2]

        self._polygon = pya.DSimplePolygon(pyaPoints, True)
        self.__internalInit(arg1)

    @__init__.register
    def _(self, arg1: pya.DSimplePolygon, arg2: int, arg3: Layer) -> None:
        self._polygon = arg1
        self.__internalInit(arg3)

    def __internalInit(self, layer: Layer):
        super().__init__(layer, self._polygon.bbox())
        self.set_shape(Shape.getCell().shapes(layer.number).insert(self._polygon))

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

    def destroy(self):
        if not self._polygon._destroyed():
            Shape.getCell().shapes(self.getShape().layer).erase(self.getShape())
            self._polygon._destroy()
            super().destroy()
        else:
            pya.Logger.warn("Polygon.destroy: already destroyed!")

    def getPoints(self) -> PointList:
        pointList = PointList()
        [
            pointList.append(Point(point.x, point.y))
            for point in self._polygon.each_point()
        ]
        return pointList

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
        return f"Polygon: {self._polygon.to_s()}"

    def transform(self, transform: Transform) -> None:
        transformedPolygon = self._polygon.transformed(transform.transform)
        shape = Shape.getCell().shapes(self.getShape().layer).insert(transformedPolygon)
        self.destroy()
        self._polygon = transformedPolygon
        self.set_shape(shape)
        self.addShape()
