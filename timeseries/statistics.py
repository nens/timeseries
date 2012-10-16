#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from xml.etree import ElementTree

import copy
import datetime
import numpy as np
import re
import sys


def indent(elem, level=0):

    """
    from
    http://www.python-forum.org/pythonforum/viewtopic.php?f=19&t=4207
    with fixes.
    """
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            indent(child, level + 1)
        # Last child has different tail
        if not child.tail or not child.tail.strip():
            child.tail = i
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


class Series(object):
    """
    """

    PATTERN = re.compile('\{([^{}]*)\}([^{}]*)')
    TAG = '{{{}}}{}'

    def __init__(self, xml):
        """
        """
        iterator = iter(ElementTree.iterparse(xml, events=('start', 'end')))

        self.root = iterator.next()[1]
        self.ns = self._ns(self.root)

        for parse_event, elem in iterator:
            if parse_event == 'end':
                if elem.tag == self._tag('event'):
                    dt = self._datetime_from_elem(elem)
                    value = elem.attrib['value']
                    self[dt] = value
                    series.remove(elem)
                elif elem.tag == self._tag('header'):
                    self._process_header(elem)
            else:  # parse_event == 'start'
                if elem.tag == self._tag('series'):
                    series = elem  # So we can remove events from it

    def _process_header(self, header):
        self.header = header
        self.start = self._datetime_from_elem(self._find(header, 'startDate'))
        self.end = self._datetime_from_elem(self._find(header, 'endDate'))
        self.step = self._timedelta_from_elem(self._find(header, 'timeStep'))
        self.ma = np.ma.array(
            np.zeros(len(self)),
            mask = True,
            fill_value=-999,
        )

    def _tag(self, tag):
        """ Return namespaced tag. """
        return self.TAG.format(self.ns, tag)

    def _ns(self, elem):
        return re.search(self.PATTERN, elem.tag).group(1)

    def _find(self, elem, tag, ns=None):
        """ find child element. """
        if ns is None:
            ns = self._ns(elem)  # Assume same namespace
        return elem.find(self.TAG.format(ns, tag))

    def _datetime_from_elem(self, elem):
        """ Return python datetime object. """
        return datetime.datetime.strptime(
            '{date} {time}'.format(
                date=elem.attrib['date'],
                time=elem.attrib['time'],
            ),
            '%Y-%m-%d %H:%M:%S',
        )

    def _timedelta_from_elem(self, elem):
        """ Return python timedelta object. """
        td_kwargs = {
            '{}s'.format(elem.attrib['unit']): int(elem.attrib['multiplier']),
        }
        return datetime.timedelta(**td_kwargs)

    def _index(self, dt):
        span = dt - self.start 
        step = self.step
        return int(span.total_seconds() / step.total_seconds())

    def _datetime_from_index(self, index):
        return self.start + index * self.step
    
    def __len__(self):
        """ Return length of timeseries if complete. """
        span = self.end - self.start 
        step = self.step
        return int(span.total_seconds() / step.total_seconds()) + 1

    def __getitem__(self, key):
        """
        self[datetime.datetime] -> value, can be assigned to
        self[0] -> {datetime, value}
        """
        if isinstance(key, datetime.datetime):
            return self.ma[self._index(key)]
        else:
            return self.ma[key]

    def __setitem__(self, key, value):
        """
        directly set the ma by date or index
        """
        if isinstance(key, datetime.datetime):
            self.ma[self._index(key)] = value
        else:
            self.ma[key] = value

    def __iter__(self):
        for i in range(len(self)):
            yield self._datetime_from_index(i), self[i]

    def update_header(self, name):
        """ Update header from self. """
        self._find(self.header, 'startDate').attrib.update(
            date=self.start.strftime('%Y-%m-%d'),
            time=self.start.strftime('%H-%M-%S'),
        )
        self._find(self.header, 'endDate').attrib.update(
            date=self.end.strftime('%Y-%m-%d'),
            time=self.end.strftime('%H-%M-%S'),
        )
        self._find(self.header, 'parameterId').text = name
        
        
    def write_header(self, xmlfile):
        ElementTree.register_namespace('', self.ns)
        xmlfile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        xmlfile.writelines(ElementTree.tostringlist(self.root)[:11])
        # import ipdb; ipdb.set_trace() 


    def write_series(self, xmlfile):
        ElementTree.register_namespace('', self.ns)
        xmlfile.writelines(ElementTree.tostringlist(self.root)[11:-4])
        for dt, value in self:
            event = ElementTree.Element('event')
            event.attrib = dict(
                date=dt.strftime('%Y-%m-%d'),
                time=dt.strftime('%H:%M:%S'),
                value='{:.2f}'.format(value),
                flag='0',
            )
            xmlfile.write('\n        ')
            xmlfile.write(ElementTree.tostring(event))
        xmlfile.write('\n    ')
        xmlfile.writelines(ElementTree.tostringlist(self.root)[-3:-2])

    def write_footer(self, xmlfile):
        ElementTree.register_namespace('', self.ns)
        xmlfile.write('    ')
        xmlfile.writelines(ElementTree.tostringlist(self.root)[-2:])


def percentiles((xml_input_path, xml_output_path)):

    source = Series(xml_input_path)
    
    width = 288
    height = int(np.ceil(len(source) / width))

    ma = np.ma.array(
        np.zeros((width * height)),
        mask=True,
        fill_value=-999,
    )
    ma[len(source) - 1::-1] = source.ma
    ma.shape = height, width
    
    parameters = {
        'a': {'percentile': 10, 'period': 52 * 7}, 
        'b': {'percentile': 10, 'period': 26 * 7}, 
        'c': {'percentile': 10, 'period': 10 * 7}, 
    }
    destination = copy.deepcopy(source)
    
    with open(xml_output_path, 'w') as xmlfile:
        destination.write_header(xmlfile)
        for name, parameter in parameters.iteritems():
            if parameter['period'] > height:
                continue
            destination.start = source.end - 287 * source.step
            destination.end = source.end
            destination.update_header(name=name)
            destination.ma = np.percentile(
                ma[0:parameter['period']],
                parameter['percentile'],
                axis=0,
            )[::-1]
            destination.write_series(xmlfile)
        destination.write_footer(xmlfile)
