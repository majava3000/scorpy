#!/usr/bin/env python
#
# deglitcher example generator/code
#
# SPDX-License-Identifier: GPL-2.0

from __future__ import print_function
from common import *

if __name__ == '__main__':
    name = 'deglitcher'
    args = getArgs(name)

    input_ = makeSimpleTrack('input', shortcodeToSegiter("ABC.D.E..F..G...H..I..."))

    # these two anchors are used by the include to actually get the python
    # specific bit of the output. make sure that only one indent level is here
    # (tab=4)
    # example-start-here
    r1 = core.deglitcher(input_)
    r2 = core.deglitcher(input_, 2)
    r3 = core.deglitcher(input_, 3)
    r4 = core.deglitcher(input_, 4)
    # example-end-here

    r1 = makeSimpleTrack('r1', r1)
    r2 = makeSimpleTrack('r2', r2)
    r3 = makeSimpleTrack('r3', r3)
    r4 = makeSimpleTrack('r4', r4)

    # do magic. supports shortcode, wavedrom and docint modes. the label is used
    # only for wavedrom output mode. tuple is necessary for the results
    doIt(args, input_, [r1, r2, r3, r4], name)
