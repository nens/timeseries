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
import pkg_resources
from datetime import datetime


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
        obj.events[d1] = 1.23
        obj.events[d3] = 0.23
        obj.events[d2] = -3.01
        self.assertEqual(d1, obj.get_start_date())
        self.assertEqual(d2, obj.get_end_date())

    def test_023(self):
        'getting events of a non empty time series'

        obj = TimeSeries(location_id='loc', parameter_id='par')
        d1 = datetime(1979, 3, 15, 9, 35)
        d3 = datetime(1979, 4, 12, 9, 35)
        d2 = datetime(1979, 5, 15, 9, 35)
        obj.events[d1] = 1.23
        obj.events[d3] = 0.23
        obj.events[d2] = -3.01
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

        [self.assertEquals(obj.events[d], obj[d]) for d in obj.events.keys()]

    def test_110(self):
        'add_value is defined and equal to __setitem__'

        obj = TimeSeries(location_id='loc', parameter_id='par')
        d1 = datetime(1979, 3, 15, 9, 35)
        ## setting
        obj.add_value(d1, 1.23)
        ## checking
        self.assertEquals(obj.events[d1], obj[d1])

    def test_111(self):
        'get_value is defined and equal to __getitem__'

        obj = TimeSeries(location_id='loc', parameter_id='par')
        d1 = datetime(1979, 3, 15, 9, 35)
        ## setting
        obj[d1] = 1.23
        ## checking
        self.assertEquals(obj.events[d1], obj.get_value(d1))

    def test_115(self):
        'can use .get with default value'

        obj = TimeSeries(location_id='loc', parameter_id='par')
        d1 = datetime(1979, 3, 15, 9, 35)
        obj.add_value(d1, 1.23)  # executing __setitem__
        ## finds values that are there
        [self.assertEquals(obj.events[d], obj.get(d)) for d in obj.events.keys()]
        d2 = datetime(1979, 5, 15, 9, 35)
        ## returns default value if event is not there
        self.assertEquals(None, obj.get(d2))


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


class TimeSeriesInputOutput(TestCase):

    def setUp(self):
        self.testdata = pkg_resources.resource_filename("timeseries", "testdata/")

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
        'result of TimeSeries.as_dict is indexed on locationId parameterId 2-tuples'
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
                          ts.get_events())

    def test101(self):
        'TimeSeries.as_dict reads events of series (b)'
        obj = TimeSeries.as_dict(self.testdata + "read.PI.timezone.2.xml")
        ts = obj[("600", "P2504")]
        self.assertEquals([
                (str_to_datetime("2010-04-05", "00:00:00", 2), 17),
                (str_to_datetime("2010-04-08", "00:00:00", 2), 22),
                (str_to_datetime("2010-04-10", "00:00:00", 2), 24), ],
                          ts.get_events())

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
