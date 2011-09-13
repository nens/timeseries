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
# Initial programmer: Pieter Swinkels
# Initial date:       2010-11-24
#
#******************************************************************************


from datetime import datetime
from datetime import timedelta
from unittest import TestCase

from timeseriesstub import add_timeseries
from timeseriesstub import average_monthly_events
from timeseriesstub import create_empty_timeseries
from timeseriesstub import enumerate_events
from timeseriesstub import map_timeseries
from timeseriesstub import multiply_timeseries
from timeseriesstub import split_timeseries
from timeseriesstub import SparseTimeseriesStub
from timeseriesstub import TimeseriesStub
from timeseriesstub import TimeseriesWithMemoryStub
from timeseriesstub import TimeseriesRestrictedStub

from timeseries import TimeSeries


class TimeseriesStubTestSuite(TestCase):

    def test_c(self):
        """Test the value on the first date & time is the first value."""
        timeserie = TimeseriesStub()
        today = datetime(2010, 11, 24)
        timeserie.add_value(today, 20.0)
        self.assertAlmostEqual(20.0, timeserie.get_value(today))

    def test_d(self):
        """Test the value after the first date & time is zero."""
        timeserie = TimeseriesStub()
        today = datetime(2010, 11, 24)
        timeserie.add_value(today, 20.0)
        tomorrow = today + timedelta(1)
        self.assertAlmostEqual(0.0, timeserie.get_value(tomorrow))

    def test_e(self):
        """Test the value before the second date & time is zero."""
        timeserie = TimeseriesStub()
        today = datetime(2010, 11, 24)
        timeserie.add_value(today, 20.0)
        tomorrow = today + timedelta(1)
        day_after_tomorrow = tomorrow + timedelta(1)
        timeserie.add_value(day_after_tomorrow, 30.0)
        self.assertAlmostEqual(0.0, timeserie.get_value(tomorrow))

    def test_ea(self):
        """Test the value before the third date & time is the second value."""
        today = datetime(2010, 12, 20)
        timeserie = TimeseriesStub((today, 10.0),
                                   (today + timedelta(1), 20.0),
                                   (today + timedelta(2), 30.0))
        self.assertAlmostEqual(20.0, timeserie.get_value(today + timedelta(1)))

    def test_f(self):
        """Test missing dates are automatically added as zeros."""
        timeserie = TimeseriesStub()
        today = datetime(2010, 12, 3)
        tomorrow = datetime(2010, 12, 4)
        day_after_tomorrow = datetime(2010, 12, 5)
        timeserie.add_value(today, 20)
        timeserie.add_value(day_after_tomorrow, 30)
        events = [event for event in timeserie.events()]
        expected_events = [(today, 20),
                           (tomorrow, 0),
                           (day_after_tomorrow, 30)]
        self.assertEqual(expected_events, events)

    def test_fa(self):
        """Test the aggregation of a single daily events to a monthly event."""
        timeserie = TimeseriesStub()
        timeserie.add_value(datetime(2010, 12, 8), 20)
        monthly_events = [event for event in timeserie.monthly_events()]
        expected_monthly_events = [(datetime(2010, 12, 1), 20)]
        self.assertEqual(expected_monthly_events, monthly_events)

    def test_fb(self):
        """Test aggregation of a multiple daily events to a monthly event."""
        timeserie = TimeseriesStub()
        timeserie.add_value(datetime(2010, 12, 8), 20)
        timeserie.add_value(datetime(2010, 12, 9), 30)
        timeserie.add_value(datetime(2010, 12, 10), 40)
        monthly_events = [event for event in timeserie.monthly_events()]
        expected_monthly_events = [(datetime(2010, 12, 1), 90)]
        self.assertEqual(expected_monthly_events, monthly_events)

    def test_fc(self):
        """Test the aggregation of a multiple daily events to monthly
        events.

        """
        timeserie = TimeseriesStub()
        timeserie.add_value(datetime(2010, 12, 8), 20)
        timeserie.add_value(datetime(2010, 12, 9), 30)
        timeserie.add_value(datetime(2010, 12, 10), 40)
        timeserie.add_value(datetime(2011, 1, 1), 50)
        monthly_events = [event for event in timeserie.monthly_events()]
        expected_monthly_events = [(datetime(2010, 12, 1), 90),
                                   (datetime(2011, 1, 1), 50)]
        self.assertEqual(expected_monthly_events, monthly_events)

    def test_g(self):
        """Test add_timeseries on time series with same start and end date."""
        today = datetime(2010, 12, 5)
        tomorrow = datetime(2010, 12, 6)
        timeserie_a = TimeseriesStub()
        timeserie_a.add_value(today, 10)
        timeserie_a.add_value(tomorrow, 20)
        timeserie_b = TimeseriesStub()
        timeserie_b.add_value(today, 30)
        timeserie_b.add_value(tomorrow, 40)
        expected_timeserie = [(today, 40), (tomorrow, 60)]
        summed_timeseries = \
             list(add_timeseries(timeserie_a, timeserie_b).events())
        self.assertEqual(expected_timeserie, summed_timeseries)

    def test_ga(self):
        """Test add_timeseries on time series with different start and end
        dates.

        """
        today = datetime(2010, 12, 5)
        tomorrow = datetime(2010, 12, 6)
        timeserie_a = TimeseriesStub((today, 10))
        timeserie_b = TimeseriesStub((tomorrow, 40))
        expected_events = [(today, 10), (tomorrow, 40)]
        events = list(add_timeseries(timeserie_a, timeserie_b).events())
        self.assertEqual(expected_events, events)

    def test_h(self):
        """Test multiply_timeseries on time series."""
        today = datetime(2010, 12, 5)
        tomorrow = datetime(2010, 12, 6)
        timeserie = TimeseriesStub()
        timeserie.add_value(today, 10)
        timeserie.add_value(tomorrow, 20)
        expected_timeserie = [(today, 40), (tomorrow, 80)]
        multiplied_timeseries = \
             list(multiply_timeseries(timeserie, 4).events())
        self.assertEqual(expected_timeserie, multiplied_timeseries)

    def test_i(self):
        """Test split_timeseries on time series."""
        timeserie = TimeseriesStub()
        timeserie.add_value(datetime(2010, 12, 7), 10)
        timeserie.add_value(datetime(2010, 12, 8), 20)
        timeserie.add_value(datetime(2010, 12, 9), -5)
        expected_negative_timeserie_events = [(datetime(2010, 12, 7), 0),
                                              (datetime(2010, 12, 8), 0),
                                              (datetime(2010, 12, 9), -5)]
        expected_positive_timeserie_events = [(datetime(2010, 12, 7), 10),
                                              (datetime(2010, 12, 8), 20),
                                              (datetime(2010, 12, 9), 0)]
        splitted_timeseries = split_timeseries(timeserie)
        self.assertEqual(expected_negative_timeserie_events, \
                         list(splitted_timeseries[0].events()))
        self.assertEqual(expected_positive_timeserie_events, \
                         list(splitted_timeseries[1].events()))

    def test_j(self):
        """Test create_empty_timeseries on an empty timeseries."""
        timeseries = TimeseriesStub()
        self.assertEqual(TimeseriesStub(), create_empty_timeseries(timeseries))

    def test_k(self):
        """Test create_empty_timeseries on a non-empty timeseries."""
        timeseries = TimeseriesStub((datetime(2011, 1, 26), 10))
        expected_timeseries = TimeseriesStub((datetime(2011, 1, 26), 0.0))
        self.assertEqual(expected_timeseries,
                         create_empty_timeseries(timeseries))

    def test_l(self):
        """Test map_timeseries on a non-empty timeseries."""
        timeseries = TimeseriesStub((datetime(2011, 7, 6), 10),
                                    (datetime(2011, 7, 7), 20),
                                    (datetime(2011, 7, 8), 30))
        expected_events = [(datetime(2011, 7, 6), -10),
                           (datetime(2011, 7, 7), -20),
                           (datetime(2011, 7, 8), -30)]
        map_function = lambda v: -1.0 * abs(v)
        events = list(map_timeseries(timeseries, map_function).events())
        self.assertEqual(expected_events, events)


class SparseTimeseriesStubTests(TestCase):

    def test_a(self):
        """Test events returns the right events."""
        timeseries = SparseTimeseriesStub(datetime(2011, 4, 8), \
                                          [10.0, 20.0, 30.0])
        expected_events = [(datetime(2011, 4,  8), 10.0),
                           (datetime(2011, 4,  9), 20.0),
                           (datetime(2011, 4, 10), 30.0)]
        self.assertEqual(expected_events, list(timeseries.events()))

    def test_b(self):
        """Test add_value adds the right events."""
        timeseries = SparseTimeseriesStub()
        timeseries.add_value(datetime(2011, 4,  8), 10.0)
        timeseries.add_value(datetime(2011, 4,  9), 20.0)
        timeseries.add_value(datetime(2011, 4, 10), 30.0)
        expected_events = [(datetime(2011, 4,  8), 10.0),
                           (datetime(2011, 4,  9), 20.0),
                           (datetime(2011, 4, 10), 30.0)]
        self.assertEqual(expected_events, list(timeseries.events()))

    def test_c(self):
        """Test add_value can only add events on consecutive days."""
        timeseries = SparseTimeseriesStub()
        timeseries.add_value(datetime(2011, 4,  8), 10.0)
        self.assertRaises(AssertionError, timeseries.add_value, \
                          datetime(2011, 4, 10), 30.0)

    def test_d(self):
        """Test add_value can only add events on consecutive days."""
        timeseries = SparseTimeseriesStub(datetime(2011, 4, 8), \
                                          [10.0, 20.0, 30.0])
        self.assertRaises(AssertionError, timeseries.add_value, \
                          datetime(2011, 4, 12), 30.0)

    def test_e(self):
        """Test events returns a subset of the events.

        The subset includes all events.

        """
        timeseries = SparseTimeseriesStub()
        timeseries.add_value(datetime(2011, 4,  8), 10.0)
        timeseries.add_value(datetime(2011, 4,  9), 20.0)
        timeseries.add_value(datetime(2011, 4, 10), 30.0)
        timeseries.add_value(datetime(2011, 4, 11), 40.0)
        start_date, end_date = datetime(2011, 4, 8), datetime(2011, 4, 12)
        events = list(timeseries.events(start_date, end_date))
        self.assertEqual(4, len(events))
        self.assertEqual((datetime(2011, 4,  8), 10.0), events[0])
        self.assertEqual((datetime(2011, 4,  9), 20.0), events[1])
        self.assertEqual((datetime(2011, 4,  10), 30.0), events[2])
        self.assertEqual((datetime(2011, 4,  11), 40.0), events[3])

    def test_f(self):
        """Test events returns a subset of the events.

        The subset starts at the first event but does not include the later
        events.

        """
        timeseries = SparseTimeseriesStub()
        timeseries.add_value(datetime(2011, 4,  8), 10.0)
        timeseries.add_value(datetime(2011, 4,  9), 20.0)
        timeseries.add_value(datetime(2011, 4, 10), 30.0)
        timeseries.add_value(datetime(2011, 4, 11), 40.0)
        start_date, end_date = datetime(2011, 4, 8), datetime(2011, 4, 10)
        events = list(timeseries.events(start_date, end_date))
        self.assertEqual(2, len(events))
        self.assertEqual((datetime(2011, 4,  8), 10.0), events[0])
        self.assertEqual((datetime(2011, 4,  9), 20.0), events[1])

    def test_g(self):
        """Test events returns a subset of the events.

        The subset starts before the first event and does not include the later
        events.

        """
        timeseries = SparseTimeseriesStub()
        timeseries.add_value(datetime(2011, 4,  8), 10.0)
        timeseries.add_value(datetime(2011, 4,  9), 20.0)
        timeseries.add_value(datetime(2011, 4, 10), 30.0)
        timeseries.add_value(datetime(2011, 4, 11), 40.0)
        start_date, end_date = datetime(2011, 4, 6), datetime(2011, 4, 10)
        events = list(timeseries.events(start_date, end_date))
        self.assertEqual(2, len(events))
        self.assertEqual((datetime(2011, 4,  8), 10.0), events[0])
        self.assertEqual((datetime(2011, 4,  9), 20.0), events[1])

    def test_h(self):
        """Test events returns a subset of the events.

        The subset starts after the first event and does not include the later
        events.

        """
        timeseries = SparseTimeseriesStub()
        timeseries.add_value(datetime(2011, 4,  8), 10.0)
        timeseries.add_value(datetime(2011, 4,  9), 20.0)
        timeseries.add_value(datetime(2011, 4, 10), 30.0)
        timeseries.add_value(datetime(2011, 4, 11), 40.0)
        start_date, end_date = datetime(2011, 4, 9), datetime(2011, 4, 11)
        events = list(timeseries.events(start_date, end_date))
        self.assertEqual(2, len(events))
        self.assertEqual((datetime(2011, 4,  9), 20.0), events[0])
        self.assertEqual((datetime(2011, 4, 10), 30.0), events[1])


class average_monthly_events_Tests(TestCase):

    def test_a(self):
        """Test the aggregation of a single daily event to an average monthly
        event.

        """
        timeserie = TimeseriesStub()
        timeserie.add_value(datetime(2010, 12, 8), 20)
        avg_monthly_events = [e for e in average_monthly_events(timeserie)]
        expected_avg_monthly_events = [(datetime(2010, 12, 1), 20.0)]
        self.assertEqual(expected_avg_monthly_events, avg_monthly_events)

    def test_b(self):
        """Test the aggregation of multiple daily events to an average monthly
        event.

        The daily events lie within a single month.

        """
        timeserie = TimeseriesStub()
        timeserie.add_value(datetime(2010, 12, 8), 20)
        timeserie.add_value(datetime(2010, 12, 9), 30)
        timeserie.add_value(datetime(2010, 12, 10), 40)
        avg_monthly_events = [e for e in average_monthly_events(timeserie)]
        expected_avg_monthly_events = [(datetime(2010, 12, 1), 30.0)]
        self.assertEqual(expected_avg_monthly_events, avg_monthly_events)

    def test_c(self):
        """Test the aggregation of multiple daily events to an average monthly
        event.

        The daily events lie within two consecutive months.

        """
        timeserie = TimeseriesStub()
        timeserie.add_value(datetime(2010, 12, 8), 20)
        timeserie.add_value(datetime(2010, 12, 9), 30)
        timeserie.add_value(datetime(2010, 12, 10), 40)
        timeserie.add_value(datetime(2011, 1, 1), 50)
        avg_monthly_events = [e for e in average_monthly_events(timeserie)]
        expected_avg_monthly_events = [(datetime(2010, 12, 1), 3.75),
                                       (datetime(2011, 1, 1), 50.0)]
        self.assertEqual(expected_avg_monthly_events, avg_monthly_events)


class TimeseriesWithMemoryTests(TestCase):

    def test_a(self):
        """Test the value on the first date is the first value."""
        today = datetime(2010, 12, 20)
        timeserie = TimeseriesWithMemoryStub((today, 20.0))
        self.assertAlmostEqual(20.0, timeserie.get_value(today))

    def test_b(self):
        """Test the value after the first date & time is the first value."""
        today = datetime(2010, 12, 20)
        timeserie = TimeseriesWithMemoryStub((today, 20.0))
        tomorrow = today + timedelta(1)
        self.assertAlmostEqual(20.0, timeserie.get_value(tomorrow))

    def test_c(self):
        """Test the value before the second date & time is the first value."""
        today = datetime(2010, 12, 20)
        timeserie = TimeseriesWithMemoryStub((today, 20.0),
                                             (today + timedelta(2), 30.0))
        tomorrow = today + timedelta(1)
        self.assertAlmostEqual(20.0, timeserie.get_value(tomorrow))

    def test_d(self):
        """Test missing dates are automatically added as the latest known
        value.

        """
        timeserie = TimeseriesWithMemoryStub()
        today = datetime(2010, 12, 3)
        tomorrow = datetime(2010, 12, 4)
        day_after_tomorrow = datetime(2010, 12, 5)
        timeserie.add_value(today, 20)
        timeserie.add_value(day_after_tomorrow, 30)
        events = [event for event in timeserie.events()]
        expected_events = \
            [(today, 20), (tomorrow, 20), (day_after_tomorrow, 30)]
        self.assertEqual(expected_events, events)


class TimeseriesStubRestrictedTest(TestCase):

    def test_a(self):
        timeseries = TimeseriesStub((datetime(2011, 1, 26), 0.0),
                                    (datetime(2011, 2, 3), 10.0),
                                    (datetime(2011, 2, 28), 0.0))
        timeseries_restricted = \
             TimeseriesRestrictedStub(timeseries=timeseries,
                                      start_date=datetime(2011, 2, 2),
                                      end_date=datetime(2011, 2, 5))
        expected_timeseries = TimeseriesStub((datetime(2011, 2, 2), 0.0),
                                             (datetime(2011, 2, 3), 10.0),
                                             (datetime(2011, 2, 4), 0.0))
        self.assertEqual(list(expected_timeseries.events()), \
                         list(timeseries_restricted.events()))


class enumerate_eventsTestSuite(TestCase):

    def test_a(self):
        today = datetime(2010, 12, 2)
        tomorrow = datetime(2010, 12, 3)
        precipitation = TimeseriesStub()
        precipitation.add_value(today, 5)
        precipitation.add_value(tomorrow, 10)
        evaporation = TimeseriesStub()
        evaporation.add_value(today, 20)
        evaporation.add_value(tomorrow, 30)
        seepage = TimeseriesStub()
        seepage.add_value(today, 10)
        seepage.add_value(tomorrow, 20)
        events = [e for e in enumerate_events(precipitation,
                                              evaporation,
                                              seepage)]

        expected_events = [((today, 5), (today, 20), (today, 10)),
                           ((tomorrow, 10), (tomorrow, 30), (tomorrow, 20))]
        self.assertEqual(expected_events, events)

    def test_aa(self):
        """Test the case with timeseries that have different times."""
        today = datetime(2011, 11, 3, 0, 0)
        later_today = datetime(2011, 11, 3, 9, 0)
        timeseries = [TimeseriesStub((today, 2)),
                      TimeseriesStub((later_today, 4))]
        events = [event for event in enumerate_events(*timeseries)]
        self.assertEqual([((today, 2), (later_today, 4))], events)

    def test_b(self):
        """Test the case that the time series contain different dates"""
        today = datetime(2010, 12, 2)
        tomorrow = datetime(2010, 12, 3)
        precipitation = TimeseriesStub()
        precipitation.add_value(today, 5)
        evaporation = TimeseriesStub()
        evaporation.add_value(today, 10)
        evaporation.add_value(tomorrow, 30)
        events = [e for e in enumerate_events(precipitation, evaporation)]

        expected_events = [((today, 5), (today, 10)),
                           ((tomorrow, 0), (tomorrow, 30))]
        self.assertEqual(expected_events[0], events[0])
        self.assertEqual(expected_events[1], events[1])

    def test_c(self):
        """Test the case that the time series contains an empty time series"""
        today = datetime(2010, 12, 2)
        precipitation = TimeseriesStub()
        precipitation.add_value(today, 5)
        evaporation = TimeseriesStub()
        events = [e for e in enumerate_events(precipitation, evaporation)]

        expected_events = [((today, 5), (today, 0))]
        self.assertEqual(expected_events[0], events[0])

    def test_d(self):
        """Test the case that the time series contain different dates and an
        empty time series.

        """
        today = datetime(2010, 12, 2)
        tomorrow = datetime(2010, 12, 3)
        precipitation = TimeseriesStub()
        precipitation.add_value(today, 5)
        evaporation = TimeseriesStub()
        evaporation.add_value(today, 10)
        evaporation.add_value(tomorrow, 30)
        seepage = TimeseriesStub()
        events = [e for e in enumerate_events(precipitation,
                                              evaporation,
                                              seepage)]

        expected_events = [((today, 5), (today, 10), (today, 0)),
                           ((tomorrow, 0), (tomorrow, 30), (tomorrow, 0))]
        self.assertEqual(expected_events[0], events[0])
        self.assertEqual(expected_events[1], events[1])

    def test_e(self):
        """Test enumerate_events returns an empty list with an empty time
        series.

        """
        self.assertEqual([], list(enumerate_events(TimeseriesStub())))


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
