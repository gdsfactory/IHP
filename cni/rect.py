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

from cni.box import Box
from cni.layer import Layer
from cni.shape import *
from cni.tech import Tech


class Rect(Shape):
    def __init__(self, layer: Layer, box: Box):
        self._box = box
        self._layer = layer
        self.__internalInit()

    def __internalInit(self):
        super().__init__(self._layer, self._box)
        self.set_shape(Shape.getCell().shapes(self._layer.number).insert(self._box.box))
        self._box.setRect(self)

    def addToRegion(self, region: pya.Region, filter: ShapeFilter):
        if filter.isIncluded(self._layer):
            region.insert(
                self._box.box.to_itype(Tech.get(Tech.techInUse).dataBaseUnits)
            )

    def clone(
        self, nameMap: NameMapper = NameMapper(), netMap: NameMapper = NameMapper()
    ):
        rect = copy.deepcopy(self)
        rect.__internalInit()
        return rect

    def destroy(self):
        self._box.destroy()
        super().destroy()

    def moveBy(self, dx: float, dy: float) -> None:
        self._box.moveBy(dx, dy)

    def toString(self) -> str:
        return f"Rect: {self._box.box.to_s()}"

    def transform(self, transform: Transform) -> None:
        self._box.transform(transform)

    @property
    def bottom(self):
        return self._box.bottom

    @property
    def left(self):
        return self._box.left

    @property
    def right(self):
        return self._box.right

    @property
    def top(self):
        return self._box.top
