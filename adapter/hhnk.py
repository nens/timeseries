#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import copy
import numpy as np
import pixml


class PercentileProcessor(pixml.SeriesProcessor):

    PERCENTILES = (1, 10, 25, 75, 90, 99)

    PARAMETER = {}
    for percentile in PERCENTILES:
        name = '.{percentile}p'.format(percentile=percentile)
        PARAMETER[name] = percentile

    def add_arguments(self, parser):
        parser.description = 'Create statistics timeseries.'


    def process(self, series):
        """
        Yield percentile timeseries
        """

        # Calculate & write percentiles
        for name, percentile in self.PARAMETER.items():
            try:
                val = np.percentile(series.ma.compressed(), percentile)
                ma = np.ma.array([val] * 2)
            except ValueError:
                ma = np.ma.masked_all(2)

            end = series.end
            start = series.start
            step = end - start
            tree = copy.deepcopy(series.tree)
            for elem in tree.iter():
                if elem.tag.endswith('parameterId'):
                    elem.text += name

            result = pixml.Series(
                tree=tree, start=start, end=end, step=step, ma=ma,
            )
            yield result


if __name__ == '__main__':
    # exit(pixml.SeriesProcessor().main())
    exit(PercentileProcessor().main())
