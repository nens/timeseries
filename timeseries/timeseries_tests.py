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
import pkg_resources


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
        import datetime
        self.assertEqual(datetime.datetime(1970, 1, 1), obj.get_start_date())
        self.assertEqual(datetime.datetime(1970, 1, 1), obj.get_end_date())

    def test_022(self):
        'start and end of a time series with events'

        obj = TimeSeries(location_id='loc', parameter_id='par')
        import datetime
        d1 = datetime.datetime(1979, 3, 15, 9, 35)
        d3 = datetime.datetime(1979, 4, 12, 9, 35)
        d2 = datetime.datetime(1979, 5, 15, 9, 35)
        obj.events[d1] = 1.23
        obj.events[d3] = 0.23
        obj.events[d2] = -3.01
        self.assertEqual(d1, obj.get_start_date())
        self.assertEqual(d2, obj.get_end_date())

    def test_023(self):
        'getting events of a non empty time series'

        obj = TimeSeries(location_id='loc', parameter_id='par')
        import datetime
        d1 = datetime.datetime(1979, 3, 15, 9, 35)
        d3 = datetime.datetime(1979, 4, 12, 9, 35)
        d2 = datetime.datetime(1979, 5, 15, 9, 35)
        obj.events[d1] = 1.23
        obj.events[d3] = 0.23
        obj.events[d2] = -3.01
        self.assertEqual(3, len(obj.get_events()))
        self.assertEqual(2, len(obj.get_events(d3)))
        self.assertEqual(2, len(obj.get_events(d1, d3)))

    def test_024(self):
        'getting events of a eventless time series'

        obj = TimeSeries(location_id='loc', parameter_id='par')
        import datetime
        d1 = datetime.datetime(1979, 3, 15, 9, 35)
        d3 = datetime.datetime(1979, 4, 12, 9, 35)
        self.assertEqual(0, len(obj.get_events()))
        self.assertEqual(0, len(obj.get_events(d3)))
        self.assertEqual(0, len(obj.get_events(d1, d3)))


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

    def test010(self):
        'result of TimeSeries.as_dict is indexed on locationId parameterId 2-tuples'
        obj = TimeSeries.as_dict(self.testdata + "read.PI.timezone.2.xml")
        self.assertEquals(set([("600", "P1201"), ("600", "P2504")]), 
                          set(obj.keys()))
        self.assertTrue(isinstance(obj[("600", "P1201")], TimeSeries))
        self.assertTrue(isinstance(obj[("600", "P2504")], TimeSeries))
