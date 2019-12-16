#!/usr/bin/env python
#
# durationScaler example generator/code
#
# SPDX-License-Identifier: GPL-2.0

from __future__ import print_function
from common import *

if __name__ == '__main__':
    name = 'durationScaler'
    args = getArgs(name)

    input_ = makeSimpleTrack('input', shortcodeToSegiter("A...B...C...D..."))

    # example-start-here
    r1 = core.durationScaler(input_, 1)
    r2 = core.durationScaler(input_, 2)
    r3 = core.durationScaler(input_, 1.5)
    r4 = core.durationScaler(input_, 1/2.0)
    r5 = core.durationScaler(input_, 1/3.0)
    r6 = core.durationScaler(input_, 1/6.0)
    # example-end-here

    r1 = makeSimpleTrack('r1', r1)
    r2 = makeSimpleTrack('r2', r2)
    r3 = makeSimpleTrack('r3', r3)
    r4 = makeSimpleTrack('r4', r4)
    r5 = makeSimpleTrack('r5', r5)
    r6 = makeSimpleTrack('r6', r6)

    # do magic. supports shortcode, wavedrom and docint modes. the label is used
    # only for wavedrom output mode. tuple is necessary for the results
    doIt(args, input_, [r1, r2, r3, r4, r5, r6], name)
