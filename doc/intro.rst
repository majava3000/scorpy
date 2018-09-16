Introduction
============

Purpose
-------

Scorpy is a library written in Python to facilitate making programs that do
semantic and statistical analysis based on previously captured "signal data".
Common sources for such signal data are digital logic analyzer captures carrying
signals sampled from physical (hardware) systems, but data can also be generated
by any tool to represent any potentially parallel information in the time domain,
for example using TSV format (tab separated values).

While most digital logic analyzer controlling software includes various protocol
analyzers, scorpy was develop to deal with scenarios where the protocol
analyzers were insufficient, or a higher level systemic information had to be
inferred from the collected data.

Terminology
-----------

Segment
  Scorpy internal data flows use "segments", which is a pair of "duration" and
  "value" that describe a signal condition (value) that exists for specific
  time (duration). This is opposed to the model where a signal value is stored
  for each point in time. Scorpy cannot represent duration of zero, so minimum
  segment duration will always be 1. Duration is unitless, and a `timescale`
  is used to convert into (or from) physical time representation.
Segiter
  Short hand for Segment iterator, which is the internal implementation model
  for most of the useful processing functions in scorpy. Most functions are
  implemented as Python generators. Going through a `segiter` will exhaust the
  contents (just like any iterator), meaning that a segiter can only be "used"
  once.
Clean
  Successive segments produced by an `segiter` have differing values. This is
  when the output is "well formed" and does not contain unnecessary transitions.
Dirty
  Successive segments produced by an `segiter` may have repeating values. Quite
  often, a `segiter` is implemented in a way that provides for multiple
  different use cases, and the generator would be slower if it would collate
  dirty segments together. In some cases such collation is not even desired
  (during synthesis of new states or modes). Conversion of potentially dirty
  data to well-formed clean representation is always possible with
  :py:func:`core.cleaner <scorpy.core.cleaner>`.
Track
  A container of a signal (represented with segments). There are various Tracks
  available in Scorpy to optimize for binary signals (can only represent `0` or
  `1`) and unsigned values of given bit-width. All scorpy tracks implement the
  iteration protocol (e.g., can be used as a source for segiters). When used
  as source for segment iteration but underlying data is not lost (in Track).

Waveform notation
-----------------

When `segiters` in Scorpy contain examples in documentation, the operation of
the examples is often visualized as a waveform graph. In such graphs, the time
domain maps into the discrete "sample" from signal start.

Time before start and after meaningful example signal is always represented as
"high impedance" condition indicating "mid level signal". This is just a
stylistic choice, and should be understood not to represent any internal Scorpy
value or signal value.

Example of a `clean` signal:

.. wavedrom::

    {signal: [
      { name: 'clean', wave: 'z0...10....1..z'},
      ],
      head: { tick: -1 },
      config: { skin: 'narrow' },
    }

The above signal in segment representation:

.. code-block:: python

    [4, 0], [1, 1], [5, 0], [3, 1]

And in change based TSV format with timescale of `1` (unity), and header line (tab=8):

.. code-block:: raw

        timestamp	value
        0	0
        4	1
        5	0
        10	1
        13	1

Example of a `dirty` signal:

.. wavedrom::

    {signal: [
      { name: 'dirty', wave: 'z0.0.10..0.11.z'},
      ],
      head: { tick: -1 },
      config: { skin: 'narrow' },
    }

And again in segment notation:

.. code-block:: python

    [2, 0], [2, 0], [1, 1], [3, 0], [2, 0], [1, 1], [2, 1]

When the `dirty` signal is cleaned, the end result will be the `clean` signal
above.

Development
-----------

Scorpy is available in `Github <https://github.com/majava3000/scorpy>`_ and
issues and development happens there as well.

License
-------

Scorpy is released and distributed under the GNU General Public License (Version
2) (please see the distribution ``LICENSE`` file for details).
