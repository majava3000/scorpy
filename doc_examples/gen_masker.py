#!/usr/bin/env python
#
# masker example generator/code
#
# SPDX-License-Identifier: GPL-2.0

from __future__ import print_function
from common import *

if __name__ == '__main__':
    name = 'masker'
    args = getArgs(name)

    v = 118

    data = makeSimpleTrack('data', shortcodeToSegiter("A..B..C..D"))
    mask = makeSimpleTrack('mask', shortcodeToSegiter("0.1....0.."))

    # example-start-here
    r = core.masker(data, mask, v)
    # example-end-here

    doIt(args, [data, mask], [r], name, useNarrow=True)
