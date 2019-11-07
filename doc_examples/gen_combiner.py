#!/usr/bin/env python
#
# combiner example generator/code
#
# SPDX-License-Identifier: GPL-2.0

from __future__ import print_function
from common import *

if __name__ == '__main__':
    name = 'combiner'
    args = getArgs(name)

    in1 = makeSimpleTrack('in1', shortcodeToSegiter("A...B...C...D..."))
    in2 = makeSimpleTrack('in2', shortcodeToSegiter("A..B..C..D..A..B"))
    in3 = makeSimpleTrack('in3', shortcodeToSegiter("A.B.C.D.A.B.C.D."))

    # # this allows us to use symbols as is, without messing stuff us. only useful
    # # for examples though
    # B = 66
    # Y = 89
    # n = 110

    # # these two anchors are used by the include to actually get the python
    # # specific bit of the output. make sure that only one indent level is here
    # # (tab=4)
    # # example-start-here
    # r1 = core.tester(input_, lambda dur, v: (v == B and dur == 2))
    # r2 = core.tester(input_, lambda dur, v: (v == B and dur == 2), (Y, n))
    # r3 = core.tester(input_, lambda dur, v: (dur == 2), (core.VALUE_PASSTHROUGH, n))
    # r4 = core.tester(input_, lambda dur, v: (dur == 2), (Y, core.VALUE_PASSTHROUGH))
    # # example-end-here
    # example-start here
    r = core.combiner(in1, in2, in3)
    # example-end-here

    # expand them in memory since we reuse the durations
    # 2-dim, where i[0] dur and rest are values (3x)
    r = tuple(r)
    print(r)
    resultTrack = []
    # vIndices = range(1, len(r)) # (1, 2, 3)
    for vIndex in range(1, len(r[0])):
        vData = map(lambda x: (x[0], x[vIndex]), r)
        print(vIndex, vData)
        resultTrack.append(makeSimpleTrack('r%u' % (vIndex-1), vData))

    #print(r)

    # for ie in r:
    #     # python 3 has *v, but we don't
    #     dur = ie[0]
    #     v = ie[1:]
    #     print(dur, v)
    # 2 (65, 65, 65)
    # 1 (65, 65, 66)
    # 1 (65, 66, 66)
    # 2 (66, 66, 67)
    # 2 (66, 67, 68)
    # 1 (67, 67, 65)
    # 1 (67, 68, 65)
    # 2 (67, 68, 66)
    # 2 (68, 65, 67)
    # 1 (68, 65, 68)
    # 1 (68, 66, 68)
    # so, need three new simple tracks with the values, but with the dur
    # repeating.



    # we fail here, since UnsignedTrack is attempted from the input
    # we should probably do a local unpack of the tracks instead and make
    # separate outputs based on those.
    #r1 = makeSimpleTrack('result1', r1)
    #r2 = makeSimpleTrack('result2', r2)
    #r3 = makeSimpleTrack('result3', r3)
    #r4 = makeSimpleTrack('result4', r4)

    # do magic. supports shortcode, wavedrom and docint modes. the label is used
    # only for wavedrom output mode. tuple is necessary for the results
    #doIt(args, input_, [r1, r2, r3, r4], name)
    # This is the form that we want to use here. however, we probably also need
    # to tell the generator that we can render properly.
    # Challenge here is that r is multivalued segiter.
    # this results in a failure
    #doIt(args, [in1, in2, in3], r, name)
    doIt(args, [in1, in2, in3], resultTrack, name)
