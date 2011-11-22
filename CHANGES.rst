Changelog of timeseries
===================================================


0.10 (2011-11-22)
-----------------

- Added abs(TimeSeries).


0.9 (2011-11-21)
----------------

- Changed some functions of TimeSeries.

- Added tests.


0.8.3 (2011-11-16)
------------------

- Added MANIFEST.in.


0.8.1 (2011-11-16)
------------------

- Added tests.


0.8 (2011-11-16)
----------------

- Added timeseries.py with Django support.

- Added time_step attribute to _from_django_QuerySet.

- Added matplotlib tot syseggs in buildout.cfg. Matplotlib is required
  by library nens.


0.7 (2011-07-18)
----------------

- Implemented function map_timeseries which applies a given function to each
  value of a given time series and returns the resulting time series.
- Fixed an error in the implementation of method
  SparseTimeseriesStub::events. This fixes the problem in the app
  lizard_waterbalance that sometimes the time series of intakes and pumps were
  appeared empty (ticket 3020).


0.6 (2011-05-31)
----------------

- Fixed an error in the computation of cumulative event values.


0.5 (2011-04-19)
----------------

- Fixed TimeseriesStub.events and TimeseriesWithMemoryStub.events, which did
  not take the given start and end date into account
- Implemented SparseTimeseriesStub to store a contiguous time serie in less
  memory; functions add_timeseries, multiply_timeseries, split_timeseries and
  subtract_timeseries returns these time series instead of the more memory
  hungry TimeseriesStub.


0.4 (2011-04-06)
----------------

- Fixed method TimeseriesRestrictedStub.events so it does not ignore the
  specified start and end.
- Fixed the function that computes the first date of the hydro year of a given
  event.
- Removed functionality specifically for the display of a graph for cumulative
  discharges. This functionality does not belongs in a low-level library such
  as timeseries.


0.3 (2011-03-28)
----------------

- Implemented support for the enumeration of the events of a dictionary of
  timeseries.

- Added support for the addition of any number of time series to function
  add_timeseries.

- Added support to the different event functions for an explicit start and end
  date.


0.2 (2011-03-16)
----------------

- Fixed the methods to enumerate the events of multiple time series. Previously
  they could not handle time series whose dates had different time stamps, for
  example events at the dates 2011-03-16 at 00:00 and 2011-03-17 at 09:00. The
  enumeration would result in an (almost :) infinite loop.

- Refactored the functions to enumerate monthly and average monthly events of a
  single time serie to reduce the size of the code.


0.1 (2011-03-08)
----------------

- Removed "create_from_file".

- Initial library skeleton created by nensskel.  [Jack Ha]
