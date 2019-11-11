#!/usr/bin/env python
#
# replacer example generator/code
#
# SPDX-License-Identifier: GPL-2.0

from __future__ import print_function
from common import *

if __name__ == '__main__':
    name = 'replacer'
    args = getArgs(name)

    input_ = makeSimpleTrack('input', shortcodeToSegiter("ABCA.B.C.A..B..C..A..."))

    # this allows us to use symbols as is, without messing stuff us. only useful
    # for examples though
    A = 65
    B = 66
    Y = 89
    n = 110

    # these two anchors are used by the include to actually get the python
    # specific bit of the output. make sure that only one indent level is here
    # (tab=4)
    # example-start-here
    # set duration of all segments to 1, without modifying their value
    r1 = core.replacer(input_, core.FILTER_ALWAYS_TRUE, lambda _, v: ( (1, v), ) )
    # split segments into two, conserving duration
    r2 = core.replacer(input_, lambda dur, _: (dur >= 2), lambda dur, v: ( (1, v), (dur-1, n) ) )
    # insert a special segment after each matching one
    r3 = core.replacer(input_, lambda _, v: (v == B), lambda dur, v: ( (dur, v), (2, n) ) )
    # remove segments with specific value
    r4 = core.replacer(input_, lambda _, v: (v == A), lambda *_: tuple() )
    # replace every second matching segment
    counter = 1
    def repEverySecond(dur, _):
        global counter
        counter += 1
        if counter % 2 == 0:
            # do not modify segment
            return core.VALUE_PASSTHROUGH
        return ( (dur, n), )
    r5 = core.replacer(input_, lambda _, v: (v == A), repEverySecond )
    # example-end-here

    r1 = makeSimpleTrack('r1', r1)
    r2 = makeSimpleTrack('r2', r2)
    r3 = makeSimpleTrack('r3', r3)
    r4 = makeSimpleTrack('r4', r4)
    r5 = makeSimpleTrack('r5', r5)

    # do magic. supports shortcode, wavedrom and docint modes. the label is used
    # only for wavedrom output mode. tuple is necessary for the results
    doIt(args, input_, [r1, r2, r3, r4, r5], name)
