#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from xml.etree import ElementTree

import datetime
import numpy as np
import re
import sys


class Series(object):

    PATTERN = re.compile('\{([^{}]*)\}([^{}]*)')
    TAG = '{{{}}}{}'

    def __init__(self, xml_input_path):
        self.xml_input_path = xml_input_path
        empty_tree = self._empty_tree()

        root = empty_tree.getroot()

        series = self._find(root, 'series')
        header = self._find(series, 'header')
        
        self.dt_start = self._datetime(self._find(header, 'startDate'))
        self.dt_end = self._datetime(self._find(header, 'endDate'))
        self.td_step = self._timedelta(self._find(header, 'timeStep'))

        self.array = self._array()

    def _empty_tree(self):
        """
        Return ElementTree, but remove all events. 
        
        Current implementation assumes only one series...
        """
        
        for event, elem in ElementTree.iterparse(self.xml_input_path,
                                                 events=('start', 'end')):
            if event == 'start' and elem.tag.endswith('TimeSeries'):
                root = elem
            if event == 'start' and elem.tag.endswith('series'):
                series = elem
            if event == 'end' and elem.tag.endswith('event'):
                series.remove(elem)
        return ElementTree.ElementTree(root)

    def _ns(self, elem):
        return re.search(self.PATTERN, elem.tag).group(1)

    def _find(self, elem, tag, ns=None):
        """ find child element. """
        if ns is None:
            ns = self._ns(elem)  # Assume same namespace
        return elem.find(self.TAG.format(ns, tag))

    def _datetime(self, elem):
        """ Return python datetime object. """
        return datetime.datetime.strptime(
            '{date} {time}'.format(
                date=elem.attrib['date'],
                time=elem.attrib['time'],
            ),
            '%Y-%m-%d %H:%M:%S',
        )

    def _timedelta(self, elem):
        """ Return python timedelta object. """
        td_kwargs = {
            '{}s'.format(elem.attrib['unit']): int(elem.attrib['multiplier']),
        }
        return datetime.timedelta(**td_kwargs)
    
    def __len__(self):
        """ Return length of timeseries if complete. """
        span = self.dt_end - self.dt_start 
        step = self.td_step
        return int(span.total_seconds() / step.total_seconds()) + 1

    def _array(self):
        """ Return array """
        width = int(3600 * 24 / self.td_step.total_seconds())
        height = int(np.ceil(len(self) / width))
        ma = np.ma.zeros((width, height))
        ma.mask = True
        return ma

    def _index2datetime(self, index):
        """ Return datetime corresponding to index """
        pass

    def _datetime2index(self, dt):
        """ Return index to array corresponding to datetime """
        pass
        


def percentiles((xml_input_path, xml_output_path)):
    series = Series(xml_input_path)
    


