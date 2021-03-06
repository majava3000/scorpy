#
# Value Charge Dump (VCD) output support
#
# SPDX-License-Identifier: GPL-2.0

from __future__ import print_function
import string

import scorpy

# timebase to timescale conversion table for VCD. while some readers do support
# non ten-power unit spec, we go safely here. ordered by precision (lowest first)
_vcdTimescaleTable = (
    (1,              1, "s"),
    (10,           100, "ms"),
    (100,           10, "ms"),
    (1000,           1, "ms"),
    (10000,        100, "us"),
    (100000,        10, "us"),
    (1000000,        1, "us"),
    (10000000,     100, "ns"),
    (100000000,     10, "ns"),
    (1000000000,     1, "ns"),
)

# VCD emitter into file like writeable object (via print)
def generateVCD(outf, *tracks):
    # TODO: timebase harmonization, starting point harmonization
    assert(all(track.timebase == tracks[0].timebase for track in tracks))

    print("$comment\ngenerated by Scorpy/%s\n$end" % (scorpy.core.VERSION_STR), file=outf)
    # calculate the suitable timescale string
    timebase = tracks[0].timebase
    assert(timebase > 0)

    timescaleStr, factor = None, None
    for dividend, subscale, unitStr in _vcdTimescaleTable:
        if dividend % timebase == 0:
            # found it
            timescaleStr = "%u %s" % (subscale, unitStr)
            factor = dividend // timebase
            break
    assert(timescaleStr != None)
    # print("timescaleStr='%s' factor=%u" % (timescaleStr, factor))

    print("$timescale %s $end" % timescaleStr, file=outf)

    print("$scope module top $end", file=outf)
    trackIndices = tuple(range(len(tracks)))
    # combine the formatters for the tracks
    formatters = tuple( [ x.vcdFormatter for x in tracks ] )

    # emit identifiers and names for tracks and types
    for tIdx in trackIndices:
        t = tracks[tIdx]
        print("$var %s %s %s $end" % (
            t.getVCDType(),
            string.ascii_letters[tIdx],
            t.getVCDName()),
            file=outf)
    print("$upscope $end", file=outf)
    print("$enddefinitions $end", file=outf)

    changes = scorpy.core.getCombinedChanges(*tracks)
    # track time as absolute
    ts = 0
    # we only emit track values when they change, to prepare to track those
    # tracks cannot be None, so this will cause a mismatch on the first emit
    prevValues = [None] * len(trackIndices)
    for comps in changes:
        values = comps[1:]
        print("#%u" % (ts * factor), file=outf)
        for tIdx in trackIndices:
            v = values[tIdx]
            if v != prevValues[tIdx]:
                vStr = formatters[tIdx](v)
                print("%s%s" % (
                    vStr, string.ascii_letters[tIdx]), file=outf)
                prevValues[tIdx] = v
        ts += comps[0]
    # emit last ts to mark end (no signal changes at this point)
    print("#%u" % (ts * factor), file=outf)
