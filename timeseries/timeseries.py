#!/usr/bin/python
# -*- coding: utf-8 -*-
#******************************************************************************
#
# This file is part of the timeseries library.
#
# The timeseries library is free software: you can redistribute it and/or
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
# Copyright 2011 Nelen & Schuurmans
#
#******************************************************************************
#
# Initial programmer: Mario Frasca
# Initial date:       2011-09-13
# $Id$
#
#******************************************************************************

import logging
import datetime

logger = logging.getLogger(__name__)


class TimeSeries:
    """Describes a TimeSeries object.

    fields of TimeSeries shadow the content of <series> elements in
    PI files.

    you may argue that this ABC flatly follows a time series
    definition that is not necessarily the best usable in all cases,
    on the other hand, we already use that same definition in our Java
    code (where we don't even implement a complete own class, we just
    use the wldelft definition and make it more usable) and in R.
    """

    def get_events(self, start_date=None, end_date=None):
        """return all valid events in given range
        """

        if start_date is None:
            start_date = self.get_start_date()
        if end_date is None:
            end_date = self.get_end_date()
        return sorted([(k, v) for (k, v) in self.events.items()
                       if start_date <= k <= end_date])

    def __init__(self, events={}, **kwargs):
        ## one of: instantaneous, continuous.  we usually work with
        ## instantaneous
        self.type = kwargs.get('type')
        ## these are used to identify the TimeSeries in a collection
        self.location_id = kwargs.get('location_id')
        self.parameter_id = kwargs.get('parameter_id')
        ## datetime.timedelta or None (for nonequidistant)
        self.time_step = kwargs.get('time_step')
        ## what to store in equidistant timeseries in case a value is
        ## missing.
        self.miss_val = kwargs.get('miss_val')
        ## don't ask me why wldelft wants this one
        self.station_name = kwargs.get('station_name')
        ## geographic coordinates
        self.lat = kwargs.get('lat')
        self.lon = kwargs.get('lon')
        ## Rijksdriehoekscoördinaten
        self.x = kwargs.get('x')
        self.y = kwargs.get('y')
        self.z = kwargs.get('z')
        ## a string
        self.units = kwargs.get('units')
        ## key: timestamp, value: (double, flag, comment)
        self.events = {}  # not necessarily a dictionary, just
                          # anything associating a timestamp to a
                          # value
        pass

    def get_start_date(self):
        """return the first timestamp

        returned value must match the events data
        """

        timestamps = self.events.keys()
        try:
            return min(timestamps)
        except:
            return datetime.datetime(1970, 1, 1)

    def get_end_date(self):
        """return the last timestamp

        returned value must match the events data
        """

        timestamps = self.events.keys()
        try:
            return max(timestamps)
        except:
            return datetime.datetime(1970, 1, 1)

    @classmethod
    def as_dict(cls, input):
        """convert input to collection of TimeSeries

        input may be a PI file or just about anything that contains
        and defines a set of time series.

        output is a dictionary, where keys are the 2-tuple
        location_id/parameter_id and the values are the TimeSeries
        objects.
        """

        return {}

    @classmethod
    def as_list(cls, input):
        """convert input to collection of TimeSeries
        """

        return cls.as_dict(input).values()