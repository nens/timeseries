#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# version: 0.20.6-3-g6d05f32
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import copy
import numpy as np
import sys

from pixml import Series
from pixml import SeriesReader
from pixml import SeriesWriter


class PercentileConverter(object):

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

    def _percentile_series(self, series):
        """
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

            yield Series(tree=tree, start=start, stop=stop, step=step, ma=ma)

    def convert(self, series_iterable):
        for series in series_iterable:
            for result in self._percentile_series(series):
                yield(result)


def percentiles():
    """
    Uses the PercentileConverter to calculate 10, 50 and 90 percentiles.
    """
    xml_input_path = sys.argv[1]
    xml_output_path = sys.argv[2]

    reader = SeriesReader(xml_input_path)
    converter = PercentileConverter()
    writer = SeriesWriter(xml_output_path)

    writer.write(converter.convert(reader.read()))

    return 0


if __name__ == '__main__':
    exit(percentiles())
