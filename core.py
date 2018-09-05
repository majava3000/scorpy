#
# Core functionality of scorpy
#
# SPDX-License-Identifier: GPL-2.0

from __future__ import print_function
import array
import sys
import math

VERSION_STR = "0.3"

# array.array codes to use with given bitwidths/8. Assume LP64 system first
arrayTypes = "BHIILLLL"
if array.array('L').itemsize != 8:
    # not LP64. since 3.3+ onwards, typecode "Q" exists for 64-bit, so switch to
    # that if it's present. For 3.2-, out of luck really with array.array on
    # this system, 32-bit wide integers is the max without numpy
    if "typecodes" in dir(array) and "Q" in array.typecodes:
        arrayTypes = arrayTypes.replace("L", "Q")
    else:
        print("WARNING: Numeric range restricted to 32-bits!", file=sys.stderr)

if sys.version < '3':
    integerTypes = (int, long)
else:
    integerTypes = (int,)

# helper to construct a list that can hold N wide unsigned values
def makeUnsignedList(bitwidth):
    sizeIndex = (bitwidth-1)//8
    return array.array(arrayTypes[sizeIndex])

# abstract top-level class
class Track:

    def __init__(self, name, timebase, duration=None):
        self.name = name
        self.timebase = timebase
        self.duration = duration

    # helper that returns the common parameters for the track in a formatted
    # manner
    def baseDescriptor(self, typeName):
        return "%s(n=%s, tb=%s, d=%s)" % (
            typeName,
            str(self.name),
            str(self.timebase),
            str(self.duration))

    def __iter__(self):
        return self.getSegments()

    # return track duration in seconds
    def getInSeconds(self, samples=None):
        if samples is None:
            samples = self.duration
        return float(samples) / self.timebase

    # return number of samples that given time in seconds would represent in
    # timebase of this track. Integer rounding is done to closes sample count
    # TODO: allow specifying rounding mode
    def secondsToSamples(self, tInSeconds):
        return int(0.5 + (tInSeconds * self.timebase))

    # default generator for as events assumes a single value to compare against
    # always
    # TODO: Perhaps the value should be list apply instead? then could use as
    #       many values as necessary for comparison
    def asEvents(self, value):
        return getAsEvents(self, (value,))

    # helper to return startAt and endAt for clipRegion if selection is valid
    def getAbsoluteClipRegion(self, startAt, endAt):
        # endAt can be None (valid)
        if endAt is None:
            endAt = self.duration
        # if endAt is negative, convert to absolute-index
        # dur=100, endAt=-1 -> endAt=99
        if endAt < 0:
            endAt = self.duration + endAt
        # check that neither values are negative at this point
        if startAt < 0 or endAt < 0:
            return None
        # check that startAt and endAt are within duration
        if startAt > self.duration or endAt > self.duration:
            return None
        # check that startAt is below endAt (at least time interval must be
        # selected)
        if startAt >= endAt:
            return None

        # all checks all-right, return the region in absolute
        return startAt, endAt

    # in-place cropping of track using segment iteration and setSegments at the
    # end. please override with a most efficient mechanism in each track type if
    # possible, since this is quite slow
    def crop(self, startAt=0, endAt=None):
        # convert startAt and endAt into values that are valid and don't overlap
        clipRegion = self.getAbsoluteClipRegion(startAt, endAt)
        if clipRegion is None:
            return False
        # startAt < endAt (guaranteed), both within the duration of the track
        startAt, endAt = clipRegion

        # we want a mechanism where we select data from segiter when signal is
        # "high". note that temporal clipping will have to be done as well, so
        # it's not enough to do regular selection
        self.setSegments(selectTimeRegion(self.getSegments(), startAt, endAt))

        return True

    # set new timebase, attempting to retain data resolution if possible.
    #
    # for sub-one scale factors, truncation will be done. sub-unit long segments
    # are lost (time is carried forward to the next segment)
    # factor is adjusted so that resulting timebase will be an integer one
    def setTimebase(self, newTimebase):
        # force newTimebase always to be an integer
        newTimebase = int(newTimebase + 0.5)
        f = newTimebase / float(self.timebase)
        if f == math.trunc(f):
            # attempt integer conversion if possible
            f = int(f)

        self.setSegments(scaleDuration(self.getSegments(), f))
        self.timebase = newTimebase

#
# Track with continuous values (not change based)
# Duration calculated automatically based on underlying storage element count
#
class ContinuousTrack(Track):

    def __init__(self, name, timebase, sequence):
        Track.__init__(self, name, timebase, len(sequence))
        self.data = sequence

    # no setSegments

    def __repr__(self):
        return "<%s>" % (self.baseDescriptor("ContinuousTrack"))

    def getSegmentsRaw(self):
        for v in self.data:
            yield(1, v)

    def getSegments(self):
        # deals with the case when the values repeat, otherwise VCD output might
        # emit dummy timestamps
        return cleaner(self.getSegmentsRaw())

    # in-place cropping of track.
    # TODO: evaluate whether the inplace-operation is correct. perhaps would be
    #       better to return a new track instead?
    # returns False if cropping region selection is invalid
    def crop(self, startAt=0, endAt=None):
        # convert startAt and endAt into values that are valid and don't overlap
        clipRegion = self.getAbsoluteClipRegion(startAt, endAt)
        if clipRegion is None:
            return False
        # startAt < endAt (guaranteed), both within the duration of the track
        # duration = 10 (len(data) == 10)
        #  valid:
        #   startAt = 9, endAt = 10 (offset one over the last index)
        #   startAt = 0, endAt = 1 (selects exactly the first entry only)
        startAt, endAt = clipRegion
        # the actual clipping is relatively easy to perform for continuous track
        # assuming that the underlying mechanism supports slicing. note that
        # this avoids using range deletes, as they might not be supported, but
        # this also means that the operation is not as efficient as it might
        # otherwise be
        self.data = self.data[startAt:endAt]
        self.duration = len(self.data)

        return True

class FloatTrack(ContinuousTrack):

    def __init__(self, name, timebase, sequence):
        ContinuousTrack.__init__(self, name, timebase, sequence)

    def __repr__(self):
        return "<%s>" % (self.baseDescriptor("FloatTrack"))

    def getVCDType(self):
        return "real 32"

    # return the VCD name (affects representation)
    def getVCDName(self):
        return self.name

    def vcdFormatter(self, v):
        return "r%.16g " % v

#
# Track unsigned changes at given delta times
#
class UnsignedTrack(Track):

    # Storage mechanism is application of value, then waiting for delta (ie,
    # same order as iterator)
    def __init__(self, name, timebase, bitwidth, duration=None, fromSegiter=None):
        Track.__init__(self, name, timebase, duration)
        self.width = bitwidth
        self.delta = makeUnsignedList(64)
        self.value = makeUnsignedList(bitwidth)
        self.duration = None
        # this won't match on any of the values by default
        self.hiZValue = None
        # default to bit-vector emitting
        self.setVCDTypeToReal(False)
        if fromSegiter is not None:
            self.setSegments(fromSegiter)

    # helper to split the deltas and values from a combiner set. note that combiner
    # should return (delta, value), not (delta, value1, value2, ...)
    def setSegments(self, segiter):
        absTime = 0
        newDelta = makeUnsignedList(64)
        newValue = makeUnsignedList(self.width)
        for delta, value in segiter:
            newDelta.append(delta)
            newValue.append(value)
            absTime += delta
        self.duration = absTime
        # replace existing data with new ones
        self.delta = newDelta
        self.value = newValue

        assert(len(self.delta) == len(self.value))

    def __repr__(self):
        return "<%s, width=%s, transitions=%u>" % (
            self.baseDescriptor("UnsignedTrack"), str(self.width), len(self.value))

    # generator that returns delta and value
    # each entry is duration how long value is held, and which value to hold
    # minimum delta is 1 (zero is not allowed)
    # hold value up to duration is reported as well
    def getSegments(self):
        absTimeAt = 0

        # ref to the original delta data (not strictly necessary anymore since
        # setSegments was fixed, but shorter resolving paths)
        deltas = self.delta
        values = self.value
        # set default value of None, if there are no values in the track, but
        # there is duration and we need to yield the very last entry
        v = self.hiZValue

        for changeIdx in range(len(deltas)):
            delta = deltas[changeIdx]
            v = values[changeIdx]
            yield(delta, v)
            absTimeAt += delta

        if self.duration > absTimeAt:
            # yield the last value from last delta up to duration (always present,
            # and if there's no changes in the track, this will be the only emit)
            yield(self.duration - absTimeAt, v)

    def getVCDTypeBitVector(self):
        return "reg %u" % self.width

    def getVCDNameBitVector(self):
        return "%s[%u:0]" % (self.name, self.width-1)

    def vcdFormatterBitVector(self, v):
        if v == self.hiZValue:
            # matching special value as hi-z, so use hi-z repr in VCD
            return "b%s " % ("z" * self.width)
        # otherwise use binary representation as is
        return "b"+format(v, "0%ub" % self.width)+" "

    def getVCDTypeReal(self):
        # real width is not care so use constant value
        return "real 1"

    def getVCDNameReal(self):
        return self.name

    def vcdFormatterReal(self, v):
        return "r%u " % v

    # switch vcd emit type to real (True) or bit-vector/reg (False)
    # default from constructor is bit-vector / reg type that supports high-z
    def setVCDTypeToReal(self, setToReal=True):
        if setToReal:
            self.getVCDType = self.getVCDTypeReal
            self.getVCDName = self.getVCDNameReal
            self.vcdFormatter = self.vcdFormatterReal
        else:
            self.getVCDType = self.getVCDTypeBitVector
            self.getVCDName = self.getVCDNameBitVector
            self.vcdFormatter = self.vcdFormatterBitVector

# binary track consists of one delta-list, initial value and duration (in
# track units). delta-list contains delta-time when value changes from
# previous value.
#
# deltas of zero are not supported (they might have special meaning later)
#
# delta-list is immutable (not enforced)
#
# inversion of binary track can be done by flipping the initial value
#
# constructor supports initial data (since it might be created more efficiently
# outside the object).
# .duration may be modified later, but will not act as an iteration stopper
#  (sum of deltas might cover shorter time than the whole duration)
#   in that case the "value" will be held for the remaining time until end
#   of duration
#
# Property of deltalist:
#  value at start of specific delta at given index: initialValue ^ ((deltaIdx+1) % 2)
class BinaryTrack(Track):

    def __init__(self, name, timebase, initial=0, data=None, duration=None, fromSegiter=None):
        Track.__init__(self, name, timebase, duration)
        self.initial = initial
        self.data = data
        if data is None:
            # make deltalist
            self.data = makeUnsignedList(64)
        if self.duration is None and self.data is not None:
            # setup default duration to be the sum of deltas + 1
            # so that it covers all of the delta sequence but nothing more
            # TODO: verify that the +1 makes sense, but it should, otherwise
            #       we end with a flip just at the end, and the next section
            #       duration is zero
            self.duration = sum(self.data)+1
        if fromSegiter is not None:
            self.setSegments(fromSegiter)

    def __repr__(self):
        return "<%s, i=%u, transitions=%u>" % (
            self.baseDescriptor("BinaryTrack"), self.initial, len(self.data))

    # returns a version of track that is inverted
    # name of the track will be original prefixed with 'n'
    def getInverted(self):
        return BinaryTrack('n'+self.name,
                           self.timebase,
                           self.initial^1,
                           self.data,
                           self.duration)

    # generator that returns delta and value
    # each entry is duration how long value is held, and which value to hold
    # minimum delta is 1 (zero is not allowed)
    # hold value up to duration is reported as well
    def getSegments(self):
        # start with the initial (always present)
        v = int(self.initial)
        absTimeAt = 0
        # make local ref to the data to minimize resolution path
        deltas = self.data
        for delta in deltas:
            yield(delta, v)
            v ^= 1
            absTimeAt += delta
        # yield the last value from last delta up to duration (always present,
        # and if there's no changes in the track, this will be the only emit)
        yield(self.duration - absTimeAt, v)

    # set initial and values given a segiterator which has deltas and values
    def setSegments(self, segiter):
        # initial values will be the first entry
        delta, value = next(segiter)
        self.initial = value
        absTime = 0
        # collect newly incoming data separate from current one
        newData = makeUnsignedList(64)
        # note that we're not interested in values here at all
        for deltaNext, value in segiter:
            absTime += delta
            newData.append(delta)
            delta = deltaNext
        absTime += delta
        self.duration = absTime
        # replace existing data (if any) with new one
        self.data = newData

    # return the vcd variable type to use with this track should it be emitted
    # to a VCD file
    def getVCDType(self):
        return "wire 1"

    # return the VCD name (affects representation)
    def getVCDName(self):
        return self.name

    def vcdFormatter(self, v):
        return str(v)

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

binaryWeights = tuple([ 2**(x) for x in range(64) ])

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
            weights = binaryWeights[:vCount]
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
        # function that return True irrespective of number of positional variables
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
    if isinstance(f, integerTypes):
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

# return segments with same duration but remapped values.
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
