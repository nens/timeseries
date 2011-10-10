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
from datetime import datetime
from datetime import timedelta
from xml.dom.minidom import parse
import re

logger = logging.getLogger(__name__)


class Pythonifier(object):
    """get a camelCaseString, return a python_style_string
    """

    def __init__(self):
        self.pattern = re.compile("([A-Z])")

    def __call__(self, text):
        return self.pattern.sub(r"_\1", text).lower()

pythonify = Pythonifier()


def str_to_datetime(date, time, offset=0):
    """convert date/time/offset to datetime
    """

    return datetime.strptime(date + 'T' + time, "%Y-%m-%dT%H:%M:%S") - timedelta(0, offset * 3600)


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
        self.events = dict(events)  # associate a timestamp to a
                                    # value, let's make a copy of it
        pass

    def get_start_date(self):
        """return the first timestamp

        returned value must match the events data
        """

        timestamps = self.events.keys()
        try:
            return min(timestamps)
        except:
            return datetime(1970, 1, 1)

    def get_end_date(self):
        """return the last timestamp

        returned value must match the events data
        """

        timestamps = self.events.keys()
        try:
            return max(timestamps)
        except:
            return datetime(1970, 1, 1)

    def add_value(self, tstamp, value):
        """set event, fall back to __setitem__
        """

        self.__setitem__(tstamp, value)

    def __setitem__(self, key, value):
        """behave as a dictionary
        """

        self.events[key] = value

    def __getitem__(self, key):
        """behave as a dictionary
        """

        return self.events[key]

    def get(self, key, default=None):
        """behave as a dictionary
        """

        return self.events.get(key, default)

    @classmethod
    def _from_xml(cls, stream):
        """private function

        convert an open input `stream` looking like a PI file into the
        result described in as_dict
        """

        def getText(node):
            return "".join(t.nodeValue for t in node.childNodes if t.nodeType == t.TEXT_NODE)

        def fromNode(node, names):
            '''extract text from included elements, replace capital
            letter with underscore + lower case letter, return
            dictionary'''

            return dict((pythonify(n.nodeName), getText(n))
                        for n in node.childNodes
                        if n.nodeName in set(names))

        dom = parse(stream)
        root = dom.childNodes[0]

        offsetNode = root.getElementsByTagName("timeZone")[0]
        offsetValue = float(getText(offsetNode))

        result = {}

        for seriesNode in root.getElementsByTagName("series"):
            headerNode = seriesNode.getElementsByTagName("header")[0]

            kwargs = fromNode(headerNode,
                              ['type', 'locationId', 'parameterId', 'missVal',
                               'stationName', 'lat', 'lon', 'x', 'y', 'z', 'units'])

            result[kwargs['location_id'], kwargs['parameter_id']] = obj = TimeSeries(**kwargs)

            for eventNode in seriesNode.getElementsByTagName("event"):
                date = eventNode.getAttribute("date")
                time = eventNode.getAttribute("time")
                value = float(eventNode.getAttribute("value"))
                obj[str_to_datetime(date, time, offsetValue)] = value

        return result

    @classmethod
    def as_dict(cls, input):
        """convert input to collection of TimeSeries

        input may be (the name of) a PI file or just about anything
        that contains and defines a set of time series.

        output is a dictionary, where keys are the 2-tuple
        location_id/parameter_id and the values are the TimeSeries
        objects.
        """

        if (isinstance(input, str) or hasattr(input, 'read')):
            ## a string or a file, maybe PI?
            result = cls._from_xml(input)
        else:
            result = None

        return result

    @classmethod
    def as_list(cls, input):
        """convert input to collection of TimeSeries
        """

        return cls.as_dict(input).values()
