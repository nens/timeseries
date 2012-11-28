timeseries
==========================================



external adapters
=================

This repository has temporarily become the home for external adapters
for FEWS.

The code for the adapters is in the adapters subfolder. This subfolder
contains all the code needed for the external adapters to work.

To make the version file in the adapters folder atomatically update
after a commit and especially after release, rename post-commit.py to
.git/hooks/post-commit and make sure it is executable.

To use the percentiles script::

    python percentiles <input.xml> <output.xml>

Currently, there are some limitations:
    - Only a common subset of the pixml standard is used
    - Flags on xml input are ignored, output flag is always "0"
    - Formatting of output in xml format values is fixed to .2f


