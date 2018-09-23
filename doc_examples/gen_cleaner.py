#!/usr/bin/env python
#
# cleaner example generator/code
#
# SPDX-License-Identifier: GPL-2.0

from __future__ import print_function
from common import *

if __name__ == '__main__':
    args = getArgs('cleaner')

    input_ = makeSimpleTrack('input', shortcodeToSegiter("00110.1.0.01.111100000101"))

    # example-start-here
    r = core.cleaner(input_)
    # example-end-here

    r = makeSimpleTrack('result', r)

    doIt(args, input_, [r], 'cleaner')
