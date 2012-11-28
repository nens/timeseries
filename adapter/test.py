#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import copy
import numpy as np
import pixml2 as pixml


class PercentileProcessor(pixml.SeriesProcessor):

    NONE = 0
    SKIP = 1
    ADD = 2
    
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
        parser.add_argument(
            '-p', '--percentiles',
            metavar='PERCENTILES',
            nargs = '*',
            default=[10, 50, 90],
            type=int,
            help='Percentiles to be calculated.',
        )

    def process(self, series):
        """
        """

        # Find some information on leapdays in current series:
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

        if leap:
            # Make every year have a leap day
            resultlength = 366
            serieslength = len(series) + misses
        else:
            # Make every year without a leap day
            resultlength = 365
            serieslength = len(series) - hits

        size = int(np.ceil(serieslength / resultlength) * serieslength)
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
        
        print(i)
        exit()

        import ipdb; ipdb.set_trace() 

        if leap[-366:].any():
            # Result will contain leap day
            length = 366

        else:
            # Result will not contain leap day
            length = 365
            size = int(np.ceil(len(series) / length ) * length)
            table = np.ma.zeros(size, mask=True)
            temp = series.ma[~leap]
            table[:temp.size + 1] = temp[::-1]
            table.shape = (-1, length)

            # Mask leap values, table = compressed()

            
        import ipdb; ipdb.set_trace() 

        if len(series) -  leaps[-1] <= 367:
            length = 366
        else:
            length = 365

        size = 15 * length
        table = np.ma.zeros(size, mask=True)

        
        


        # Make sure our data is square
        length = self.args['length']
        size = int(np.ceil(len(series) / length ) * length)
        table = np.append(
            series.ma[::-1],
            np.ma.array(
                np.zeros(size - len(series)),
                mask=True,
                fill_value=series.ma.fill_value,
            )
        )
        table.shape = (-1 ,length)
        print(table.shape)

        yield series
        return

        for name, parameter in self.PARAMETERS.iteritems():

            if parameter['period'] > height:
                continue

            ma = np.percentile(
                table[0:parameter['period']],
                parameter['percentile'],
                axis=0,
            )[::-1]
            end = series.end
            step = series.step
            start = end - step * (width - 1)
            tree = copy.deepcopy(series.tree)
            for elem in tree.iter():
                if elem.tag.endswith('parameterId'):
                    elem.text = name

            yield pixml.Series(
                tree=tree, start=start, end=end, step=step, ma=ma,
            )


if __name__ == '__main__':
    # exit(pixml.SeriesProcessor().main())
    exit(PercentileProcessor().main())
