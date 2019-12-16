#
# Track implementations for Scorpy
# Do not place anything else in this file, only top level classes
#
#
# SPDX-License-Identifier: GPL-2.0

from __future__ import print_function

import scorpy
import scorpy.auxutil as auxutil

import math

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

    def getSegments(self):
        raise NotImplementedError('subclasses must override getSegments()!')

    def setSegments(self, segiter):
        raise NotImplementedError('subclasses must override setSegments()!')

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
        return scorpy.core.getAsEvents(self, (value,))

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
        self.setSegments(scorpy.core.regionSelector(self.getSegments(), startAt, endAt))

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

        self.setSegments(scorpy.core.durationScaler(self.getSegments(), f))
        self.timebase = newTimebase

#
# Track with continuous values (not change based)
# Duration calculated automatically based on underlying storage element count
#
class ContinuousTrack(Track):

    def __init__(self, name, timebase, sequence):
        Track.__init__(self, name, timebase, len(sequence))
        self.data = sequence

    def setSegments(self, segiter):
        raise NotImplementedError('ContinuousTrack does not support .setSegments()!')

    def __repr__(self):
        return "<%s>" % (self.baseDescriptor("ContinuousTrack"))

    def getSegmentsRaw(self):
        for v in self.data:
            yield(1, v)

    def getSegments(self):
        # deals with the case when the values repeat, otherwise VCD output might
        # emit dummy timestamps
        return scorpy.core.cleaner(self.getSegmentsRaw())

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
        self.delta = auxutil.makeUnsignedList(64)
        self.value = auxutil.makeUnsignedList(bitwidth)
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
        newDelta = auxutil.makeUnsignedList(64)
        newValue = auxutil.makeUnsignedList(self.width)
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
            self.data = auxutil.makeUnsignedList(64)
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
        newData = auxutil.makeUnsignedList(64)
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
