#
# Asserted code to deal with reading input files
#
# Contains:
# - Support for scorpy path spec decoding
# - TSV entries into stream chunks
# - Binary (saleae bin protocol) entries into stream chunks
# - Generic binary tracks creator (bin or tsv)
#
# SPDX-License-Identifier: GPL-2.0

from __future__ import print_function
import sys
import os.path
import re
import struct
import array

# we use xrange internally here, and xPickle. No need to use depend on six.py
# for these.
if sys.version_info[0] >= 3:
  import pickle
  xrange = range
else:
  # python < 3
  import cPickle as pickle

from scorpy import core

####################
# PATH SPEC SUPPORT
####################

# valid formats that we'll recognize
formats = ("TSP8", "TSP16", "TSP32", "TSP64")
# make an re string from all of these
formatSelector = "|".join(formats)
# timebase selector
timebaseSelector = "[0-9]+[kmKM]?"
# channel name selector
chanSelector = "-CH[0-9]+[a-zA-Z_]+[a-zA-Z0-9_]*"

# we'll use a slightly weird way of capturing both the first level and second
# level channel specs (first level encompasses all of them and the second to
# last match will be the last internal match which we'll throw away)
pathSpecSelector = "^(.*?)_SCORPY_(%s)-(%s)((%s)+)\\.(.*)$" % (formatSelector, timebaseSelector, chanSelector)
pathSpecRE = re.compile(pathSpecSelector)

# given timebaseSpec, decode into a number
def decodeTimebaseSpec(s):
    factors = {
        'K': 1000,
        'M': 1000000,
    }
    unitChar = s[-1].upper()
    if unitChar in factors:
        return int(s[:-1]) * factors[unitChar]
    else:
        return int(s)

# isolate the important bits from the channel selector
chanSpecRE = re.compile(r"^-CH([0-9]+)(.*)$")

# given channel spec, return the channel number and name
def decodeChannelSpec(s):
    comps = chanSpecRE.match(s).groups()
    assert(len(comps) == 2)
    return (int(comps[0]), comps[1])

# given list of channel specs, check for:
# - overlapping channel IDs
# - overlapping channel names
# - too high channel IDs
# TODO: In theory, the TSP spec will set up another maxChannelID as well, at
#       least for TSP8
def chansAreValid(chans, maxChannelID=15):
    chanIDs = set()
    chanNames = set()
    for id, name in chans:
        if id > maxChannelID:
            print("ERROR(PATHSPEC): Max channel ID is %u, %u was specified" % (
                maxChannelID, id))
            return False
        if id in chanIDs:
            print("ERROR(PATHSPEC): Channel ID %u specified multiple times" % id)
            return False
        if name in chanNames:
            print("ERROR(PATHSPEC): Channel name %s specified multiple times" % name)
            return False
        chanIDs.add(id)
        chanNames.add(name)

    return True

# given path, returns a tuple of (mode, baserate|None, (chIdx, chName), (chIdx, chName), ..)
# from the given name (using scorpy path encoded spec)
# returns None if not detected.
def decodePathSpec(p):
    # identification done on basename part only
    base = os.path.basename(p)
    # print("base:", base)
    # print("pathSpecSelector: '%s'" % pathSpecSelector)
    matcho = pathSpecRE.match(base)
    if matcho == None:
        return None
    # we have something, time to decode stuff
    # separate things that we'll need later
    comps = matcho.groups()[1:]
    ret = []
    ret.append(comps[0])
    ret.append(decodeTimebaseSpec(comps[1]))
    channelSpecsStr = comps[2] # we ignore the trailing internal match anyway
    chans = [ decodeChannelSpec(x) for x in re.findall(chanSelector, channelSpecsStr) ]
    # check that the channel spec is sane
    if not chansAreValid(chans):
        return None
    ret += sorted(chans)
    # print(channelSpecs)
    ret.append(comps[-1])
    # suffix = comps[-1]
    # print(matcho.groups())
    # print(formatSpec, timebase, channelSpecs, suffix)

    return tuple(ret)

####################
# STREAM CONVERTERS
####################

# return TSV values in parsed list of (absTS, val-1-int, val-2-int, ...)
def tsvToStream(f):
    # we do our own binvalue to int converter. this is the fastest method with
    # map with 2.7
    vMap = {
    '0': 0,
    '1': 1,
    }

    for l in f:
        comps = l.rstrip().split()
        ts = long(comps[0])
        values = map(vMap.get, comps[1:])
        yield (ts,) + tuple(values)

# iterator that runs struct decoder on fixed size chunks from file
def structReader(f, fmtSpec):
    elSize = struct.calcsize(fmtSpec)
    reading = True
    while True:
        # read the next chunk if possible
        chunk = f.read(elSize)
        if len(chunk) == 0:
            # EOF
            break
        # underlying file is malsized probably, since otherwise if the input
        # file is buffered, this should always be true
        assert(len(chunk) == elSize)
        yield struct.unpack(fmtSpec, chunk)

    # EOF encountered
    # do nothing (return None to mark end of iterator)

# iterator that returns the content from binary format in an abs-ts + abs-value
# list. note that since spec may select channels where there's no activity, this
# might return consecutive identical value sets (the changes are not compatured
# by the selected channels in spec)
def binaryToStream(f, spec):

    # make the struct format spec based on the decoding type
    typeMap = {
        'TSP8':  'B',
        'TSP16': 'H',
        'TSP32': 'I',
        'TSP64': 'Q',
    }
    if spec[0] not in typeMap:
        print("ERROR: Don't know how to decode '%s'" % spec[0], file=sys.stderr)
        return

    # number of channels to extract from the data (0=type, 1=timebase, -1=suffix)
    channelCount = len(spec) - 3
    # # isolation masks for each channel (spec order, using channel IDs)
    # channelIsolators = tuple( 1 << x[0] for x in spec[2:-1])
    # isolators are shift counts of getting the channel data to the lsb bit
    # before masking with one
    channelIsolators = tuple( x[0] for x in spec[2:-1] )
    # print("channelIsolators: %s" % str(channelIsolators))
    assert(channelCount == len(channelIsolators))

    fmtSpec = "<Q%s" % typeMap[spec[0]]
    #print("fmtSpec='%s'" % fmtSpec)
    #elSize = struct.calcsize(fmtSpec)
    #print("fmtSpec='%s', elSize=%u" % (fmtSpec, elSize))
    # split up the data from the file into structs decoding them one element at
    # a time
    for ts, combinedV in structReader(f, fmtSpec):
        # run the combinedV against each of the isolator to get the values
        # using isolator masks is a bit problematic since we'd need to get the
        # results back into integers and best we can do is bools. so instead we
        # use shift counts and additional and to get the lsb only. probably not
        # as efficient, but can't be helped really
        # v = tuple( ((combinedV & x) != 0) for x in channelIsolators)
        yield (ts,) + tuple( ((combinedV >> x) & 1) for x in channelIsolators )

###########################
# TOP-LEVEL FORMAT PARSERS
###########################

def readTSV(path, timebase=500000000):

    # rely on the underlying python to do the right thing wrt to newlines
    f = open(path, "r")
    # deal with the header separately
    header = f.readline().rstrip().split()
    if len(header) < 2 or header[0] != "Sample":
        print("ERROR: Incompatible header (use tabs and include header)", file=sys.stderr)
        sys.exit(1)
    channelCount = len(header)-1

    # isolate channel names
    chNames = map(lambda x: x.strip(), header[1:])
    # verify that no names are duplicates
    if len(chNames) != len(set(chNames)):
        print("ERROR: Duplicate track names detected", file=sys.stderr)
        sys.exit(1)

    # use the generic multitrack creating helper
    return parseIntoBinaryTracks(tsvToStream(f), chNames, timebase)

def readBinary(path):
    spec = decodePathSpec(path)
    if spec == None:
        print("ERROR: Failed to decode scorpy namespec from '%s'" % path, file=sys.stderr)
        return None
    # print("scorpy path spec: '%s'" % str(spec))

    f = open(path, "rb")
    stream = binaryToStream(f, spec)
    # isolate the channel names (in spec order, which is also id order)
    chNames = tuple( x[1] for x in spec[2:-1] )

    # use the generic multitrack generator
    return parseIntoBinaryTracks(stream, chNames, spec[1])

# GCCF parser does not reuse the same logic as the TSV/binary readers
def readGCCF(path):
    f = open(path, "rb")
    p = pickle.Unpickler(f)
    # common header first (carries channel count)
    common = p.load()
    assert(common.setdefault('channelcount', 0) > 0)

    # descriptors are regular dictionaries, count must match
    descriptors = p.load()
    assert(len(descriptors) == common['channelcount'])

    # construct the supported array element formats
    formatString = "Bf"
    # convert this into a tuple of format typecodes and itemsizes in this
    # environment
    supportedFormats = map(lambda x: (x, array.array(x).itemsize), formatString)

    # check for descriptor validity
    names = set()
    for desc in descriptors:
        #print(" descr: %r" % desc)
        assert(desc.setdefault('samplecount', 0) > 0)
        assert(desc.setdefault('format', None) in supportedFormats )
        assert(desc.setdefault('name', None) != None)
        assert(desc.setdefault('timebase', 0) > 0)
        # check against duplicate names
        n = desc['name']
        assert(n not in names)
        names.add(n)

    # will contain the tracks to return
    track = {}

    # load the data, and create the suitable track objects
    for desc in descriptors:
        channelByteCount = desc['samplecount'] * desc['format'][1]
        formatCode = desc['format'][0]
        d = array.array(formatCode)
        d.fromstring(f.read(channelByteCount))
        assert(len(d) == desc['samplecount'])
        # print("'%s': %r .. %r [timebase=%u, count=%u]" % (desc['name'], d[0], d[-1], desc['timebase'], len(d)))
        if formatCode == 'B':
            # start with an empty track (defaults used: no data, no initial)
            bt = core.BinaryTrack(desc['name'],
                                  desc['timebase'])
            # set data using a helper iterator (duration will be updated automatically)
            bt.setSegments(core.segiterFromIterable(d))
            # print(bt)
            track[desc['name']] = bt
        elif formatCode == 'f':
            ft = core.FloatTrack(desc['name'],
                                 desc['timebase'],
                                 d)
            track[desc['name']] = ft
        else:
            print("reader.GCCF: unsupported track type '%s'" % formatCode)

    # at this point f should return EOF
    assert(len(f.read()) == 0)
    assert(len(track) > 0)

    return track

def readCapture(path):
    if path.endswith('.tsv'):
        return readTSV(path)
    elif path.endswith('.bin'):
        return readBinary(path)
    elif path.endswith('.gccf'):
        return readGCCF(path)
    return None

#####################################
# GENERIC PARSERS INTO BINARY TRACKS
#####################################

# given iterator that returns absts, val1, val2, val3 stream, construct new
# BinaryTracks using the additional information about the tracks
# chNames: ordered list of track names to create (reader needs to be setup to
#  return values in this order). Used as track count that is generated in the
#  end
def parseIntoBinaryTracks(stream, chNames, timebase):

    channelCount = len(chNames)
    channelIndices = tuple(range(channelCount))

    # load initial values and verify ts at start is zero
    icomps = next(stream)
    initialTS = icomps[0]
    # print("initialTS=%d" % initialTS)
    # we support non-zero initial value, we just assume that time starts there
    # (should we do this btw? TODO: pros and cons for both approaches here)

    # prepare the data for tracking
    chLastTimestamp = [initialTS] * channelCount
    # print("chLastTimestamp=%s" % chLastTimestamp)

    # all channels start at initial values
    chLastValue = list(icomps[1:])
    # but also store the inital values for later, when we create channels
    chInitials = icomps[1:]

    # use list comprehension to make a tuple of empty lists, attempt to get 64
    # bits (won't work on non LP64 systems with <3.3 python)
    chData = tuple( [ core.makeUnsignedList(64) for _ in xrange(channelCount)] )

    # we need to access this to final closing to the channels
    ts = None

    for comps in stream:
        ts = comps[0]
        values = comps[1:]

        for chIdx in channelIndices:
            v = values[chIdx]
            if v != chLastValue[chIdx]:
                # time to update
                deltaTS = ts - chLastTimestamp[chIdx]
                chData[chIdx].append(deltaTS)
                chLastValue[chIdx] = v
                chLastTimestamp[chIdx] = ts

    # create tracks using the collected chDatas and set their duration to the last ts+1
    # TODO: Infact, we don't know what the original capture time was. Change
    #       based TSV cannot communicate this anyway. Does the binary output?
    track = {}
    for chIdx in channelIndices:
        trackName = chNames[chIdx]
        bt = core.BinaryTrack(trackName,      # name
                         timebase,            # timebase
                         chInitials[chIdx],   # initial
                         chData[chIdx],       # data
                         ts+1-initialTS)      # duration
        track[trackName] = bt

    # validity checks (mainly last value check)
    for chIdx in channelIndices:
        # check for validity (2. identify last value and compared to
        # last known one). Note that len is one over the last index, and the
        # formula is for the index (so we don't add +1 here, since it's already
        # included in len())
        lastVal = chInitials[chIdx] ^ (len(chData[chIdx]) % 2)
        if lastVal != chLastValue[chIdx]:
            print(" !! lastval=%u, last-val=%u" % (lastVal, chLastValue[chIdx]), file=sys.stderr)

    return track
