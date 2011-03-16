Changelog of timeseries
===================================================


0.3 (unreleased)
----------------

- Nothing changed yet.


0.2 (2011-03-16)
----------------

- The methods to enumerate the events of multiple time series could not handle
  time series whose dates had different time stamps, for example events at the
  dates 2011-03-16 at 00:00 and 2011-03-17 at 09:00. The enumeration would
  result in an (almost :) infinite loop. This has been fixed.

- The functions to enumerate monthly and average monthly events of a single
  time serie has been refactored to reduce the size of the code.


0.1 (2011-03-08)
----------------

- Removed "create_from_file".

- Initial library skeleton created by nensskel.  [Jack Ha]
