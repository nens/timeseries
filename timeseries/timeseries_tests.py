#!/usr/bin/python
# -*- coding: utf-8 -*-
#******************************************************************************
#
# This file is part of the lizard_waterbalance Django app.
#
# The lizard_waterbalance app is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# the lizard_waterbalance app.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2010 Nelen & Schuurmans
#
#******************************************************************************
#
# Initial programmer: Mario Frasca
# Initial date:       2011-10-10
#
#******************************************************************************

from unittest import TestCase
from timeseries import TimeSeries
from timeseries import str_to_datetime
from timeseries import _element_with_text
import pkg_resources
from datetime import datetime, timedelta
from xml.dom.minidom import Document
from xml.dom.minidom import Element
from nens import mock
import os
import logging


class django:
    """sort of namespace"""

    class QuerySet:
        def __init__(self, content):
            self.content = [WB.Series(i, self) for i in content]
            self.current = -1
            self.filtered = []

        def count(self):
            return len(self.content)

        def __iter__(self):
            return self

        def next(self):
            try:
                self.current += 1
                return self.content[self.current]
            except IndexError:
                raise StopIteration


class WB:
    """contains water balance mock objects"""

    class Series:
        def __init__(self, content, qs):
            self.qs = qs
            self.timestep = WB.LP_Object('')
            self.location = WB.LP_Object(content['location'])
            self.parameter = WB.LP_Object(content['parameter'], 'm3/h')
            self.event_set = WB.EventSet(content['events'], qs)

    class LP_Object:
        def __init__(self, content, unit=None):
            self.id = content
            self.unit = unit
            if content is not None and unit is not None:
                self.groupkey = WB.LP_Object(None, unit)

    class Event:
        def __init__(self, tvfc):
            self.timestamp, self.value, self.flag, self.comment = tvfc

    class EventSet:
        def __init__(self, content, qs):
            self.qs = qs
            self.content = content
            self.current = -1
            pass

        def __iter__(self):
            return self

        def next(self):
            try:
                self.current += 1
                return WB.Event(self.content[self.current])
            except IndexError:
                raise StopIteration

        def all(self):
            return self

        def filter(self, *args, **kwargs):
            self.qs.filtered.append((args, kwargs))
            return self


class TimeSeriesTestSuite(TestCase):
    def test_001(self):
        """can we create an empty TimeSeries object?
        """

        TimeSeries()

    def test_002(self):
        """can we create a TimeSeries object with a couple of properties?
        """

        obj = TimeSeries(location_id='loc', parameter_id='par')
        self.assertEqual('loc', obj.location_id)
        self.assertEqual('par', obj.parameter_id)

    def test_010(self):
        'can we initialize a set of TimeSeries objects from a PI file?'

        ## please define a test case
        pass

    def test_020(self):
        'can we ask for the events of an eventless time series?'

        obj = TimeSeries(location_id='loc', parameter_id='par')
        self.assertEqual(0, len(obj.get_events()))

    def test_021(self):
        'start and end of an eventless time series is 1970-01-01'

        obj = TimeSeries(location_id='loc', parameter_id='par')
        self.assertEqual(datetime(1970, 1, 1), obj.get_start_date())
        self.assertEqual(datetime(1970, 1, 1), obj.get_end_date())

    def test_022(self):
        'start and end of a time series with events'

        obj = TimeSeries(location_id='loc', parameter_id='par')
        d1 = datetime(1979, 3, 15, 9, 35)
        d3 = datetime(1979, 4, 12, 9, 35)
        d2 = datetime(1979, 5, 15, 9, 35)
        obj[d1] = 1.23
        obj[d3] = 0.23
        obj[d2] = -3.01
        self.assertEqual(d1, obj.get_start_date())
        self.assertEqual(d2, obj.get_end_date())

    def test_023(self):
        'getting events of a non empty time series'

        obj = TimeSeries(location_id='loc', parameter_id='par')
        d1 = datetime(1979, 3, 15, 9, 35)
        d3 = datetime(1979, 4, 12, 9, 35)
        d2 = datetime(1979, 5, 15, 9, 35)
        obj[d1] = 1.23
        obj[d3] = 0.23
        obj[d2] = -3.01
        self.assertEqual(3, len(obj.get_events()))
        self.assertEqual(2, len(obj.get_events(d3)))
        self.assertEqual(2, len(obj.get_events(d1, d3)))

    def test_024(self):
        'getting events of a eventless time series'

        obj = TimeSeries(location_id='loc', parameter_id='par')
        d1 = datetime(1979, 3, 15, 9, 35)
        d3 = datetime(1979, 4, 12, 9, 35)
        self.assertEqual(0, len(obj.get_events()))
        self.assertEqual(0, len(obj.get_events(d3)))
        self.assertEqual(0, len(obj.get_events(d1, d3)))

    def test_042(self):
        'using deprecated events function'

        root = logging.getLogger()
        handler = mock.Handler()
        root.addHandler(handler)
        obj = TimeSeries(location_id='loc', parameter_id='par')
        d1 = datetime(1979, 3, 15, 9, 35)
        d3 = datetime(1979, 4, 12, 9, 35)
        d2 = datetime(1979, 5, 15, 9, 35)
        obj[d1] = 1.23
        obj[d3] = 0.23
        obj[d2] = -3.01
        self.assertEqual(3, len(list(obj.events())))
        self.assertEqual(2, len(list(obj.events(d3))))
        self.assertEqual(2, len(list(obj.events(d1, d3))))
        self.assertEqual(3, len(handler.content))
        self.assertEqual("timeseries.timeseries|WARNING|Call to deprecated function events.",
                         handler.content[0])
        root.removeHandler(handler)

    def test_100(self):
        '''object can be seen as a dictionary (defines __setitem__ and
        __getitem__)'''

        obj = TimeSeries(location_id='loc', parameter_id='par')
        d1 = datetime(1979, 3, 15, 9, 35)
        d3 = datetime(1979, 4, 12, 9, 35)
        d2 = datetime(1979, 5, 15, 9, 35)
        obj[d1] = 1.23  # executing __setitem__
        obj[d3] = 0.23
        obj[d2] = -3.01

        [self.assertEquals(obj._events[d], obj[d]) for d in obj._events.keys()]

    def test_110(self):
        'add_value is defined and equal to __setitem__'

        obj = TimeSeries(location_id='loc', parameter_id='par')
        d1 = datetime(1979, 3, 15, 9, 35)
        ## setting
        obj.add_value(d1, 1.23)
        ## checking
        self.assertEquals(obj._events[d1], obj[d1])

    def test_111(self):
        'get_event is defined and equal to __getitem__'

        obj = TimeSeries(location_id='loc', parameter_id='par')
        d1 = datetime(1979, 3, 15, 9, 35)
        ## setting
        obj[d1] = 1.23
        ## checking
        self.assertEquals(obj._events[d1], obj.get_event(d1))

    def test_112(self):
        'get_value is defined returns only value, no flags'

        obj = TimeSeries(location_id='loc', parameter_id='par')
        d1 = datetime(1979, 3, 15, 9, 35)
        ## setting
        obj[d1] = 1.23
        ## checking
        self.assertEquals(obj._events[d1][0], obj.get_value(d1))

    def test_115(self):
        'can use .get with default value'

        obj = TimeSeries(location_id='loc', parameter_id='par')
        d1 = datetime(1979, 3, 15, 9, 35)
        obj.add_value(d1, 1.23)  # executing __setitem__
        ## finds values that are there
        [self.assertEquals(obj._events[d], obj.get(d))
         for d in obj._events.keys()]
        d2 = datetime(1979, 5, 15, 9, 35)
        ## returns default value if event is not there
        self.assertEquals(None, obj.get(d2))

    def test_200(self):
        'represent empty TimeSeries as Element'

        obj = TimeSeries(location_id='loc', parameter_id='par')
        doc = Document()
        current = obj._as_element(doc)
        self.assertTrue(isinstance(current, Element))
        self.assertEquals('series', current.tagName)
        childElements = [i
                         for i in current.childNodes
                         if i.nodeType != i.TEXT_NODE]
        self.assertEquals(1, len(childElements))
        self.assertEquals(['header'], [i.tagName for i in childElements])
        self.assertEquals({}, dict(current.attributes))

    def test_201(self):
        'represent TimeSeries with two events as Element'

        obj = TimeSeries(location_id='loc', parameter_id='par')
        obj[datetime(1980, 11, 23, 19, 35)] = -1
        doc = Document()
        current = obj._as_element(doc)
        self.assertTrue(isinstance(current, Element))
        self.assertEquals('series', current.tagName)
        childElements = [i
                         for i in current.childNodes
                         if i.nodeType != i.TEXT_NODE]
        self.assertEquals(2, len(childElements))
        self.assertEquals(['header', 'event'],
                          [i.tagName for i in childElements])
        self.assertEquals({}, dict(current.attributes))


class TestUtilityFunctions(TestCase):
    def test000(self):
        'str_to_datetime, utc'
        self.assertEquals(datetime(2010, 04, 03),
                          str_to_datetime("2010-04-03", "00:00:00"))

    def test002(self):
        'str_to_datetime, negative offset'
        self.assertEquals(datetime(2010, 04, 03, 4),
                          str_to_datetime("2010-04-03", "00:00:00", -4))

    def test004(self):
        'str_to_datetime, positive offset'
        self.assertEquals(datetime(2010, 04, 03, 11),
                          str_to_datetime("2010-04-03", "12:00:00", 1))
        self.assertEquals(datetime(2012, 02, 29, 20),
                          str_to_datetime("2012-03-01", "00:00:00", 4))

    def test100(self):
        '_element_with_text without text, without attributes'

        doc = Document()
        obj = _element_with_text(doc, 'test')
        self.assertTrue(isinstance(obj, Element))
        self.assertEquals('test', obj.tagName)
        self.assertEquals([], obj.childNodes)
        self.assertEquals({}, dict(obj.attributes))

    def test101(self):
        '_element_with_text without text, with attributes'

        doc = Document()
        obj = _element_with_text(doc, 'test', attr={'a': 2})
        self.assertTrue(isinstance(obj, Element))
        self.assertEquals('test', obj.tagName)
        self.assertEquals([], obj.childNodes)
        self.assertEquals('2', obj.getAttribute('a'))

    def test102(self):
        '_element_with_text with text, without attributes'

        doc = Document()
        obj = _element_with_text(doc, 'test', "attr={'a': 2}")
        self.assertTrue(isinstance(obj, Element))
        self.assertEquals('test', obj.tagName)
        self.assertEquals(1, len(obj.childNodes))
        self.assertEquals("attr={'a': 2}",
                          ''.join(i.nodeValue for i in obj.childNodes))


class TimeSeriesInput(TestCase):

    def setUp(self):
        self.testdata = pkg_resources.resource_filename(
            "timeseries", "testdata/")

    def test000(self):
        'TimeSeries.as_dict accepts file name, returns dictionary'
        obj = TimeSeries.as_dict(self.testdata + "read.PI.timezone.2.xml")
        self.assertTrue(isinstance(obj, dict))

    def test005(self):
        'TimeSeries.as_dict accepts open stream, returns dictionary'
        stream = file(self.testdata + "read.PI.timezone.2.xml")
        obj = TimeSeries.as_dict(stream)
        self.assertTrue(isinstance(obj, dict))

    def test007(self):
        'TimeSeries.as_dict receiving unrecognized object, returns None'
        self.assertEquals(None, TimeSeries.as_dict(None))
        self.assertEquals(None, TimeSeries.as_dict(123))
        self.assertEquals(None, TimeSeries.as_dict(set()))

    def test010(self):
        '''result of TimeSeries.as_dict is indexed on locationId
        parameterId 2-tuples'''
        obj = TimeSeries.as_dict(self.testdata + "read.PI.timezone.2.xml")
        self.assertEquals(set([("600", "P1201"), ("600", "P2504")]),
                          set(obj.keys()))
        self.assertTrue(isinstance(obj[("600", "P1201")], TimeSeries))
        self.assertTrue(isinstance(obj[("600", "P2504")], TimeSeries))

    def test100(self):
        'TimeSeries.as_dict reads events of series (a)'
        obj = TimeSeries.as_dict(self.testdata + "read.PI.timezone.2.xml")
        ts = obj[("600", "P1201")]
        self.assertEquals([
                (str_to_datetime("2010-04-03", "00:00:00", 2), (20, 0, '')),
                (str_to_datetime("2010-04-04", "00:00:00", 2), (22, 0, '')),
                (str_to_datetime("2010-04-05", "00:00:00", 2), (17, 0, '')),
                (str_to_datetime("2010-04-06", "00:00:00", 2), (20, 0, '')),
                (str_to_datetime("2010-04-07", "00:00:00", 2), (21, 0, '')),
                (str_to_datetime("2010-04-08", "00:00:00", 2), (22, 0, '')),
                (str_to_datetime("2010-04-09", "00:00:00", 2), (24, 0, '')),
                (str_to_datetime("2010-04-10", "00:00:00", 2), (24, 0, '')),
                (str_to_datetime("2010-04-11", "00:00:00", 2), (24, 0, '')),
                (str_to_datetime("2010-04-12", "00:00:00", 2), (22, 0, '')), ],
                          ts.get_events())

    def test101(self):
        'TimeSeries.as_dict reads events of series (b)'
        obj = TimeSeries.as_dict(self.testdata + "read.PI.timezone.2.xml")
        ts = obj[("600", "P2504")]
        self.assertEquals([
                (str_to_datetime("2010-04-05", "00:00:00", 2), (17, 0, '')),
                (str_to_datetime("2010-04-08", "00:00:00", 2), (22, 0, '')),
                (str_to_datetime("2010-04-10", "00:00:00", 2), (24, 0, '')), ],
                          ts.get_events())

    def test102(self):
        """TimeSeries.as_dict reads events of series (c)

        This time series contains two values that should be ignored.

        """
        obj = TimeSeries.as_dict(self.testdata + "read.PI.timezone.missVal.xml")
        ts = obj[("600", "P1212")]
        self.assertEquals([
                (str_to_datetime("2010-04-03", "00:00:00", 2), (20, 0, '')),
                (str_to_datetime("2010-04-04", "00:00:00", 2), (22, 0, '')),
                (str_to_datetime("2010-04-05", "00:00:00", 2), (17, 0, '')),
                (str_to_datetime("2010-04-06", "00:00:00", 2), (20, 0, '')),
                (str_to_datetime("2010-04-07", "00:00:00", 2), (21, 0, '')),
                (str_to_datetime("2010-04-09", "00:00:00", 2), (24, 0, '')),
                (str_to_datetime("2010-04-11", "00:00:00", 2), (24, 0, '')),
                (str_to_datetime("2010-04-12", "00:00:00", 2), (22, 0, '')), ],
                          ts.get_events())

    def test103(self):
        """TimeSeries.as_dict reads events of series (d)

        This time series contains two values that should be ignored.

        """
        obj = TimeSeries.as_dict(self.testdata + "read.PI.timezone.no.missVal.xml")
        ts = obj[("600", "P1212")]
        self.assertEquals([
                (str_to_datetime("2010-04-03", "00:00:00", 2), (20, 0, '')),
                (str_to_datetime("2010-04-04", "00:00:00", 2), (22, 0, '')),
                (str_to_datetime("2010-04-05", "00:00:00", 2), (17, 0, '')),
                (str_to_datetime("2010-04-06", "00:00:00", 2), (20, 0, '')),
                (str_to_datetime("2010-04-07", "00:00:00", 2), (21, 0, '')),
                (str_to_datetime("2010-04-08", "00:00:00", 2), (-999.0, 0, '')),
                (str_to_datetime("2010-04-09", "00:00:00", 2), (24, 0, '')),
                (str_to_datetime("2010-04-10", "00:00:00", 2), (-999.0, 0, '')),
                (str_to_datetime("2010-04-11", "00:00:00", 2), (24, 0, '')),
                (str_to_datetime("2010-04-12", "00:00:00", 2), (22, 0, '')), ],
                          ts.get_events())
    def test110(self):
        'TimeSeries.as_dict reads events of series (a)'
        obj = TimeSeries.as_dict(self.testdata + "read.PI.timezone.2.xml")
        ts = obj[("600", "P1201")]
        self.assertEquals([
                (str_to_datetime("2010-04-03", "00:00:00", 2), 20),
                (str_to_datetime("2010-04-04", "00:00:00", 2), 22),
                (str_to_datetime("2010-04-05", "00:00:00", 2), 17),
                (str_to_datetime("2010-04-06", "00:00:00", 2), 20),
                (str_to_datetime("2010-04-07", "00:00:00", 2), 21),
                (str_to_datetime("2010-04-08", "00:00:00", 2), 22),
                (str_to_datetime("2010-04-09", "00:00:00", 2), 24),
                (str_to_datetime("2010-04-10", "00:00:00", 2), 24),
                (str_to_datetime("2010-04-11", "00:00:00", 2), 24),
                (str_to_datetime("2010-04-12", "00:00:00", 2), 22), ],
                          ts.get_values())

    def test111(self):
        'TimeSeries.as_dict reads events of series (b)'
        obj = TimeSeries.as_dict(self.testdata + "read.PI.timezone.2.xml")
        ts = obj[("600", "P2504")]
        self.assertEquals([
                (str_to_datetime("2010-04-05", "00:00:00", 2), 17),
                (str_to_datetime("2010-04-08", "00:00:00", 2), 22),
                (str_to_datetime("2010-04-10", "00:00:00", 2), 24), ],
                          ts.get_values())

    def test112(self):
        """TimeSeries.as_dict reads events of series (c)

        This time series contains two values that should be ignored.

        """
        obj = TimeSeries.as_dict(self.testdata + "read.PI.timezone.missVal.xml")
        ts = obj[("600", "P1212")]
        self.assertEquals([
                (str_to_datetime("2010-04-03", "00:00:00", 2), 20),
                (str_to_datetime("2010-04-04", "00:00:00", 2), 22),
                (str_to_datetime("2010-04-05", "00:00:00", 2), 17),
                (str_to_datetime("2010-04-06", "00:00:00", 2), 20),
                (str_to_datetime("2010-04-07", "00:00:00", 2), 21),
                (str_to_datetime("2010-04-09", "00:00:00", 2), 24),
                (str_to_datetime("2010-04-11", "00:00:00", 2), 24),
                (str_to_datetime("2010-04-12", "00:00:00", 2), 22), ],
                          ts.get_values())

    def test200(self):
        'TimeSeries.as_list reads file given its name'
        obj = TimeSeries.as_list(self.testdata + "read.PI.timezone.2.xml")
        self.assertTrue(isinstance(obj, list))
        self.assertEquals(2, len(obj))

    def test201(self):
        'TimeSeries.as_list reads stream'
        stream = file(self.testdata + "read.PI.timezone.2.xml")
        obj = TimeSeries.as_list(stream)
        self.assertTrue(isinstance(obj, list))
        self.assertEquals(2, len(obj))

    def test300(self):
        'TimeSeries.as_dict reads from empty django QuerySet'

        testdata = django.QuerySet([])
        obj = TimeSeries.as_dict(testdata)
        self.assertEquals({}, obj)

    def test305(self):
        'TimeSeries.as_dict reads from django QuerySet'

        DT = datetime
        testdata = django.QuerySet([
                {'location': '123',
                 'parameter': 'Q',
                 'events': [(DT(2011, 11, 11, 12, 20), 1.1, 8, ''),
                            (DT(2011, 11, 11, 12, 25), 1.2, 1, ''),
                            (DT(2011, 11, 11, 12, 30), 1.3, 2, '')]},
                {'location': '124',
                 'parameter': 'Q',
                 'events': [(DT(2011, 11, 11, 12, 20), 0.1, 8, ''),
                            (DT(2011, 11, 11, 12, 25), 0.2, 1, ''),
                            (DT(2011, 11, 11, 12, 30), 0.3, 2, '')]},
                ])
        obj = TimeSeries.as_dict(testdata)
        self.assertEquals(set([('123', 'Q'), ('124', 'Q')]), set(obj.keys()))
        self.assertEquals(set([1.1, 1.2, 1.3]), set(i[0] for i in obj[('123', 'Q')]._events.values()))
        self.assertEquals(set([0.1, 0.2, 0.3]), set(i[0] for i in obj[('124', 'Q')]._events.values()))
        self.assertEquals([], testdata.filtered)

    def test350(self):
        'TimeSeries.as_dict filters based on timestamps from django QuerySet'

        DT = datetime
        testdata = django.QuerySet([
                {'location': '124',
                 'parameter': 'Q',
                 'events': [(DT(2011, 11, 11, 12, 20), 0.1, 8, ''),
                            (DT(2011, 11, 11, 12, 25), 0.2, 1, ''),
                            (DT(2011, 11, 11, 12, 30), 0.3, 2, '')]},
                ])
        start = DT(2011, 11, 11, 12, 25)
        obj = TimeSeries.as_dict(testdata, start)
        self.assertEquals(set([('124', 'Q')]), set(obj.keys()))
        self.assertEquals([((), {'timestamp__gte': start})], testdata.filtered)

    def test352(self):
        'TimeSeries.as_dict filters based on timestamps from django QuerySet'

        DT = datetime
        testdata = django.QuerySet([
                {'location': '124',
                 'parameter': 'Q',
                 'events': [(DT(2011, 11, 11, 12, 20), 0.1, 8, ''),
                            (DT(2011, 11, 11, 12, 25), 0.2, 1, ''),
                            (DT(2011, 11, 11, 12, 30), 0.3, 2, '')]},
                ])
        end = DT(2011, 11, 11, 12, 25)
        obj = TimeSeries.as_dict(testdata, end=end)
        self.assertEquals(set([('124', 'Q')]), set(obj.keys()))
        self.assertEquals([((), {'timestamp__lte': end})], testdata.filtered)

    def test354(self):
        'TimeSeries.as_dict filters based on timestamps from django QuerySet'

        DT = datetime
        testdata = django.QuerySet([
                {'location': '124',
                 'parameter': 'Q',
                 'events': [(DT(2011, 11, 11, 12, 20), 0.1, 8, ''),
                            (DT(2011, 11, 11, 12, 25), 0.2, 1, ''),
                            (DT(2011, 11, 11, 12, 30), 0.3, 2, '')]},
                ])
        start = DT(2011, 11, 11, 12, 25)
        end = DT(2011, 11, 11, 12, 25)
        obj = TimeSeries.as_dict(testdata, start, end)
        self.assertEquals(set([('124', 'Q')]), set(obj.keys()))
        self.assertEquals([((), {'timestamp__gte': start}),
                           ((), {'timestamp__lte': end}),
                           ], testdata.filtered)


class TimeSeriesOutput(TestCase):

    def setUp(self):
        self.testdata = pkg_resources.resource_filename(
            "timeseries", "testdata/")
        if ('current.xml') in os.listdir(self.testdata):
            os.unlink(self.testdata + "current.xml")

    def tearDown(self):
        if ('current.xml') in os.listdir(self.testdata):
            os.unlink(self.testdata + "current.xml")

    def test000(self):
        'TimeSeries.write_to_pi_file writes list to new file'
        obj = TimeSeries.as_list(self.testdata + "read.PI.timezone.2.xml")
        TimeSeries.write_to_pi_file(self.testdata + "current.xml",
                                    obj,
                                    offset=2)
        target = file(self.testdata + "targetOutput.xml").read()
        current = file(self.testdata + "current.xml").read()
        self.assertEquals(target.strip(), current.strip())

    def test010(self):
        'TimeSeries.write_to_pi_file writes list to stream'
        stream = mock.Stream()
        obj = TimeSeries.as_list(self.testdata + "read.PI.timezone.2.xml")
        TimeSeries.write_to_pi_file(stream, obj, offset=2)
        target = file(self.testdata + "targetOutput.xml").read()
        current = ''.join(stream.content)
        self.assertEquals(target.strip(), current.strip())

    def test020(self):
        'TimeSeries.write_to_pi_file writes dict to stream'
        stream = mock.Stream()
        obj = TimeSeries.as_dict(self.testdata + "read.PI.timezone.2.xml")
        TimeSeries.write_to_pi_file(stream, obj, offset=2)
        target = file(self.testdata + "targetOutput.xml").read()
        current = ''.join(stream.content)
        self.assertEquals(target.strip(), current.strip())

    def test022(self):
        'TimeSeries.write_to_pi_file writes dict to stream'
        stream = mock.Stream()
        obj = TimeSeries.as_dict(self.testdata + "read.PI.timezone.2.xml")
        TimeSeries.write_to_pi_file(stream, obj, offset=0)
        target = file(self.testdata + "targetOutput00.xml").read()
        current = ''.join(stream.content)
        self.assertEquals(target.strip(), current.strip())

    def test024(self):
        'TimeSeries.write_to_pi_file writes dict to stream with 12 offset'
        stream = mock.Stream()
        obj = TimeSeries.as_dict(self.testdata + "read.PI.timezone.2.xml")
        TimeSeries.write_to_pi_file(stream, obj, offset=12)
        target = file(self.testdata + "targetOutput12.xml").read()
        current = ''.join(stream.content)
        self.assertEquals(target.strip(), current.strip())

    def test030(self):
        'TimeSeries.write_to_pi_file appends children to stream'
        stream = mock.Stream()
        obj = TimeSeries.as_dict(self.testdata + "read.PI.timezone.2.xml")
        TimeSeries.write_to_pi_file(stream, obj, offset=0, append=True)
        target_lines = file(self.testdata + "targetOutput00.xml").readlines()[2:-1]
        target = ''.join(i.strip() for i in target_lines)
        current = ''.join(i.strip() for i in ''.join(stream.content).split('\n'))
        self.assertEquals(target, current)


class TimeSeriesBinaryOperations(TestCase):
    def setUp(self):
        obj = TimeSeries(location_id='loc', parameter_id='par')
        d1 = datetime(1979, 3, 15, 9, 35)
        d3 = datetime(1979, 4, 12, 9, 35)
        d2 = datetime(1979, 5, 15, 9, 35)
        obj[d1] = 1.23
        obj[d3] = 0.23
        obj[d2] = -3.01

        self.a = obj

        obj = TimeSeries(location_id='loc', parameter_id='par')
        obj[d1] = 33.3
        obj[d2] = -0.25

        self.b = obj

    def test000(self):
        'cloning timeseries without events'

        current = self.a.clone()

        for attrib in self.a.__dict__:
            if attrib == '_events':
                continue
            self.assertEquals(current.__dict__[attrib],
                              self.a.__dict__[attrib])
        self.assertEquals({}, current._events)

    def test010(self):
        'cloning timeseries with events'

        current = self.a.clone(with_events=True)

        for attrib in self.a.__dict__:
            self.assertEquals(current.__dict__[attrib],
                              self.a.__dict__[attrib])

    ## testing binary functions, PLUS
    def test100(self):
        'timeseries + 0 gives same timeseries'

        current = self.a + 0

        for attrib in self.a.__dict__:
            self.assertEquals(current.__dict__[attrib],
                              self.a.__dict__[attrib])

    def test110(self):
        'timeseries + 1 gives same timestamps with other value'

        current = self.a + 1

        for attrib in self.a.__dict__:
            if attrib == '_events':
                continue
            self.assertEquals(self.a.__dict__[attrib],
                              current.__dict__[attrib])

        for key in self.a._events:
            self.assertEquals(self.a.get_value(key) + 1, current[key][0])

    def test112(self):
        '1 + timeseries gives same timestamps with other value'

        current = 1 + self.a

        for attrib in self.a.__dict__:
            if attrib == '_events':
                continue
            self.assertEquals(self.a.__dict__[attrib],
                              current.__dict__[attrib])

        for key in self.a._events:
            self.assertEquals(self.a.get_value(key) + 1, current[key][0])

    def test120(self):
        'timeseries + other gives union of keys'

        current = self.a + self.b

        for attrib in self.a.__dict__:
            if attrib == '_events':
                continue
            self.assertEquals(self.a.__dict__[attrib],
                              current.__dict__[attrib])

        for key in current._events:
            self.assertEquals(self.a.get(key, [0])[0] + self.b.get(key, [0])[0],
                              current[key][0])

    ## testing binary functions, MINUS
    def test130(self):
        'timeseries - 0 gives same timeseries'

        current = self.a - 0

        for attrib in self.a.__dict__:
            self.assertEquals(current.__dict__[attrib],
                              self.a.__dict__[attrib])

    def test140(self):
        'timeseries - 1 gives same timestamps with other value'

        current = self.a - 1

        for attrib in self.a.__dict__:
            if attrib == '_events':
                continue
            self.assertEquals(self.a.__dict__[attrib],
                              current.__dict__[attrib])

        for key in self.a._events:
            self.assertEquals(self.a.get_value(key) - 1, current[key][0])

    def test142(self):
        '1 - timeseries gives same timestamps with other value'

        current = 1 - self.a

        for attrib in self.a.__dict__:
            if attrib == '_events':
                continue
            self.assertEquals(self.a.__dict__[attrib],
                              current.__dict__[attrib])

        for key in self.a._events:
            self.assertEquals(1 - self.a.get_value(key), current[key][0])

    def test150(self):
        'timeseries - other gives union of keys'

        current = self.a - self.b

        for attrib in self.a.__dict__:
            if attrib == '_events':
                continue
            self.assertEquals(self.a.__dict__[attrib],
                              current.__dict__[attrib])

        for key in current._events:
            self.assertEquals(self.a.get(key, [0])[0] - self.b.get(key, [0])[0],
                              current[key][0])

    ## testing binary functions, MULT
    def test200(self):
        'timeseries * 1 gives same timeseries'

        current = self.a * 1

        for attrib in self.a.__dict__:
            self.assertEquals(current.__dict__[attrib],
                              self.a.__dict__[attrib])

    def test210(self):
        'timeseries * 2 gives same timestamps with other value'

        current = self.a * 2

        for attrib in self.a.__dict__:
            if attrib == '_events':
                continue
            self.assertEquals(self.a.__dict__[attrib],
                              current.__dict__[attrib])

        for key in self.a._events:
            self.assertEquals(self.a.get_value(key) * 2, current[key][0])

    def test212(self):
        '2 * timeseries gives same timestamps with other value'

        current = 2 * self.a

        for attrib in self.a.__dict__:
            if attrib == '_events':
                continue
            self.assertEquals(self.a.__dict__[attrib],
                              current.__dict__[attrib])

        for key in self.a._events:
            self.assertEquals(self.a.get_value(key) * 2, current[key][0])

    def test220(self):
        'timeseries * other gives intersection of keys'

        current = self.a * self.b

        for attrib in self.a.__dict__:
            if attrib == '_events':
                continue
            self.assertEquals(self.a.__dict__[attrib],
                              current.__dict__[attrib])

        for key in current._events:
            self.assertEquals(self.a.get_value(key) * self.b.get_value(key),
                              current[key][0])

    ## testing binary functions, with is_locf
    def test230(self):
        'self is last observation carried forward.'

        a = self.a.clone(with_events=True)
        a.is_locf = True
        b = self.a.clone(with_events=True)
        key = datetime(1979, 8, 1, 9, 35)
        d2 = datetime(1979, 5, 15, 9, 35)
        b[key] = 2

        current = a + b
        self.assertEquals(a[d2][0] + 2, current[key][0])

    def test232(self):
        'locf, self and other are completely disjoint, result has only other keys'
        a = self.a.clone()
        a.is_locf = True
        b = self.a.clone()
        d1 = datetime(2011, 5, 15, 9, 35)
        d2 = datetime(2011, 6, 15, 9, 35)
        d3 = datetime(2011, 7, 15, 9, 35)
        d4 = datetime(2011, 8, 15, 9, 35)
        b[d1] = 2
        b[d2] = 3
        a[d3] = 1
        a[d4] = 0

        current = a + b
        self.assertEquals(2, current[d1][0])
        self.assertEquals(3, current[d2][0])
        self.assertEquals(None, current.get(d3))
        self.assertEquals(None, current.get(d4))

    def test234(self):
        'locf, self and other are completely disjoint, result has only other keys'
        a = self.a.clone()
        a.is_locf = True
        b = self.a.clone()
        d1 = datetime(2011, 5, 15, 9, 35)
        d2 = datetime(2011, 6, 15, 9, 35)
        d3 = datetime(2011, 7, 15, 9, 35)
        d4 = datetime(2011, 8, 15, 9, 35)
        a[d1] = 2
        a[d2] = 3
        b[d3] = 1
        b[d4] = 0

        current = a + b
        self.assertEquals(None, current.get(d1))
        self.assertEquals(None, current.get(d2))
        self.assertEquals(4, current[d3][0])
        self.assertEquals(3, current[d4][0])

    # test clone
    def test300(self):
        'test equality, different attributes -> False'

        b = self.a.clone(with_events=True)
        b.location_id = 'different'

        self.assertFalse(b == self.a)

    def test310(self):
        'test equality, less events -> False'

        b = self.a.clone(with_events=True)
        del b._events[b._events.keys()[0]]

        self.assertFalse(b == self.a)

    def test320(self):
        'test equality, more events -> False'

        b = self.a.clone(with_events=True)
        b._events[self.a._events.keys()[-1] + timedelta(0, 100)] = 1

        self.assertFalse(b == self.a)

    def test330(self):
        'test equality, different timestamps -> False'

        b = self.a.clone(with_events=True)
        a = self.a.clone(with_events=True)
        b._events[self.a._events.keys()[-1] + timedelta(0, 100)] = 1
        a._events[self.a._events.keys()[-1] + timedelta(0, 200)] = 1

        self.assertFalse(b == a)

    def test340(self):
        'test equality, different values -> False'

        b = self.a.clone(with_events=True)
        a = self.a.clone(with_events=True)
        b._events[self.a._events.keys()[-1] + timedelta(0, 200)] = 1
        a._events[self.a._events.keys()[-1] + timedelta(0, 200)] = 2

        self.assertFalse(b == a)

    def test350(self):
        'test equality, nothing different -> True'

        b = self.a.clone(with_events=True)
        self.assertTrue(b == self.a)

    # 400 series are the unary functions
    def test400(self):
        'abs(timeseries)'

        current = abs(self.a)

        for key in self.a._events:
            self.assertEquals(abs(self.a.get_value(key)), current[key][0])


class TimeSeriesSubsetting(TestCase):
    def setUp(self):
        obj = TimeSeries(location_id='loc', parameter_id='par')
        self.d1 = datetime(1979, 3, 15, 9, 35)
        self.d3 = datetime(1979, 4, 12, 9, 35)
        self.d2 = datetime(1979, 5, 15, 9, 35)
        obj[self.d1] = 1.23
        obj[self.d3] = 0.23
        obj[self.d2] = -3.01

        self.a = obj

    def test0000(self):
        'filter without parameters returns everything'

        b = self.a.filter()
        self.assertEquals(self.a, b)

    def test0002(self):
        'filter against None returns everything'

        b = self.a.filter(timestamp_lte=None)
        self.assertEquals(self.a, b)
        b = self.a.filter(timestamp_lt=None)
        self.assertEquals(self.a, b)

    def test0010(self):
        'filter before or at timestamp'

        b = self.a.filter(timestamp_lte=self.d2)
        self.assertEquals(self.a, b)
        b = self.a.filter(timestamp_lte=self.d1)
        self.assertEquals(1, len(b))

    def test0012(self):
        'filter before timestamp'

        b = self.a.filter(timestamp_lt=self.d1)
        self.assertEquals(0, len(b))
        b = self.a.filter(timestamp_lt=self.d2)
        self.assertEquals(2, len(b))

    def test0020(self):
        'filter after or at timestamp'

        b = self.a.filter(timestamp_gte=self.d1)
        self.assertEquals(self.a, b)

    def test0022(self):
        'filter after timestamp'

        b = self.a.filter(timestamp_gt=self.d1)
        self.assertEquals(2, len(b))
        b = self.a.filter(timestamp_gt=self.d2)
        self.assertEquals(0, len(b))

    def test0030(self):
        'filter double sided'

        b = self.a.filter(timestamp_gte=self.d1, timestamp_lte=self.d2)
        self.assertEquals(self.a, b)
        b = self.a.filter(timestamp_gt=self.d1, timestamp_lt=self.d2)
        self.assertEquals(1, len(b))
