#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import pixml


class CopyProcessor(pixml.SeriesProcessor):

    def process(self, series):
        """
        Simply return the series.
        """
        yield series


if __name__ == '__main__':
    exit(CopyProcessor().main())
