# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring,missing-class-docstring
# pylint: disable=missing-function-docstring

from .. import plot_pkt_sizes_hypo


def test_dnsnamelengths_csvfile_getter():
    name_lengths = plot_pkt_sizes_hypo.DNSNameLengths("csvfile_name")
    assert name_lengths.csvfile == "csvfile_name"


def test_dnsnamelengths_csvfile_setter():
    name_lengths = plot_pkt_sizes_hypo.DNSNameLengths("csvfile_name")
    name_lengths.csvfile = "other_csvfile_name"
    assert name_lengths.csvfile == "other_csvfile_name"


def test_dnsnamelengths_get():
    name_lengths = plot_pkt_sizes_hypo.DNSNameLengths(
        plot_pkt_sizes_hypo.DEFAULT_STAT_FILE
    )
    print(name_lengths.get("dns_max"))
    assert name_lengths.get("dns_max")
