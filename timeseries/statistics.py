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
        
    def _index(self, dt):
        span = dt - self.start 
        step = self.step
        return int(span.total_seconds() / step.total_seconds())

    def _datetime_from_index(self, index):
        return self.start + index * self.step
        
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


    def _series_from_tree(self, tree):
        """
        Return Series instance from tree, initialized from header.

        Start, stop and step are removed from header.
        """
        remove_from_header = []
        for elem in tree.iter():
            if elem.tag.endswith('header'):
                header = elem
            elif elem.tag.endswith('startDate'):
                start = self._datetime_from_elem(elem)
                remove_from_header.append(elem)
            elif elem.tag.endswith('endDate'):
                stop = self._datetime_from_elem(elem)
                remove_from_header.append(elem)
            elif elem.tag.endswith('timeStep'):
                step = self._timedelta_from_elem(elem)
                remove_from_header.append(elem)

        map(header.remove, remove_from_header)

        size = int((stop - start).total_seconds() / step.total_seconds()) + 1
        ma = np.ma.array(np.zeros(size), mask=True, fill_value=-999)

        return Series(tree=tree, start=start, stop=stop, step=step, ma=ma)

    def read(self):
        """
        Returns a generator of series objects.

        As etree parses the tree, it keeps an internal tree that is not necessarily in sync with the events returned by iterparse.

        Therefore we keep a copy of selected elements of the tree that is used to instantiate the series.
        """
        iterator = iter(ElementTree.iterparse(
            self.xml_input_path, events=('start', 'end'),
        ))

        for parse_event, elem in iterator:
            if parse_event == 'end' and elem.tag.endswith('event'):
                dt = self._datetime_from_elem(elem)
                value = elem.attrib['value']
                result[dt] = value
                wildseries.remove(elem)
            elif parse_event == 'end' and elem.tag.endswith('header'):
                series.append(copy.deepcopy(elem))
                result = self._series_from_tree(copy.deepcopy(tree))
            elif parse_event == 'end' and elem.tag.endswith('series'):
                yield result
                wildtree.remove(wildseries)
                tree.remove(series)
            elif parse_event == 'start' and elem.tag.endswith('series'):
                wildseries = elem
                series = copy.deepcopy(elem)
                tree.append(series)
                map(series.remove, series.getchildren()[:])
            elif parse_event == 'end' and elem.tag.endswith('timeZone'):
                tree.append(copy.deepcopy(elem))
            elif parse_event == 'start' and elem.tag.endswith('TimeSeries'):
                wildtree = elem
                tree = copy.deepcopy(elem)
                map(tree.remove, tree.getchildren()[:])


class SeriesWriter(object):

    def __init__(self, xml_output_path):
        self.xml_output_file = open(xml_output_path, 'w')
        self.initialized = False

    def _register_namespace(self, series):
        """ Register default namespace for etree output. """
        namespace = re.search(
            '\{([^{}]*)\}([^{}]*)',
            series.tree.tag
        ).group(1)
        ElementTree.register_namespace('', namespace)

    def _write_treesection(self, series, part, indent):
        self.xml_output_file.write(
            indent * ' ' +
            ''.join(
                ElementTree.tostringlist(series.tree)[slice(*part)]
            ).strip() +
            '\n'
        )

    def _write_flat_element(self, series, tag, attrib, indent):
        element = ElementTree.Element(tag)
        element.attrib = attrib
        self.xml_output_file.write(
            indent * ' ' + ElementTree.tostring(element) + '\n',
        )
    
    def _write_range_elements(self, series):
        """ Writes the endDate, startDate and timeStep elements. """
        self._write_flat_element(
            series=series, tag='timeStep', attrib=dict(
                unit='second', 
                multiplier=str(series.step.seconds),
            ), indent=12,
        )

        self._write_flat_element(
            series=series, tag='startDate', attrib=dict(
                date=series.start.strftime('%Y-%m-%d'),
                time=series.start.strftime('%H:%M:%S'),
            ), indent=12,
        )

        self._write_flat_element(
            series=series, tag='endDate', attrib=dict(
                date=series.stop.strftime('%Y-%m-%d'),
                time=series.stop.strftime('%H:%M:%S'),
            ), indent=12,
        )

    def _write_series(self, series):
        """ Write series to xmlfile. """

        self._write_treesection(series=series, part=(11, -45), indent=4)
        self._write_range_elements(series)
        self._write_treesection(series=series, part=(-45, -3), indent=12)
        
        for dt, value in series:
            self._write_flat_element(
                series=series, tag='event', attrib=dict(
                    date=dt.strftime('%Y-%m-%d'),
                    time=dt.strftime('%H:%M:%S'),
                    value='{:.2f}'.format(value),
                    flag='0',
                ), indent=8,
            )

        self._write_treesection(series=series, part=(-3, -1), indent=4)

    def _write_lead_out(self, series):
        ElementTree.register_namespace('', self.ns)
        xmlfile.write('    ')
        xmlfile.writelines(ElementTree.tostringlist(self.root)[-2:])
    
    def write(self, series_iterable):
        for series in series_iterable:
            if not self.initialized:
                self._register_namespace(series)
                self.xml_output_file.write(
                    '<?xml version="1.0" encoding="UTF-8"?>\n'
                )
                self._write_treesection(
                    series=series, part=(None, 11), indent=0,
                )

                self.initialized = True
            self._write_series(series)
        if self.initialized:
            self._write_treesection(
                series=series, part=(-1, None), indent=0
            )
        self.xml_output_file.close()


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


def percentiles(*args):
    """
    To be called by the console script.
    
    Since it is not sure if the console script passes the arguments,
    we accept them, but don't use them.
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
