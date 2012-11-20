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
    
    PERIODS = {
        '10w': 10,
        '6m': 26,
        '1j': 52,
    }
    PERCENTILES = (10, 50, 90)
    PARAMETERS = {}
    for k, v in PERIODS.items():
        for p in PERCENTILES:
            parameterkey = 'Q.{}.{}'.format(p, k)
            PARAMETERS.update({
                parameterkey: {'percentile': p, 'period': v},
            })
    
    def add_arguments(self, parser):
        parser.description = 'Create statistics timeseries.'

    def process(self, series):
        """
        Copied from percentile.py
        """
        # Create and fill an array with shape (weeks, steps-per-week)
        width = int(3600 * 24 * 7 / series.step.total_seconds())
        height = int(np.ceil(len(series) / width))
        size = height * width
        table = np.append(
            series.ma[::-1],
            np.ma.array(
                np.zeros(size - len(series)),
                mask=True,
                fill_value=series.ma.fill_value,
            )
        )
        table.shape = height, width

        for name, parameter in self.PARAMETERS.iteritems():
            if parameter['period'] > height:
                continue

            ma = np.percentile(
                table[0:parameter['period']],
                parameter['percentile'],
                axis=0,
            )[::-1]
            stop = series.stop
            step = series.step
            start = stop - step * (width - 1)
            tree = copy.deepcopy(series.tree)
            for elem in tree.iter():
                if elem.tag.endswith('parameterId'):
                    elem.text = name

            yield pixml.Series(
                tree=tree, start=start, stop=stop, step=step, ma=ma,
            )


if __name__ == '__main__':
    exit(PercentileProcessor().main())
