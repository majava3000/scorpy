#
# Auxiliary utils that can be shared between higher level Scorpy parts
# Must not have any internal dependencies
#
# SPDX-License-Identifier: GPL-2.0

from __future__ import print_function
import array
import sys

# array.array codes to use with given bitwidths/8. Assume LP64 system first
_arrayTypes = "BHIILLLL"
if array.array('L').itemsize != 8:
    # not LP64. since 3.3+ onwards, typecode "Q" exists for 64-bit, so switch to
    # that if it's present. For 3.2-, out of luck really with array.array on
    # this system, 32-bit wide integers is the max without numpy
    if "typecodes" in dir(array) and "Q" in array.typecodes:
        _arrayTypes = _arrayTypes.replace("L", "Q")
    else:
        print("WARNING: Numeric range restricted to 32-bits!", file=sys.stderr)

# internal helper to construct a list that can hold N bits wide unsigned values
def makeUnsignedList(bitwidth):
    sizeIndex = (bitwidth-1)//8
    return array.array(_arrayTypes[sizeIndex])
