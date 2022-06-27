# Copyright (C) 2021-22 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import sys

import pytest

from .. import parse_load_results
from .. import plot_load
from .. import plot_load_cdf
from .. import plot_pkt_sizes

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021-22 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


@pytest.fixture
def parse_load_fixture(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["cmd"])
    parse_load_results.main()
    yield


def test_plot_load(monkeypatch, parse_load_fixture):
    monkeypatch.setattr(sys, "argv", ["cmd"])
    plot_load.main()


def test_plot_load_cdf(monkeypatch, parse_load_fixture):
    monkeypatch.setattr(sys, "argv", ["cmd"])
    plot_load_cdf.main()


def test_plot_pkt_sizes(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["cmd"])
    plot_pkt_sizes.main()
