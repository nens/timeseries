#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# version: 0.20.6-3-g6d05f32
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import copy
import glob
import numpy as np
import os
import re
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
        table = np.ma.concatenate([
            series.ma[::-1],
            np.ma.array(np.empty(size - len(series)), mask=True),
        ])
        table.shape = height, width

        for name, parameter in self.PARAMETERS.iteritems():
            # Skip period if not source timeseries not long enough
            if parameter['period'] > height:
                continue

            # Determine the percentiles from the unmasked values
            ma = np.ma.array(np.empty(table.shape[1]), mask=True)
            for i in range(ma.size):
                column = table[0:parameter['period'], i].compressed()
                if column.size:
                    ma[i] = np.percentile(column, parameter['percentile'])
            
            # Create Series object and yield it.
            end = series.end
            step = series.step
            start = end - step * (width - 1)
            tree = copy.deepcopy(series.tree)
            for elem in tree.iter():
                if elem.tag.endswith('parameterId'):
                    elem.text = name

            yield Series(tree=tree, start=start, end=end, step=step, ma=ma)

    def convert(self, series_iterable):
        for series in series_iterable:
            for result in self._percentile_series(series):
                yield(result)


def percentiles_files(xml_input_path, xml_output_path):
    """
    Uses the PercentileConverter to calculate 10, 50 and 90 percentiles.
    """
    reader = SeriesReader(xml_input_path)
    converter = PercentileConverter()
    writer = SeriesWriter(xml_output_path)

    writer.write(converter.convert(reader.read()))


def percentiles():

    xml_input_dir = sys.argv[1]
    xml_output_dir = sys.argv[2]

    # Create output dir if it does not exist.
    if not os.path.exists(xml_output_dir):
        os.mkdir(xml_output_dir)

    for xml_input_path in glob.glob(os.path.join(xml_input_dir, '*.xml')):
        xml_input_file = os.path.basename(xml_input_path)
        xml_output_file = re.sub('^input', 'output', xml_input_file)

        xml_input_path = os.path.join(xml_input_dir, xml_input_file)
        xml_output_path = os.path.join(xml_output_dir, xml_output_file)

        percentiles_files(
            xml_input_path=xml_input_path,
            xml_output_path=xml_output_path,
        )

    return 0


if __name__ == '__main__':
    exit(percentiles())
