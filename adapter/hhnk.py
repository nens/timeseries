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

    def _glg_ghg_window(self, series):
        """
        Return start, end datetimes corresponding to last window of
        eight hydrologic years before series end.
        """
        end_kwargs = dict(day=31, month=3)

        if series.end.replace(**end_kwargs) < series.end:
            end = series.end.replace(**end_kwargs)
        else:
            end = series.end.replace(year=series.end.year - 1, **end_kwargs)

        return end.replace(year=end.year - 8, month=4, day=1), end

    def _glg_ghg_series(self, series, table):
        """
        Return two Series objects with each only having one value,
        being the glg and the ghg, respectively.

        table must be a table with years as the first dimension and days
        as the second.
        """
        data = {}

        data['ghg'] = np.ma.sort(table, 1, endwith=False)[:,-3:].mean(0).mean()
        data['glg'] = np.ma.sort(table, 1, endwith=True)[:,:3].mean(0).mean()

        for key, value in data.items():
            start = series.end
            end = series.end
            step = series.step
            tree = copy.deepcopy(series.tree)
            if np.ma.is_masked(value):
                ma = np.ma.array([0], mask=True)
            else:
                ma = np.ma.array([value])
            for elem in tree.iter():
                if elem.tag.endswith('parameterId'):
                    elem.text += '.{}'.format(key)

            result =  pixml.Series(
                tree=tree, start=start, end=end, step=step, ma=ma,
            )
            yield result

    def process(self, series):
        """
        Yield percentile timeseries and glg and ghg timeseries
        """

        # Prepare for GLG & GHG
        glg_ghg_window_start, glg_ghg_window_end = self._glg_ghg_window(series)
        glg_ghg_table = np.ma.array(np.zeros((8,24)), mask=True)

        # Find some information on leapdays in current series,
        # At the same time fill glg_ghg_table
        hits = 0 # Misses
        misses = 0   # Leapdays present
        expect = False
        leap = False

        for i, (d, v) in enumerate(series):
            if d.day == 28 and d.month == 2:
                 couplepart = expect = True
            elif d.day == 29 and d.month == 2:
                if len(series) - i < 367:
                    leap = True
                expect = False
                hits += 1
            elif d.day == 1 and d.month == 3 and expect:
                misses += 1
                expect = False
            if d.day == 14 or d.day == 28:
                if d > glg_ghg_window_start and d < glg_ghg_window_end:
                    glg_ghg_day = (d - glg_ghg_window_start).days
                    glg_ghg_i = int(glg_ghg_day / 365.25)
                    glg_ghg_j = int((glg_ghg_day % 365.25) / (365.25 / 24))
                    glg_ghg_table[glg_ghg_i, glg_ghg_j] = v

        # Write GLG & GHG result
        for result in self._glg_ghg_series(series=series, table=glg_ghg_table):
            yield result

        # Calculate & write percentiles
        for name, percentile in self.PARAMETER.items():
            try:
                percentile_val = np.percentile(series.ma.compressed(), percentile)
                ma = np.ma.array([percentile_val]*2)
            except ValueError:
                ma = np.ma.masked_all(2)

            end = series.end
            start = series.start
            step = end - start
            tree = copy.deepcopy(series.tree)
            for elem in tree.iter():
                if elem.tag.endswith('parameterId'):
                    elem.text += name

            result =  pixml.Series(
                tree=tree, start=start, end=end, step=step, ma=ma,
            )
            yield result


if __name__ == '__main__':
    # exit(pixml.SeriesProcessor().main())
    exit(PercentileProcessor().main())