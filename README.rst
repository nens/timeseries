timeseries
==========================================

To create the percentile executable, do::

    python bootstrap.py
    bin/buildout

Then a statistics file can be created from an pi xml file using::

    bin/percentiles inputxml outputxml

To make the version line in statistics.py automatically update after
a commit and especially after release, rename post-commit.py to
.git/hooks/post-commit and make sure it is executable.
