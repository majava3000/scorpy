#
# shared functionality for example generators
#
# SPDX-License-Identifier: GPL-2.0

from __future__ import print_function
import sys
import argparse
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scorpy.testing import *

# textual report of input vs results
def printAsShortcodes(tracks, outf=sys.stdout):
    labels = []
    shortcodes = []
    for t in tracks:
        labels.append(t.name)
        shortcodes.append(segiterToShortcode(iter(t)))
    maxWidth = max(map(len, labels))
    for idx in range(len(labels)):
        print("{:>{width}}: {}".format(labels[idx], shortcodes[idx], width=maxWidth), file=outf)

# only emit shortcodes (used for manual verification)
MODE_SHORTCODE = 0
# only emit wavedrom (for visual testing)
MODE_WAVEDROM = 1
# emit the include blurb that contains the code block reference and wavedrom
MODE_DOCINC = 2

def getArgs(name):
    ap = argparse.ArgumentParser()
    ap.description = "{} - Generate example for '{}'".format(ap.prog, name)
    ap.add_argument('-o', '--outfile',
                 type=argparse.FileType('w'),
                 default=sys.stdout,
                 help='Name of file where to store results (if not stdout)')
    ap.add_argument('--shortcode',
                   action='store_const',
                   dest='mode',
                   const=MODE_SHORTCODE,
                   default=MODE_DOCINC,
                   help='Generate shortcode output (for logical inspection)')
    ap.add_argument('--wavedrom',
                   action='store_const',
                   dest='mode',
                   const=MODE_WAVEDROM,
                   help='Generate wavedrom output (for visual inspection)')
    ap.add_argument('--docinc',
                   action='store_const',
                   dest='mode',
                   const=MODE_DOCINC,
                   help='Generate include file for Sphinx (default)')
    args = ap.parse_args()
    args.progname = ap.prog
    return args

# args, input_, [r1, r2, r3, r4], 'tester'
def doIt(args, input_, results, label):

    if args.mode == MODE_WAVEDROM:
        print(resultAsWavedrom(input_, results, label), file=args.outfile)
    elif args.mode == MODE_SHORTCODE:
        printAsShortcodes([input_]+results, outf=args.outfile)
    else:
        print(""".. Generated by {}

.. literalinclude:: ../doc_examples/{}
   :language: python
   :dedent: 4
   :linenos:
   :start-after: example-start-here
   :end-before: example-end-here
""".format(args.progname, args.progname), file=args.outfile)

        # wavedrom needs to be indented, otherwise not recognized properly
        wavedrom = resultAsWavedrom(input_, results)
        wavedrom = '\n'.join([ "    "+line for line in wavedrom.splitlines()])
        print(""".. wavedrom::

{}""".format(wavedrom), file=args.outfile)
