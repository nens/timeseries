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
import datetime


class PercentileProcessor(pixml.SeriesProcessor):

    NONE = 0
    SKIP = 1
    ADD = 2
    
    PERCENTILES = (10, 25, 75, 90)
    PERIOD = 15  # Years
    
    PARAMETER = {}
    for percentile in PERCENTILES:
        name = '.{percentile}p.{period}y'.format(percentile=percentile, period=PERIOD)
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

        # Initialize statistics table based on this information
        if leap:
            # Make every year have a leap day
            resultlength = 366
            serieslength = len(series) + misses
        else:
            # Make every year without a leap day
            resultlength = 365
            serieslength = len(series) - hits

        size = int(np.ceil(serieslength / resultlength) * resultlength)
        table = np.ma.array(np.zeros(size), mask=True)

        # Fill statistics table and remove or add leapdays if necessary.
        action = self.NONE
        i = serieslength - 1
        for d, v in series:
            if d.day == 28 and d.month == 2:
                # Before possible leap day. If leap, signal that 2-29 must be
                # filled, else signal that it must be skipped if it is present.
                action = self.ADD if leap else self.SKIP             
                table[i] = v
                i -= 1
            elif d.day == 29 and d.month == 2:
                # Leap day! Act according to action and reset action.
                if action == self.SKIP:
                    pass
                elif action == self.ADD:
                    table[i] = v
                    i -= 1
                action = self.NONE
            elif d.day == 2 and d.month == 3:
                # After possible leap day. If action is still add,
                # masked must be added for the leap day.
                if action == self.ADD:
                    table[i] = np.ma.masked
                    i -= 1
                table[i] = v
                i -= 1
            else:
                table[i] = v
                i -= 1

        table.shape = (-1, resultlength)
        

        for name, percentile in self.PARAMETER.items():

            if table.shape[0] < self.PERIOD:
                years = table.shape[0]
            else:
                years = self.PERIOD

            ma = np.ma.array(np.zeros(resultlength), mask=True)

            for i in np.arange(ma.size):
                values = table[0:years, i].compressed()
                if len(values):
                    ma[-(i + 1)] = np.percentile(values, percentile)

            end = series.end
            step = series.step
            start = end - step * (resultlength - 1)
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
