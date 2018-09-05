#
# Reuseable simple reports
#
# SPDX-License-Identifier: GPL-2.0

from __future__ import print_function
import sys
from scorpy import core

# Generic mode based score reporting utility given track (segiter is not enough)
# modeInfo is a list of following entries:
#  (value, label, score)
# Values that are present in segiter that are not listed in the modeInfo are
# ignored. Only pretty printing supported at the moment
def emitModeReport(track, modeInfo, outf=sys.stdout):
    stats = core.getBasicStatistics(track)

    # duration in seconds so that we can scale to percentages correctly
    dur = track.getInSeconds()
    durSamples = track.duration
    # we'll also want to calculate count per second
    countToCPSFactor = 1 / dur
    # total score accumulator (for percentage of total score)
    totalScore = 0

    # table contents
    formatter = ( r"%s", r"%s", r"%6.3f", r"%6.3f", r"%.2f", r"%.3f" )
    table = [ [ "Mode", "V", r"s/tot%", r"t/tot%", "count/s", "score" ] ]

    # we'll accumulate the total score while emitting rest, and back-patch the
    # table
    for v, modeStr, score in modeInfo:
        # jump over entries that are not represented at all
        if v not in stats:
            continue
        count, totDuration = stats[v]
        ofTotal = float(totDuration) / durSamples
        modeScore = ofTotal * score
        totalScore += modeScore
        table.append([modeStr, v, None, ofTotal * 100.0, float(count)*countToCPSFactor, modeScore * 100])
    # update the percentage of total scores and convert to strings using the
    # formatters
    for idx in range(1, len(table)):
        table[idx][2] = table[idx][5] / totalScore
        for enidx in range(len(table[idx])):
            table[idx][enidx] = formatter[enidx] % table[idx][enidx]
    # calculate the maximum column widths
    columnFormatters = [ 0 ] * len(table[0])
    totalWidth = 0
    for idx in range(len(table[0])):
        maxWidth = max(map(lambda x: len(table[x][idx]), range(len(table))))
        totalWidth += maxWidth
        columnFormatters[idx] = r'%'+("%u" % maxWidth)+'s'
    totalWidth += 2*(len(table[0])-1)

    for idx in range(len(table)):
        components = map(lambda enidx: columnFormatters[enidx] % table[idx][enidx], range(len(table[idx])))
        print('  '.join(components), file=outf)
        if idx == 0:
            # after the header print out the hdiv
            print("-" * totalWidth, file=outf)

    print("\nTOTAL SCORE: %.3f (lower is better, max=%.3f). Total time %.5f seconds" % (totalScore*100, 100*10, dur), file=outf)
