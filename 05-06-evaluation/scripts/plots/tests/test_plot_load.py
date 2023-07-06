# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring,missing-class-docstring
# pylint: disable=missing-function-docstring

import logging

from .. import plot_baseline

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


def test_array_ordered_by_query_time__too_little_queries(caplog):
    with caplog.at_level(logging.ERROR):
        plot_baseline.array_ordered_by_query_time([[0.1]], 2)
    assert "#0 has too little queries (1)" in caplog.text
    with caplog.at_level(logging.ERROR):
        plot_baseline.array_ordered_by_query_time([[0.1, 0.2]], 3, [({}, "file")])
    assert "file has too little queries (2)" in caplog.text
