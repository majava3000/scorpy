# Signal Capture OpeRations and Processing with pYthon (scorpy)

Scorpy is a library useful in doing signal capture file processing. In future,
it will be documented with examples, but for now, source is it.

# LICENSE

Scorpy is distributed under the GPLv2 license, except for the median calculation
helper in statistics.py whose license is unknown (see source)

# Scorpy library source code

## core

Contains the core classes and generators

## reader

Contains support code to read capture data from various file formats

## report

Contains reuseable higher level report functions (one ore more)

## statistics

Median calculation support without numpy or python3

## vcd

Contains custom VCD emitting code (for gtkwave visual verification)
