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


class PhysicalRule(float):
    """
    Due to the complexity of physical design rules, the value for a physical
    design rule needs to be represented as a higher-level object, rather than simply as a single
    floating point number. For example, the design rules for minimum extension of one layer
    over another may not be just a single value. Rather, it may be represented as a pair of
    values, one for the extension in the horizontal direction and one for the extension in the
    vertical direction. This is most conveniently handled as a pair of floating point values.
    In general, this PhysicalRule object can return values representing a single floating-point
    number, a pair of floating-point numbers, or a list of of pairs of floating-point numbers.
    This approach provides the necessary flexibility to represent different types of physical
    design rules.
    These PhysicalRule objects are used in conjunction with the Python API Tech class. This
    PhysicalRule object is used as the return type for the getPhysicalRule() method for the
    Tech class. Note that there is no need to “construct” any PhysicalRule objects; they will
    be created and returned automatically by the Tech class when this getPhysicalRule()
    method is used. Note that this PhysicalRule class is derived from the basic Python float
    floating-point number class. Thus, when a single number is returned in this PhysicalRule
    object, the result can be used just like a floating-point number.

    """

    def __new__(cls, value):
        instance = super().__new__(cls, value)
        instance._value = value
        return instance

    @property
    def value(self):
        """
        the value of the PhysicalRule object; this is either a CoordValue, a
        DualCoordValue or a DualCoordArrayValue (Note that these types
        represent a floating-point number, a pair of floating-point numbers,
        or a list of pairs of floating-point numbers).

        """
        return self._value
