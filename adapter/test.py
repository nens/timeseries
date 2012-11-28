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
        leapindex = np.empty(len(series), dtype=np.bool8)
        leaplist = []
        leapitem = [None, None, None]

        print('tic')
        for i, (d, v) in enumerate(series):
            # Create leapitems
            if d.month == 2 and d.day == 28:
                leapitem[0] = i
            elif d.month == 2 and d.day == 29:
                leapitem[1] = i
            elif d.month == 3 and d.day == 01:
                leapitem[2] = i
                leaplist.append(leapitem)
                leapitem = [None, None, None]

            # Fill leapindex
            leapindex[i] = (
                d.month == 2 and d.day == 29,
            )

        print('tac')
        print(leapindex[-366:].size)

        import ipdb; ipdb.set_trace() 

        if leapindex[-366:].any():
            # Result will contain leap day
            length = 366
            size = int(np.ceil(len(series) / length ) * length)
            table = np.ma.zeros(size, mask=True)

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
