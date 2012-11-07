timeseries
==========================================

To create the percentile executable, do::

    python bootstrap.py
    bin/buildout

Then a statistics file can be created from an pi xml file using::

    bin/percentiles inputxml outputxml
