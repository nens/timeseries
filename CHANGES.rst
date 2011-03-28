Changelog of timeseries
===================================================


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
