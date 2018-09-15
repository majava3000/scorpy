#
# Core functionality of scorpy
#
# SPDX-License-Identifier: GPL-2.0

from __future__ import print_function
# we keep the track implementations in a separate file, but API-wise they're
# part of core.
from scorpy.tracks import *

import sys

# prepare for semver, although not obeyed yet
version_info = (0, 4, 0)
VERSION_STR = "%u.%u.%u" % version_info

# construct a list of valid integer types available
if sys.version_info[0] < 3:
    _integerTypes = (int, long)
else:
    _integerTypes = (int,)

##
# PUBLIC API STARTS HERE
##

# helper to require at least specific version of scorpy. emits error if not
# and terminates with error. scorpy does not use this function internally
def requireVersion(major, minor=0, patch=0):
    checkAgainst = major, minor, patch
    if version_info < checkAgainst:
        print("ERROR: At least version %u.%u.%u of Scorpy required (%u.%u.%u found). Cannot continue" % (checkAgainst+version_info) )
        sys.exit(1)
    return True

# internal combiner utility. does grunt work of getCombinedChanges, but does not
# assume inputs are itersegs
def segmentCombiner(*itersegs):

    segIterator = [ iter(t) for t in itersegs ]
    # debug only, consumes all data
    # for i in segIterator:
    #     print(list(i))
    # return

    # load initials and hold values (always present)
    initials = [ next(t) for t in segIterator ]
    segValue = [ i[1] for i in initials ]
    segHoldUntil = [ i[0] for i in initials ]

    # print("initial segValue: %r" % segValue)
    # assume all itersegs have still data (might not be true)
    unconsumedChannelIndices = list(range(len(itersegs)))
    # since we can't modify lists while iterating, this will hold the channel
    # indices to remove from the candidates. removal will be done at the end
    # of the main loop where this will also be pruned if it has something
    consumedChannelIndices = []

    # do initial emit (all source itersegs are valid at this point, no reason
    # to filter based on consumed/unconsumed status)
    timeAt = min(segHoldUntil)
    # time when we emitted last (for output delta). timeAt for first emit equals
    # delta, so no reason to calculate offset from lastEmitAt
    yield tuple([timeAt] + segValue)
    lastEmitAt = timeAt

    # we continue until there's no sources to consume
    while len(unconsumedChannelIndices) > 0:
        # print("START(luCI=%u)" % len(unconsumedChannelIndices))
        # print(" values: %r" % segValue)
        # print(" holdUntil: %r" % segHoldUntil)

        # update segHoldUntil and segValue for each track whose change was
        # consumed this time
        for chIdx in unconsumedChannelIndices:
            # time to update the value for track?
            # this will be hit for all itersegs on the first iteration
            # note that equal check is on purpose, since once itersegs run out of
            # data, their holdtime will be lower than timeAt (by design)
            if timeAt == segHoldUntil[chIdx]:
                # print("  Updated chIdx %u, match on timeAt(%u)" % (chIdx, timeAt))
                comps = next(segIterator[chIdx], None)
                if comps is None:
                    # ran out of track data. value valid until the end
                    # (ie, just remove this track from update list, don't update
                    # hold time
                    consumedChannelIndices.append(chIdx)
                    # print("   chIdx %u ran out of data, keeping value at %u" % (
                    #     chIdx, segValue[chIdx]))
                    # continue with next track, since no other side-effects from
                    # this track
                    continue
                # we have more data for the track. convert timestamp to absolute
                # and update state
                duration, value = comps
                # print("   chIdx %u next data: dur=%u, v=%r" % (chIdx, duration, value))
                segHoldUntil[chIdx] = timeAt + duration # += duration as well
                segValue[chIdx] = value

        # remove channels that are no longer with us
        if len(consumedChannelIndices) > 0:
            for chIdx in consumedChannelIndices:
                unconsumedChannelIndices.remove(chIdx)
            # erase list for next round
            consumedChannelIndices = []

        # advance time to the newest minimum. however, values that are at timeAt
        # or below must not be considered here (ie, we need to ignore itersegs
        # that we ran out of data for). Also emit the new entries at this point
        if len(unconsumedChannelIndices) > 0:
            timeAt = min((segHoldUntil[ci] for ci in unconsumedChannelIndices))

            # emit (always at least one emit exists at this point if we have
            # values that weren't completely consumed at this point)
            # print("emit(%u (@%u), %r)" % (
            #     (timeAt - lastEmitAt), timeAt, 
            #     segValue) )
            yield tuple([timeAt - lastEmitAt] + segValue)
            lastEmitAt = timeAt
    # all done, generator ends

# utility that generates an iterable sequence of combined track values.
# returned values are like with getSegments() generator, but each source track
# participates in the generation, and changes are emitted whenever any source
# track changes. results can be used for many different purposes:
# - Creating MultiBinaryTracks
# - Creating VCD emit compliant data
# - Creating decision points for binary logic/calculations
#
# Note that combiner does not care about actual value format, any format is
# supported as long as the underlying track supports the getSegments() interface
def getCombinedChanges(*tracks):
    # NOTE: timebase harmonization is not supported, but at least check that
    #       all tracks have the same timebase
    assert(all(track.timebase == tracks[0].timebase for track in tracks))
    # NOTE: check also that durations are the same for all (also should probably
    #       implement this properly)
    # BUG: need to relax this since for some reason deglitcher returns one
    #      shorter track when using test-mode. Also, this is not a critical
    #      problem, but keep it in until core reason is resolved (just comment
    #      out for now)
    # assert(all(track.duration == tracks[0].duration for track in tracks))

    return segmentCombiner(*tracks)

_binaryWeights = tuple([ 2**(x) for x in range(64) ])

# given a value combiner, return a binary value
# data will be additive with multipliers based on binary series
# delta is unchanged. this is probably horrifically inefficient
def binaryCombiner(comb):
    weights = None
    chIndices = None
    for c in comb:
        delta = c[0]
        if weights is None:
            vCount = len(c)-1
            # load the weights with the remaining length
            weights = _binaryWeights[:vCount]
            # reverse the weights for msb order (more natural to debug)
            weights = tuple(reversed(weights))
            #print("binaryCombiner: weights: %s" % str(weights))
            chIndices = tuple(range(vCount))
        # multiply entries by respective entries of values and sum them
        v = sum( (c[1+chIdx] * weights[chIdx] for chIdx in chIndices) )
        # print("(%u, %s) -> (%u, %s)" % (delta, c[1:1+vCount], delta, v))
        yield (delta, v)

# deglitch a combiner stream
# any delta that is equal or smaller to given value will be combined
# with the following entry
def deglitcher(comb, samplesToDeglitch=1):
    # amount of accumulated change for next entry if glitch detected
    accu = 0
    # track glitched entry, so that we can remove the last one
    prevGlitch = None
    for c in comb:
        if c[0] <= samplesToDeglitch:
            accu += c[0]
            prevGlitch = c
        else:
            # duration is above glitch limit, we'll emit
            if accu > 0:
                # emit with any accumulator applied here
                yield( tuple( (c[0]+accu,) + c[1:] ) )
                accu = 0
            else:
                # emit unchanged
                yield(c)
    # we might have a glitch at the very end. if so, don't deglitch it
    # TODO: this is untested, need testdata for this
    if accu > 0:
        yield(prevGlitch)

# returns basic statistic data from the track:
# - number of each value is present
# - total duration of each value
def getBasicStatistics(comb):
    # this will contain the results:
    # - key will be an unique value
    # - data will be count and sum over duration
    ret = {}
    for delta, value in comb:
        if value not in ret:
            ret[value] = [0, 0]
        ret[value][0] += 1
        ret[value][1] += delta

    return ret

# Allow using a special symbols to document pass through cases. Can be used with
# replacer and segmentPicker
VALUE_PASSTHROUGH = None
NO_FILTER = None

# executes filter on each segment, then:
# - if filter returns False, passes segment unmodified
# - if filter returns True, calls the replacerFunc with the segmentData applied
#   if replacerFunc returns None:
#   - return original segment unmodified
#   otherwise replaceFunc should return an iterable with at least one segment
#   which the same configuration as the original data. iterator may return
#   multiple segments as well, and all will be returned to caller
# If filterFunc is None, no filtering will be done (replaceFunc will be called
# on each segment)
# NOTE: returned segments might be unclean
def replacer(segiter, filterFunc, replaceFunc):
    if filterFunc is NO_FILTER:
        # function that returns True irrespective of number of positional vars
        filterFunc = lambda *_: True
    for segment in segiter:
        if not filterFunc(*segment):
            # filter didn't match, pass as is
            # print("replacer(%s): no match, pass-through" % str(segment))
            yield segment
        else:
            r = replaceFunc(*segment)
            # print("replacer(%s): matched, result=%s" % (str(segment), str(r)))
            if r is VALUE_PASSTHROUGH:
                # replacer decided to avoid modifications, pass as is
                # print(" replacer: replacer didn't want to replace, yielding original")
                yield segment
            else:
                # replacer returned a segiter, so run that through before
                # continuing with regular programming
                for replacementSegment in r:
                    # print(" replacer: yielding %s" % str(replacementSegment))
                    yield replacementSegment

# executes filter on each segment, and returns new segments with 0 or 1 values
# depending whether the filter matched or not (1 = match). Values to use as
# True/False replacement may also be given as an optional parameter (True first,
# False then)
def tester(segiter, filterFunc, resultValues=(1, 0)):
    # make a local map from the values. Note that core.VALUE_PASSTHROUGH is
    # acceptable for both
    retValues = {
        True: resultValues[0],
        False: resultValues[1],
    }
    for segment in segiter:
        # NOTE: passes multidimensional values onwards correctly here
        result = filterFunc(*segment)
        v = retValues[result]
        if v is VALUE_PASSTHROUGH:
            # TODO: this will clip to single unit value vectors. Perhaps the
            #       PASSTHROUGH should be also dimensional? if single
            #       dimensional but input is multidimensional, copy whole input
            #       otherwise allow each dimension to be passthrough'd
            #       separately
            v = segment[1]
        yield (segment[0], v)

# given segiter, combine any segments that have identical values
def cleaner(segiter):
    prevValues = None
    prevDeltaAccumulator = 0
    for segment in segiter:
        newValues = segment[1:]
        newDelta = segment[0]
        if newValues == prevValues:
            # repeat, accumulate accumulator, do not yield
            prevDeltaAccumulator += newDelta
            continue
        # values change
        # emit previously stored data
        if prevValues is not None:
            yield ((prevDeltaAccumulator,) + prevValues)
        prevValues = newValues
        prevDeltaAccumulator = newDelta
    # we are likely to have a segment still unemitted so emit now
    if prevValues is not None:
        yield ((prevDeltaAccumulator,) + prevValues)

# replace input data with given value when given maskiter evalutes to boolean
# True. Returned values might not be clean
def setMaskValue(segiter, maskiter, newValue):
    # print("setMaskValue: starting")
    combinedSegments = segmentCombiner(segiter, maskiter)
    # print("setMaskValue: combinedSegments set up")
    # replace value when mask evals true
    selectIfMaskTrue = lambda dur, origValue, mask: mask
    # # fail all filtering
    # selectIfMaskTrue = lambda dur, origValue, mask: False
    # segments to produce should be same duration, but with value replaced
    # note that we'll propagate the mask back into the result, since we can
    # drop that out later and it's important to retain the dimensionality
    # since replacer supports returning with multiple segments, return with an
    # iterable with the results in this format
    replacerFunc = lambda dur, origValue, mask: ( (dur, newValue, mask), )
    # result of this will be segments with old|newValue and mask (unclean)
    replaced = replacer(combinedSegments, selectIfMaskTrue, replacerFunc)
    # print("setMaskValue: lambdas and replaced set up")
    # at this point, we'll want to drop the mask entry, since it was added by
    # us and we don't want to communicate that back. use a generator expression
    # for this
    # slicer = lambda x: (x[0], x[1])
    # origDimensioned = ( slicer(seg) for seg in replaced)
    origDimensioned = ( seg[:-1] for seg in replaced)
    # origDimensioned = ( slicer(seg) for seg in replaced)
    # origDimensioned = replaced
    return origDimensioned

# Returns events based on value match
# Returned data:
#  (delta, duration of event)
def getAsEvents(segiter, basedOnValues):
    lastEmitAt = 0
    prevSegmentAt = 0
    for segment in segiter:
        # print("segment=%s" % str(segment))
        delta = segment[0]
        values = segment[1:]
        # if we have a value-match, we have a new event
        if values == basedOnValues:
            # emit delta based on previous emit
            yield (prevSegmentAt - lastEmitAt, delta)
            lastEmitAt = prevSegmentAt
        # advance to next segment
        prevSegmentAt += delta

# returns segiter based on iterable "continuous" input data
# (used by GCCF binary input, but may be useful for other purposes as well)
# timeScale can be used to change the factor with which the returned data is
# processed
def segiterFromIterable(iterable, timeScaler=1):
    i = iter(iterable)
    count = 1
    prevV = next(i)
    for v in i:
        if v == prevV:
            count += 1
        else:
            yield(timeScaler * count, prevV)
            prevV, count = v, 1
            #count = 1
    yield(timeScaler * count, prevV)

# returns segiter that picks data from input segiter given time region given
# (does not return anything before or after the selection points, so duration of
# returned segiter is likely to be shorter than the input
def selectTimeRegion(segIter, startAt, endAt):
    absTime = 0
    for segment in segIter:
        # the following cases exist:
        # 1) segment is completely before startAt -> omitted
        #    segEnd <= startAt
        # 2) segment is partially before startAt (overlaps) -> cut + emit
        #    segEnd > startAt
        #    segStart < startAt
        #    segEnd <= endAt
        # 3) segment is completely within startAt..endAt -> emit as is
        #    segStart >= startAt
        #    segEnd <= endAt
        #    corner case here is a segment that exactly covers the selection
        #    interval
        # 4) segment is partially over endAt (overlaps) -> cut + emit
        #    segStart >= startAt
        #    sendEnd > endAt
        # 5) segment is partially over startAt and endAt (overlaps both) -> cut + emit
        #    segStart < startAt
        #    segEnd > endAt
        # 6) segment is completely after endAt -> omitted + end iteration
        #    segStart >= endAt

        segStart = absTime
        segEnd = absTime + segment[0]

        if segEnd > startAt:
            if segStart >= endAt:
                # 6 segment completely after endAt, end
                # print("p6(end) [no emit]")
                return
            # print("p1(segEnd=%u > startAt=%u) [info]" % (segEnd, startAt))
            # 2-6 can be true
            if segStart < startAt:
                if segEnd <= endAt:
                    # 2
                    # dur = segEnd - startAt
                    # print("p2(segEnd=%u <= endAt=%u)" % (segEnd, endAt))
                    yield(segEnd - startAt, segment[1])
                else:
                    # 5
                    # dur = selection range
                    # print("p3(segEnd=%u > endAt=%u)" % (segEnd, endAt))
                    yield(endAt - startAt, segment[1])
            elif segEnd <= endAt:
                # 3 (pass-through)
                # print("p4(segEnd=%u <= endAt=%u)" % (segEnd, endAt))
                yield(segment)
            elif segEnd > endAt:
                # 4
                # dur = endAt - segStart
                # print("p5(segEnd=%u > endAt=%u)" % (segEnd, endAt))
                yield(endAt - segStart, segment[1])
            else:
                assert(False)
        else:
            # print("p0(segEnd=%u <= startAt=%u) [no emit]" % (segEnd, startAt))
            pass

        absTime += segment[0]

# scale duration of the segments by given factor. Segment durations are
# rounded to closest integer, sub-one segments are lost, and duration is added
# to the next segment if possible.
# if integer factor given, no loss of data happens (including with unit)
# note that 0 as input is accepted as are negative values (unsure why you'd want
# that, but it's possible)
def scaleDuration(segiter, f):
    # handle special case of non-float
    if isinstance(f, _integerTypes):
        for delta, v in segiter:
            yield(delta * f, v)
        return

    # f is not integer, need to do this a bit more carefully
    # this will contain the accrued time due to sub-one duration segments (we'll
    # add it to the next segment duration)
    accumulator = 0.0
    for delta, v in segiter:
        newDelta = delta * f + accumulator
        # truncate to integer
        intDelta = int(newDelta)
        if intDelta == 0:
            # too short, accrue into next (contains previous accumulator as well)
            accumulator = newDelta
            continue

        yield(intDelta, v)
        # accrue any part that isn't included in the current segment. always
        # >= 0.0 and < 1.0
        accumulator = newDelta - intDelta

# given a track, will return an activity track (binary) which is 1 when there is
# activity and 0 when there is not activity. threshold done by value being
# stable for long enough time (expressed in seconds)
# output track has the same timebase as origin track
def makeActivityTrack(name, inputTrack, activityThreshold):
    # create activity track
    actTrack = BinaryTrack(name, inputTrack.timebase)
    stabilityThresholdSamples = actTrack.secondsToSamples(activityThreshold)
    # our activity filter will return 1 on any segment whose duration is less
    # than the stability threshold and 0 otherwise.
    actFilter = lambda dur, level: (dur <= stabilityThresholdSamples)
    actBuilder = tester(inputTrack, actFilter)
    # since we're likely to have multiple successive segments with the same
    # value, we'll need to clean them all up before setting as the data to the
    # new track
    actTrack.setSegments(cleaner(actBuilder))
    return actTrack

# return segments with same duration but remapped values. values not present
# in map are passed without modifications.
# supports multidimensional values
# returns values are unclean
def valueRemapper(segiter, valueMap):

    for segment in segiter:
        k = segment[1:]
        # print("k:", k)
        r = segment
        if k in valueMap:
            # print("hit")
            r = ((segment[0],) + valueMap[k])
        # print(segment, r)
        yield r

# select segments from input if there is a change in the selector iterator that
# occurs within the input segment duration. more than single selection event per
# segment is ignored (at-most-once). If there are no changes during the input
# segment, it will be unselected (see below)
#
# each input segment is evaluated independently and will either be selected or
# unselected. both selected and unselected may return either the original value
# of input, or be replaced by specific values. selection/unselection logic can
# also be inverted
#
# default parameters are chosen so that output is compatible for binaryTrack
# consumption for easy consumption
def segmentPicker(inputSegiter, changeSegiter, valueWhenSelected=1, valueWhenUnselected=0, invertSelection=False):

    # since we use the iterator interface for changes selectively, we need to
    # make a local iter wrapper for it (incase tracks are given as parameters)
    # having iter(iter(a)) is not a problem (although might be slightly
    # wasteful)
    changeSegiter = iter(changeSegiter)

    # always positive after processing a single segment, but may turn negative
    # while processing the segment
    durationUntilChange = next(changeSegiter)[0]

    # # debugging only
    # debugTimebase = 250000000
    # ts = 0

    # we make emission decision based on the inputSegiter, not the changeSegiter
    # origin cannot be selected, since there's no way to express change at zero
    for segment in inputSegiter:

        # default to unselected
        isSelected = False

        # the following can happen:
        # 1. segment is shorter or as long as durationUntilChange -> not selected
        #    (durationUntilChange post adjustment is positive or zero)
        # 2. segment is longer than durationUntilChange -> selected
        #    (durationUntilChange post adjustment is negative)
        #
        #    since multiple selections must be combined into one, we need to
        #    review the changeSegiter forward until current segment no longer
        #    covers it (or covers exactly)
        #
        #    while durationUntilChange < 0:
        #      durationUntilChange += next(changeSegiter)[0]
        #
        #    So infact, we can decrement first, then do the decision based on
        #    the result

        durationUntilChange -= segment[0]

        if durationUntilChange < 0:
            isSelected = True
            # skip any changes until we're at least at zero
            while durationUntilChange < 0:
                durationUntilChange += next(changeSegiter)[0]

        if invertSelection:
            isSelected = not isSelected

        # default to pass unchanged value
        v = segment[1]

        if isSelected:
            if valueWhenSelected is not VALUE_PASSTHROUGH:
                v = valueWhenSelected
        else:
            if valueWhenUnselected is not VALUE_PASSTHROUGH:
                v = valueWhenUnselected

        # debugging only
        # if isSelected:
        #     print("%9u INPUT: %s (durationUntilChange=%d)" % (ts / (debugTimebase / 1000000), segment, durationUntilChange))
        #     print("              -> %s (selected=%u)" % (str(emitSegment), isSelected))
        #     print("                 dur=%u us" % (segment[0] / (debugTimebase / 1000000)) )
        # ts += segment[0]

        emitSegment = segment[0], v
        yield(emitSegment)

# Splits anchor segments into pre-anchor-post segments according to given
# sample durations (if possible). mostly useful for generating synthetic power
# transition modes that are implicit and not visible in digital captures
# if segment duration is shorter than pre+post, there anchor mode will not be
# present in output (and the segment length is divided linearly between pre and
# post)
def addSyntheticTransitions(segiter, modeAnchor, modePre, modePost, durationPre, durationPost):
    # if anchor is too short to contain both full times, only pre+post will be
    # generated and the segment time is split between them according to the
    # relative length of each.
    preDurationFactor = durationPre / (durationPre + durationPost)
    # duration cutoff under which there won't be anchor since it can't fit
    anchorCutoffDuration = durationPre + durationPost

    # replacer function will be called upon hitting anchor
    # we reuse the anchorValue since it's given to us anyway
    def addSynthModes(segmentDuration, anchorValue):
        r = None

        if segmentDuration <= anchorCutoffDuration:
            # only two segments. split the time according to relative times
            # taken by pre and post (assume the actions are linear in terms of
            # moving into anchor mode and out of it)
            postSegDuration = int(0.5 + preDurationFactor * segmentDuration)
            preSegDuration = segmentDuration - postSegDuration
            assert(postSegDuration >= 0 and preSegDuration >= 0)
            r = ( (preSegDuration, modePre),
                  (postSegDuration, modePost) )
        else:
            # we generate all three segments
            anchorSegDuration = segmentDuration - (durationPre + durationPost)
            r =  ( (durationPre, modePre),
                   (anchorSegDuration, anchorValue),
                   (durationPost, modePost) )
        # print("addSynthModes(ind=%u): r=%s" % (segmentDuration, str(r)) )
        return r

    # filter to use as anchor detection:
    #  duration used to ensure that at least 2 time units are present,
    #  otherwise pre+post cannot be represented (minimum represetation without
    #  anchor)
    anchorFilter = lambda dur, v: (dur >= 2 and v == modeAnchor)
    # return the iterator to caller
    return replacer(segiter, anchorFilter, addSynthModes)
