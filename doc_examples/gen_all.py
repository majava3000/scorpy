#!/usr/bin/env python
#
# Run all the example generators in this directory in doc-int mode
#
# SPDX-License-Identifier: GPL-2.0

from __future__ import print_function
import sys
import glob
import re
import subprocess

reTargetIsolator = re.compile(r".*/gen_([a-zA-Z0-9_-]+)\.py")

if __name__ == '__main__':
    assert(len(sys.argv) == 3)
    basedir = sys.argv[1]
    outdir = sys.argv[2]

    for path in sorted(glob.iglob(basedir+"/gen_*.py")):
        # isolate the label
        matcho = reTargetIsolator.match(path)
        if matcho is None:
            continue

        label = matcho.group(1)
        if label == 'all':
            # skip ourselves
            continue

        print("Running generator for '%s'" % label)
        r = subprocess.call([path, '--docinc', '-o', "%s/%s.inc" % (outdir, label)])
        assert(r == 0)
