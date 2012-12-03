Changelog of timeseries
===================================================


0.21.1 (2012-12-03)
-------------------

- Fix writing incorrect missval to binary format


0.21 (2012-11-29)
-----------------

- Add support for binary pixml

- Add script for yearday statistics.


0.20.10 (2012-11-14)
--------------------

- Change the way the output files are named.


0.20.9 (2012-11-14)
-------------------

- Change percentiles, now it takes directories as arguments.


0.20.8 (2012-11-13)
-------------------

- Nothing changed yet.


0.20.7 (2012-11-13)
-------------------

- Add script to build zips to be deployed on fews machines.


0.20.7 (2012-11-13)
-------------------

- Moved statistics code to subfolder adapters,
- Split out the code for reading and writing.


0.20.6 (2012-11-13)
-------------------

- Fixes to statistics:
    - Use text to select part of tree when writing
    - Use old fashioned formatting for parameter name
    


0.20.5 (2012-11-08)
-------------------

- Code cleaned up
- Range (start, end, step) elements now always placed
  after third header element.


0.20.4 (2012-11-07)
-------------------

- Make statistics module work standalone
- Fix error with arguments (due to unreliable console_scripts actions)


0.20.3 (2012-11-07)
-------------------

- Correct header elements order.


0.20.2 (2012-10-31)
-------------------

- bin/percentiles now accepts multiple timeseries in a file.


0.20.1 (2012-10-17)
-------------------

- Nothing changed yet.


0.20 (2012-10-17)
-----------------

- Add statistics module and console script to generate timeseries
  statistics.


0.19 (2012-06-25)
-----------------

- Added timeseries.__delitem__ for deleting items as a dictionary.


0.18 (2012-06-13)
-----------------

- Use etree instead of minidom for parsing and writing timeseries.
- Fix some tests and remove some overdone tests.


0.17 (2012-03-22)
-----------------

- Sets the logging level to log the use of a deprecated function to debug (from
  warn) (nens/vss#92)


0.16 (2012-02-08)
-----------------

- Added option TimeSeries.get_events(dates=[...]) to get events from
  only the provided list of dates.


0.15 (2011-12-22)
-----------------

- Updates TimeseriesRestrictedStub so its methods get_start_date and
  get_end_date return the right value (#15).

- Fixes the equality operator for SparseTimeseriesStub



0.14 (2011-12-14)
-----------------

- Updates TimeSeries.events to fill in missing values as method
  TimeseriesStub.events does (#14).

- Fixes the problem that a timeseries read from an XML file still contains
  the values that are specified as missing values (#13).


0.13 (2011-12-08)
-----------------

- Improved detection of Django QuerySet.


0.12 (2011-11-29)
-----------------

- Fixes the problem that under Windows, a PI XML file written by
  TimeSeries.write_to_pi_file contained the empty string for each time tag
  (#12).


0.11 (2011-11-24)
-----------------

- Implemented option TimeSeries.is_locf, Last Observation Carried
  Forward: Now we can do operations on non-equidistant timeseries.


0.10.1 (2011-11-22)
-------------------

- Nothing changed yet.


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
