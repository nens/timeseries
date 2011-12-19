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

import logging
import itertools
import timeseries

from copy import deepcopy
from datetime import datetime
from datetime import timedelta
from math import fabs

from timeseries import daily_events
from timeseries import TimeSeries

logger = logging.getLogger(__name__)


def _first_of_day(event):
    """Return the first moment of the day for an event.

    >>> _first_of_day((datetime(1999, 10, 2, 3, 4), 0.0))
    datetime.datetime(1999, 10, 2, 0, 0)
    """
    date, value = event
    return datetime(date.year, date.month, date.day)


def _first_of_month(event):
    """Return the first day of the month for an event.

    >>> _first_of_month((datetime(1999, 10, 2, 3, 4), 0.0))
    datetime.datetime(1999, 10, 1, 0, 0)
    """
    date, value = event
    return datetime(date.year, date.month, 1)


def _first_of_quarter(event):
    """Return the first day of the quarter for an event.

    The first day of a quarter is returned:

      >>> dt = datetime(1972, 12, 25)
      >>> _first_of_quarter((dt, 'reinout'))
      datetime.datetime(1972, 10, 1, 0, 0)

      >>> dt = datetime(1972, 10, 1)
      >>> _first_of_quarter((dt, 'bla'))
      datetime.datetime(1972, 10, 1, 0, 0)

      >>> dt = datetime(1976, 01, 27)
      >>> _first_of_quarter((dt, 'maurits'))
      datetime.datetime(1976, 1, 1, 0, 0)

    """
    date, value = event
    month = 1 + ((date.month - 1) / 3 * 3)
    return datetime(date.year, month, 1)


def _first_of_year(event):
    """Return the first day of the year for an event.

    >>> _first_of_year((datetime(1999, 10, 2, 3, 4), 0.0))
    datetime.datetime(1999, 1, 1, 0, 0)
    """
    date, value = event
    return datetime(date.year, 1, 1)


def _first_of_hydro_year(event):
    """Return the first day of the year for an event.
    Hydrologic year starts in October!

    >>> _first_of_hydro_year((datetime(1999, 10, 2, 3, 4), 0.0))
    datetime.datetime(1999, 10, 1, 0, 0)
    >>> _first_of_hydro_year((datetime(1999, 9, 2, 3, 4), 0.0))
    datetime.datetime(1998, 10, 1, 0, 0)
    """
    date, value = event
    if date < datetime(date.year, 10, 1):
        year = date.year - 1
    else:
        year = date.year
    return datetime(year, 10, 1)


def grouped_event_values(timeseries, period, average=False):
    """Return iterator with totals for days/months/years for timeseries.

    Aggregation function is sum.
    Optional: take average.

    >>> ts = TimeseriesStub()  # empty timeseries
    >>> [i for i in grouped_event_values(ts, 'day')]
    []
    >>> [i for i in grouped_event_values(ts, 'month')]
    []
    >>> [i for i in grouped_event_values(ts, 'quarter')]
    []
    >>> [i for i in grouped_event_values(ts, 'year')]
    []
    >>> [i for i in grouped_event_values(ts, 'not_a_period')]
    Traceback (most recent call last):
       ...
    AssertionError
    >>>

    """

    groupers = {'year': _first_of_year,
                'month': _first_of_month,
                'quarter': _first_of_quarter,
                'day': _first_of_day}
    grouper = groupers.get(period)
    assert grouper is not None

    for date, events in itertools.groupby(timeseries.events(), grouper):
        if average:
            # To be able to count the events, we make a list of the
            # generated elements. There are ways to count them without
            # having to make the list explicit but this is the easy
            # way.
            events = list(events)
            result = (sum(value for (date, value) in events) /
                      (1.0 * len(events)))
        else:
            result = sum(value for (date, value) in events)
        yield date, result


def cumulative_event_values(timeseries, reset_period, period='month',
                            multiply=1, time_shift=0):
    """Return iterator with major events and at least with interval.

    cumulative is reset on reset_period

    Aggregation function is sum.
    Optional: take average.
    """
    if reset_period == 'hydro_year' and period == 'year':
        # This is a really strange combination for which the rest of this
        # function is not suited. We fix that as follows.
        period = 'hydro_year'

    # When the reset period is smaller than the group period, it is possible
    # that the grouper returns a date before the date of the resetter, for
    # example when the reset period is a month and the group period a
    # quarter. But to which cumulative time series should this lead?
    #
    # To "fix" this problem, we use the following rule:
    #
    #    When the reset period is smaller than the group period, use the reset
    #    period also for the group period.
    #
    # In this way, the user always sees the reset.

    keys = ['day', 'month', 'quarter', 'hydro_year', 'year']
    if keys.index(reset_period) < keys.index(period):
        period = reset_period

    firsters = {'year': _first_of_year,
                'hydro_year': _first_of_hydro_year,
                'month': _first_of_month,
                'quarter': _first_of_quarter,
                'day': _first_of_day}
    reseter = firsters.get(reset_period)
    assert reseter is not None

    grouper = firsters.get(period)
    assert grouper is not None

    cumulative = 0
    time_shift = timedelta(time_shift)
    for date, events in itertools.groupby(timeseries.events(), reseter):
        cumulative = 0
        for cum_date, cum_events in itertools.groupby(events, grouper):
            cumulative += sum(value for (date, value) in cum_events)
            yield (cum_date + time_shift), cumulative * multiply


def monthly_events(timeseries):
    """Return a generator to iterate over all monthly events.

    A TimeseriesStub stores daily events. This generator aggregates these
    daily events to monthly events. Each monthly events takes place on the
    first of the month and its value is the total value of the daily events
    for that month.

    """
    return grouped_event_values(timeseries, 'month')


def average_monthly_events(timeseries):
    """Return a generator to iterate over all average monthly events.

    A TimeseriesStub stores daily events. This generator aggregates these
    daily events to monthly events that is placed at the first of the month
    and whose value is the average value of the daily events for that month.

    """
    return grouped_event_values(timeseries, 'month', average=True)


def daily_sticky_events(events):
    """Return a generator to iterate over all daily events.

    The generator iterates over the events in the order they were added. If
    dates are missing in between two successive events, this function fills in
    the missing dates with the value on the latest known date.

    Parameters:
      *events*
        sequence of (date or datetime, value) pairs ordered by date or datetime

    """
    # We initialize this variable to silence pyflakes.
    date_to_yield = None
    previous_value = 0
    for date, value in events:
        if not date_to_yield is None:
            while date_to_yield < date:
                yield date_to_yield, previous_value
                date_to_yield = date_to_yield + timedelta(1)
        yield date, value
        previous_value = value
        date_to_yield = date + timedelta(1)


class TimeseriesStub(timeseries.TimeSeries):
    """Implements a time series for testing.

    A time series is a sequence of values ordered by date and time.

    Instance variables:
     *initial_value*
      value on any date before the first date
     *events*
      list of (date and time, value) tuples ordered by date and time

    """
    def __init__(self, *events):
        if len(events) == 0:
            events = []
        self._events = events

    def get_start_date(self):
        """Return the initial date and time.

        The returned value must match the events data.
        """
        try:
            return self._events[0][0]
        except:
            return datetime(1970, 1, 1)

    def get_end_date(self):
        """Return the final date and time.

        The returned value must match the events data.
        """
        try:
            return self._events[-1][0]
        except:
            return datetime(1970, 1, 1)

    def sorted_event_items(self):
        """return all items, sorted by key
        """
        return list(self.events())

    def get_value(self, date_time):
        """Return the value on the given date and time.

        Note that this method assumes that the events are ordered earliest date
        and time first.

        """
        result = 0.0
        events = (event for event in self._events if event[0] >= date_time)
        event = next(events, None)
        if not event is None:
            if event[0] == date_time:
                result = event[1]
        return result

    def add_value(self, date_time, value):
        """Add the given value for the given date and time.

        Please note that events should be added earliest date and time first.

        """
        self._events.append((date_time, value))

    def raw_events(self):
        """Return a generator to iterate over all daily events.

        The generator iterates over the events in the order they were
        added. If dates are missing in between two successive events,
        this function does not fill in the missing dates with value.

        """
        for date, value in self._events:
            yield date, value

    def raw_events_dict(self):
        return dict(self.raw_events())

    def events(self, start_date=None, end_date=None):
        """Return a generator to iterate over the requested daily events.

        The generator iterates over the events in the order they were
        added. If dates are missing in between two successive events,
        this function fills in the missing dates with value 0.

        """
        if start_date is not None and end_date is not None:
            for date, value in daily_events(self._events):
                if start_date is not None and date < start_date:
                    continue
                if end_date is not None and date < end_date:
                    yield date, value
                else:
                    break
        else:
            for date, value in daily_events(self._events):
                yield date, value

    def get_events(self, start_date=None, end_date=None):
        return self.events(start_date, end_date)

    def monthly_events(self):
        """Return a generator to iterate over all monthly events.

        A TimeseriesStub stores daily events. This generator aggregates these
        daily events to monthly events. Each monthly events takes place on the
        first of the month and its value is the total value of the daily events
        for that month.

        """
        return grouped_event_values(self, 'month')

    def __eq__(self, other):
        """Return True iff the two given time series represent the
        same events."""
        my_events = list(self.events())
        your_events = list(other.events())
        equal = len(my_events) == len(your_events)
        if equal:
            for (my_event, your_event) in zip(my_events, your_events):
                equal = my_event[0] == your_event[0]
                if equal:
                    equal = fabs(my_event[1] - your_event[1]) < 1e-6
                if not equal:
                    break
        return equal


class SparseTimeseriesStub(timeseries.TimeSeries):
    """Represents a continuous time series.

    A continuous time series is a sequence of values ordered by date and time
    where each event is the day after the first event.

    Instance variables:
      *first_date*
        date of the first event
      *previous_date*
        date of the last event that has been added
      *values*
        list of values

    """
    def __init__(self, first_date=None, values=None):
        self.first_date = first_date
        if values is None:
            self.values = []
        else:
            self.values = values
            self.previous_date = self.first_date + timedelta(len(values) - 1)

    def get_start_date(self):
        """Return the initial date and time.

        The returned value must match the events data.
        """
        if not self.first_date is None:
            return self.first_date
        else:
            return datetime(1970, 1, 1)

    def get_end_date(self):
        """Return the final date and time.

        The returned value must match the events data.
        """
        if not self.first_date is None:
            return self.first_date + timedelta(len(self.values) - 1)
        else:
            return datetime(1970, 1, 1)

    def sorted_event_items(self):
        """return all items, sorted by key
        """
        return list(self.events())

    def add_value(self, date_time, value):
        """Add the given value for the given date and time.

        Please note that events should be added earliest date and time first.

        """
        if self.first_date is None:
            self.first_date = date_time
        else:
            assert self.previous_date is not None
            next_expected_date = self.previous_date + timedelta(1)
            assert next_expected_date.isocalendar() == date_time.isocalendar()
        self.previous_date = date_time
        self.values.append(value)

    def events(self, start_date=None, end_date=None):
        """Return a generator to iterate over the requested daily events.

        The generator iterates over the events in the order they were
        added. If dates are missing in between two successive events,
        this function fills in the missing dates with value 0.

        """
        current_date = self.first_date
        if start_date is not None and end_date is not None:
            if current_date == start_date:
                for value in self.values:
                    if current_date < end_date:
                        yield current_date, value
                        current_date = current_date + timedelta(1)
                    else:
                        break
            else:
                for value in self.values:
                    if current_date < start_date:
                        pass
                    elif current_date < end_date:
                        yield current_date, value
                    else:
                        break
                    current_date = current_date + timedelta(1)
        else:
            for value in self.values:
                yield current_date, value
                current_date = current_date + timedelta(1)

    def get_events(self, start_date=None, end_date=None):
        return self.events(start_date, end_date)


class TimeseriesWithMemoryStub(TimeseriesStub):

    def __init__(self, *args, **kwargs):
        TimeseriesStub.__init__(self, *args, **kwargs)

    def get_value(self, date_time):
        """Return the value on the given date and time.

        Note that this method assumes that the events are ordered earliest date
        and time first.

        """
        result = 0.0
        previous_event = None
        # note that we traverse the list of events in reverse
        for event in reversed(self._events):
            if event[0] < date_time:
                if previous_event is None:
                    result = event[1]
                else:
                    result = previous_event[1]
                break
            elif event[0] == date_time:
                result = event[1]
                previous_event = event
        return result

    def events(self, start_date=None, end_date=None):
        """Return a generator to iterate over all daily events.

        The generator iterates over the events in the order they were added. If
        dates are missing in between two successive events, this function fills
        in the missing dates with the value on the latest known date.

        """
        if start_date is not None and end_date is not None:
            for date, value in daily_sticky_events(self._events):
                if start_date is not None and date < start_date:
                    continue
                if end_date is not None and date < end_date:
                    yield date, value
                else:
                    break
        else:
            for date, value in daily_sticky_events(self._events):
                yield date, value


class TimeseriesRestrictedStub(TimeseriesStub):
    """Represents a time series that lies between specific dates.

    A time series is a sequence of values ordered by date and time.

    Instance variables:
      *timeseries*
        object that supports an events method
      *start_date*
        date of the first day of the time series
      *end_date*
        date of the day *after* the last day of the time series

    """
    def __init__(self, *args, **kwargs):
        self.timeseries = kwargs["timeseries"]
        del kwargs["timeseries"]
        self.start_date = kwargs["start_date"]
        del kwargs["start_date"]
        self.end_date = kwargs["end_date"]
        del kwargs["end_date"]
        TimeseriesStub.__init__(self, *args, **kwargs)

    def get_start_date(self):
        """Return the initial date and time.

        The returned value must match the events data.
        """
        start_event = next(self.events(), (datetime(1970, 1, 1), 0))
        return start_event[0]

    def get_end_date(self):
        """Return the final date and time.

        The returned value must match the events data.
        """
        end_date = self.timeseries.get_end_date()
        if end_date > self.end_date:
            end_date = self.end_date
        return end_date

    def events(self, start_date=None, end_date=None):
        """Return a generator to iterate over the requested events.

        Parameters:
          *start_date*
            date of the earliest event to iterate over
          *end_data*
            date of the date after the latest event to iterate over
        """
        events = self.timeseries.events(start_date=self.start_date,
                                        end_date=self.end_date)
        if start_date is None and end_date is None:
            for event in events:
                yield event[0], event[1]
        else:
            for event in events:
                if not start_date is None and event[0] < start_date:
                    continue
                if not end_date is None and event[0] < end_date:
                    yield event[0], event[1]
                else:
                    break


def enumerate_events(*timeseries_list):
    """Yield the events for all the days of the given time series.

    Parameters:
      *timeseries_list*
        list of time series

    Each of the given time series should specify values for possibly
    non-continous ranges of dates. For each day present in a time series, this
    method yields a tuple of events of all time series. If that day is present
    in a time series, the tuple contains the corresponding event. If that day
    is not present, the tuple contains an event with value 0 at that day.

    The description above only mentions dates. However, this method can handle
    events whose 'date' include a time component *as long as* the 'date' object
    supports an isocalendar() method as datetime.date and datetime.datetime do.

    """
    next_start = datetime.max
    for timeseries in timeseries_list:
        start = next((event[0] for event in timeseries.events()), None)
        if not start is None:
            next_start = min(next_start, start)

    if next_start == datetime.max:
        # none of the time series contains an event and we stop immediately
        return

    # next_start is the first date for which an event is specified

    events_list = [timeseries.events() for timeseries in timeseries_list]
    earliest_event_list = [next(events, None) for events in events_list]

    timeseries_count = len(timeseries_list)

    no_events_are_present = False
    while not no_events_are_present:
        no_events_are_present = True
        to_yield = [(next_start, 0.0)] * timeseries_count
        for index, earliest_event in enumerate(earliest_event_list):
            if not earliest_event is None:
                no_events_are_present = False
                if earliest_event[0].isocalendar() == next_start.isocalendar():
                    to_yield[index] = earliest_event
                    earliest_event_list[index] = next(events_list[index], None)
        next_start = next_start + timedelta(1)
        if not no_events_are_present:
            yield tuple(to_yield)


def enumerate_dict_events(timeseries_dict):
    """Yield the events for all the days of the given time series.

    Parameter:
      *timeseries_dict*
        dictionary where a value is
          - a timeseries or
          - a dictionary where **each** value is a timeseries

    Each of the given time series should specify values for possibly
    non-continous ranges of dates. For each day present in a time series, this
    method yields a tuple of events of all time series. If that day is present
    in a time series, the tuple contains the corresponding event. If that day
    is not present, the tuple contains an event with value 0 at that day.

    The description above only mentions dates. However, this method can handle
    events whose 'date' include a time component *as long as* the 'date' object
    supports an isocalendar() method as datetime.date and datetime.datetime do.

    """
    next_start = datetime.max
    #get earliest moment
    for timeseries in timeseries_dict.values():
        if not type(timeseries) == type({}):
            start = next((event[0] for event in timeseries.events()), None)
        else:
            for ts_nested in timeseries.values():
                start = next((event[0] for event in ts_nested.events()), None)
        if not start is None:
            next_start = min(next_start, start)

    if next_start == datetime.max:
        # none of the time series contains an event and we stop immediately
        return

    # next_start is the first date for which an event is specified
    events_list = []
    keys_list = []
    for key, timeseries in timeseries_dict.items():
        if not type(timeseries) == type({}):
            events_list.append(timeseries.events())
            keys_list.append([key])
        else:
            #nested timeserie
            for key_nested, timeseries_nested in timeseries.items():
                events_list.append(timeseries_nested.events())
                keys_list.append([key, key_nested])

    earliest_event_list = [next(events, None) for events in events_list]

    no_events_are_present = False
    while not no_events_are_present:
        no_events_are_present = True
        to_yield = {'date': next_start}
        for key in keys_list:
            if len(key) == 1:
                to_yield[key[0]] = (next_start, 0.0)
            else:
                if key[0] not in to_yield:
                    to_yield[key[0]] = {}
                to_yield[key[0]][key[1]] = (next_start, 0.0)

        for index, earliest_event in enumerate(earliest_event_list):
            if not earliest_event is None:
                no_events_are_present = False
                if earliest_event[0].isocalendar() == next_start.isocalendar():
                    if len(keys_list[index]) == 1:
                        to_yield[keys_list[index][0]] = earliest_event
                    else:
                        if keys_list[index][0] not in to_yield:
                            to_yield[keys_list[index][0]] = {}
                        to_yield[keys_list[index][0]][keys_list[index][1]] = \
                             earliest_event
                    earliest_event_list[index] = next(events_list[index], None)
        next_start = next_start + timedelta(1)
        if not no_events_are_present:
            yield to_yield


def enumerate_merged_events(timeseries_a, timeseries_b):
    """Yields all triples *(date, value_a, value_b)* for the given time series.

    In *(date, value_a, value_b)*, *value_a* is the value of the event at
    *date* in *timeseries_a* and *value_b* the value of the event at *date* in
    *timeseries_b*.

    Note that the given time series can have different date ranges. Therefore
    it is possible one time series specifies a value at a date outside the date
    range of the other time series. In that case, this method does return a
    triple for that date and it uses the value 0 for the missing value.

    Parameters:
      *timeseries_a*
        object that supports a method events() to yield events
      *timeseries_b*
        object that supports a method events() to yield events

    """
    events_a = timeseries_a.events()
    events_b = timeseries_b.events()
    event_a = next(events_a, None)
    event_b = next(events_b, None)
    while not event_a is None and not event_b is None:
        if event_a[0].isocalendar() < event_b[0].isocalendar():
            yield event_a[0], event_a[1], 0
            event_a = next(events_a, None)
        elif event_a[0].isocalendar() > event_b[0].isocalendar():
            yield event_b[0], 0, event_b[1]
            event_b = next(events_b, None)
        else:
            yield event_a[0], event_a[1], event_b[1]
            event_a = next(events_a, None)
            event_b = next(events_b, None)
    if event_a is None:
        if not event_b is None:
            yield event_b[0], 0, event_b[1]
        for event in events_b:
            yield event[0], 0, event[1]
    else:
        if not event_a is None:
            yield event_a[0], event_a[1], 0
        for event in events_a:
            yield event[0], event[1], 0


def create_empty_timeseries(timeseries):
    """Return the empty TimeseriesStub that starts on the same day as
    the given time series.

    If the given time series is non-empty, this function returns a
    TimeseriesStub with a single event that starts on the day as the
    given time series and which has value 0.0. If the given time
    series is empty, this function returns an empty TimeseriesStub.

    """
    empty_timeseries = TimeseriesStub()
    event = next(timeseries.events(), None)
    if not event is None:
        empty_timeseries.add_value(event[0], 0.0)
    return empty_timeseries


def add_timeseries(*args):
    """Return the TimeseriesStub that is the sum of the given time series."""
    result = SparseTimeseriesStub()
    for events in enumerate_events(
        *args):
        date = events[0][0]
        value = sum([value[1] for value in events])

        result.add_value(date, value)
    return result


def subtract_timeseries(timeseries_a, timeseries_b):
    """Return the TimeseriesStub that is the difference of the given
    time series."""
    result = SparseTimeseriesStub()
    for date, value_a, value_b in enumerate_merged_events(
        timeseries_a, timeseries_b):

        result.add_value(date, value_a - value_b)
    return result


def multiply_timeseries(timeseries, value):
    """Return the product of the given time series with the given value.

    """
    product = SparseTimeseriesStub()
    for event in timeseries.events():
        product.add_value(event[0], event[1] * value)
    return product


def map_timeseries(timeseries, map_function):
    """Apply the given map function to each value of the given time series.

    This method returns a time series.

    """
    product = SparseTimeseriesStub()
    for time, value in timeseries.events():
        product.add_value(time, map_function(value))
    return product


def split_timeseries(timeseries):
    """Return the 2-tuple of non-positive and non-negative time series.

    Parameters:
      *timeseries*
        time series that contains the events for the new 2 -tuple

    This function creates a 2-tuple of TimeseriesStub, where the first
    element contains all non-positive events (of the given time
    series) and the second element contains all non-negative
    events. The 2 resulting time series have events for the same dates
    as the given time series, but with value zero if the value at that
    date does not have the right sign.

    """
    non_pos_timeseries = SparseTimeseriesStub()
    non_neg_timeseries = SparseTimeseriesStub()
    for (date, value) in timeseries.events():
        if value > 0:
            non_pos_timeseries.add_value(date, 0)
            non_neg_timeseries.add_value(date, value)
        elif value < 0:
            non_pos_timeseries.add_value(date, value)
            non_neg_timeseries.add_value(date, 0)
        else:
            non_pos_timeseries.add_value(date, 0)
            non_neg_timeseries.add_value(date, 0)
    return (non_pos_timeseries, non_neg_timeseries)


def write_to_pi_file(*args, **kwargs):
    """Write the given timeseries in PI XML format.

    Parameters:
      *kwargs['filename']*
        name of PI XML file to create and write to
      *kwargs['timeseries']*
        single time series, or a dict of time series, where each time series
        has with a method 'events' to generate all date, value pairs

    """
    multiple_series_stub = kwargs['timeseries']
    if isinstance(multiple_series_stub, dict):
        multiple_series = []
        for parameter_id, series_stub in multiple_series_stub.iteritems():
            my_kwargs = deepcopy(kwargs)
            my_kwargs["parameter_id"] = parameter_id
            series = TimeSeries(*args, **my_kwargs)
            series.sorted_event_items = lambda s=series_stub: list(s.events())
            multiple_series.append(series)
        multiple_series.sort(key=lambda series: series.parameter_id)
    else:
        series = TimeSeries(*args, **kwargs)
        series.sorted_event_items = lambda: list(multiple_series_stub.events())
        multiple_series = [series]

    TimeSeries.write_to_pi_file(kwargs['filename'], multiple_series)
