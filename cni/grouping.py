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

from __future__ import annotations

import pya

from cni.box import Box
from cni.physicalComponent import *
from cni.tech import Tech


class Grouping(PhysicalComponent):
    def __init__(self, name: str = "", components: PhysicalComponent = None):
        super().__init__()
        self._name = name
        self._components = []

        if components is not None:
            self._components.add(components)

    def __iter__(self):
        return self._components.__iter__()

    def __next__(self):
        return self._components.__next__()

    def add(self, components: PhysicalComponent) -> None:
        if type(components) is not list:
            self._components.append(components)
        else:
            self._components.extend(components)

    def addToRegion(self, region: pya.Region, filter: ShapeFilter):
        [component.addToRegion(region, filter) for component in self._components]

    def clone(
        self, nameMap: NameMapper = NameMapper(), netMap: NameMapper = NameMapper()
    ):
        components = []
        [components.append(component.clone()) for component in self._components]
        return Grouping(self._name, components)

    def destroy(self):
        [component.destroy() for component in self._components]
        self._components.clear()

    def getBBox(self, filter: ShapeFilter = ShapeFilter()) -> Box:
        region = pya.Region()
        [component.addToRegion(region, filter) for component in self._components]
        dbox = region.bbox().to_dtype(Tech.get(Tech.techInUse).dataBaseUnits)
        return Box(dbox.left, dbox.bottom, dbox.right, dbox.top)

    def getComps(self) -> list:
        return self._components

    def getComp(self, index: int) -> PhysicalComponent:
        return self._components[index]

    def moveBy(self, dx: float, dy: float) -> None:
        [component.moveBy(dx, dy) for component in self._components]

    def toString(self):
        [component.toString() for component in self._components]

    def transform(self, transform: Transform) -> None:
        [component.transform(transform) for component in self._components]
