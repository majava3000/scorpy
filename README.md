# Signal Capture OpeRations and Processing with pYthon (scorpy)

Scorpy is a library useful in doing signal capture file processing. In future,
it will be documented with examples, but for now, source is it.

# LICENSE

Scorpy is distributed under the GPLv2 license, except for the median calculation
helper in statistics.py whose license is unknown (see source)

# Versioning

Internally, scorpy uses [semver](https://semver.org) compatible scheme. However,
while Scorpy is initial development (major == 0), to guarantees about API
stability or backward compatibility is given. Scorpy is not semver compliant at
this point.

# Scorpy library source code

## auxutil

Utils used by other components but without other dependencies (to break
dependency cycles)

## core

Contains the core utilities and generators. Imports `tracks.*` automatically
into the same namespace.

## reader

Contains support code to read capture data from various file formats

## report

Contains reuseable higher level report functions (one ore more)

## statistics

Median calculation support without numpy or python3

## tracks

Implementations of `core.*Track` classes. No need to pull this in separately.

## vcd

Contains custom VCD emitting code (for gtkwave visual verification)
