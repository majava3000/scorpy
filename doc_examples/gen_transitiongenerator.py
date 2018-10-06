#!/usr/bin/env python
#
# transitionGenerator example generator/code
#
# SPDX-License-Identifier: GPL-2.0

from __future__ import print_function
from common import *

if __name__ == '__main__':
    name = 'transitionGenerator'
    args = getArgs(name)

    input_ = makeSimpleTrack('input', shortcodeToSegiter("0.R0R0.R0..R0...R0...."))

    # # this allows us to use symbols as is, without messing stuff us. only useful
    # # for examples though
    u = 117
    d = 100
    R = 82

    # these two anchors are used by the include to actually get the python
    # specific bit of the output. make sure that only one indent level is here
    # (tab=4)
    # example-start-here
    r1 = core.transitionGenerator(input_, 0, d, u, 1, 1)
    r2 = core.transitionGenerator(input_, 0, d, u, 1, 2)
    r3 = core.transitionGenerator(input_, 0, d, u, 2, 2)
    # example-end-here

    r1 = makeSimpleTrack('result1', r1)
    r2 = makeSimpleTrack('result2', r2)
    r3 = makeSimpleTrack('result3', r3)

    # do magic. supports shortcode, wavedrom and docint modes. the label is used
    # only for wavedrom output mode. tuple is necessary for the results
    doIt(args, input_, [r1, r2, r3], name)
