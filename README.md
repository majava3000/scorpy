# Signal Capture OpeRations and Processing with PYthon (scorpy)

Scorpy is a library useful in doing signal capture file processing. In future,
it will be documented with examples, but for now, source is it.

# LICENSE

Scorpy is distributed under the GPLv2 license, except for the bundled "six"
helper library whose license is contained in the source file preamble and the
median calculation helper in statistics.py whose license is unknown (see source)

# Scorpy library source code

## core

Contains the core classes and generators

## reader

Contains support code to read capture data from various file formats

## six

In-line copy of six, should be probably removed anyways since not that useful
anymore.

## statistics

Median calculation support without numpy or python3

## vcd

Contains custom VCD emitting code (for gtkwave visual verification)
