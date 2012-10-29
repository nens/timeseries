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


class Series(object):
    """
    like etree, but:
        events stored as numpy array
        start, stop and step stored as python objects
        closing and opening tags and timezone included.
    """

    def __init__(self, tree, start, stop, step, ma):
        self.start = start
        self.stop = stop
        self.step = step
        self.tree = tree
        self.ma = ma

    def __len__(self):
        """ Return length of timeseries if complete. """
        return self.ma.size

    def __getitem__(self, key):
        """
        self[datetime.datetime] -> value
        self[0] -> {datetime, value}
        """
        if isinstance(key, datetime.datetime):
            return self.ma[self._index(key)]
        else:
            return self.ma[key]

    def __setitem__(self, key, value):
        """
        self[datetime.datetime] = value, or
        self[index] = value
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
            time=self.start.strftime('%H:%M:%S'),
        )
        self._find(self.header, 'endDate').attrib.update(
            date=self.end.strftime('%Y-%m-%d'),
            time=self.end.strftime('%H:%M:%S'),
        )
        self._find(self.header, 'parameterId').text = name
        
        
    def write_header(self, xmlfile):
        ElementTree.register_namespace('', self.ns)
        xmlfile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        xmlfile.writelines(ElementTree.tostringlist(self.root)[:11])


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


def percentiles_old((xml_input_path, xml_output_path)):

    mysource = Series(xml_input_path)
    
    width = 288 * 7
    height = int(np.ceil(len(mysource) / width))

    ma = np.ma.array(
        np.zeros((width * height)),
        mask=True,
        fill_value=-999,
    )
    ma[len(mysource) - 1::-1] = mysource.ma
    ma.shape = height, width
    
    periods = {
        '10w': 10,
        '6m': 26,
        '1j': 52,
    }
    percentiles = (10, 50, 90)
    parameters = {}
    for k, v in periods.items():
        for p in percentiles:
            parameterkey = 'Q.{}.{}'.format(p,k)
            parameters.update({parameterkey: {'percentile': p, 'period': v}})
    
    destination = copy.deepcopy(mysource)
    
    with open(xml_output_path, 'w') as xmlfile:
        destination.write_header(xmlfile)
        # results = {}
        for name, parameter in parameters.iteritems():
            if parameter['period'] > height:
                continue
            destination.start = mysource.end - (7 * 288 - 1) * mysource.step
            destination.end = mysource.end
            destination.update_header(name=name)
            destination.ma = np.percentile(
                ma[0:parameter['period']],
                parameter['percentile'],
                axis=0,
            )[::-1]
            destination.write_series(xmlfile)
            # results.update({name: copy.deepcopy(destination)})
        destination.write_footer(xmlfile)


class SeriesReader(object):
    PATTERN = re.compile('\{([^{}]*)\}([^{}]*)')
    TAG = '{{{}}}{}'

    def __init__(self, xml_input_path):
        self.xml_input_path = xml_input_path

    def read(self):
        """
            timeseries = 
            timezone =
            series parsing:
                series =
                header parsing:
                    parse and remove start, stop, and step.
                    create series
                events parsing:
                    assign event to series object, remove event from tree
            series ended:
                instantiate Series object and yield it.
        """
        iterator = iter(ElementTree.iterparse(
            self.xml_input_path, events=('start', 'end'),
        ))

        for parse_event, elem in iterator:
            if parse_event == 'end' and elem.endswidth('event'):
                pass
            elif parse_event == 'start' and elem.tag.endswith('TimeSeries'):
                self.ns = self._ns(elem)
                import ipdb; ipdb.set_trace() 
            elif parse_event == 'start':
                pass

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
        

class PercentileConverter(object):
    
    PARAMETERS = None

    def _percentile_series(self, series, parameter):
        pass

    def convert(self, series_iterable):
        for series in series_iterable:
            yield series  # Test version
        """
        for series in series_iterable
            parameters = blabla
            for parameter in parameters
            yield _percentile_series(series, parameter)
        """



class SeriesWriter(object):

    def __init__(self, xml_output_path):
        self.xml_output_file = open(xml_output_path, 'w')
        # Write some basic rows

    def write(self, series_iterable):
        for series in series_iterable:
            pass
            # Write series; headers and events
        # Write closing tags
        self.xml_output_file.close()

def percentiles((xml_input_path, xml_output_path)):
    reader = SeriesReader(xml_input_path)
    converter = PercentileConverter()
    writer = SeriesWriter(xml_output_path)

    writer.write(converter.convert(reader.read()))
