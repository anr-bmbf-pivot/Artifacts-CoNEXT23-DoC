#! /usr/bin/env python
#
# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

import pandas
import pytest

from .. import plot_iot_data_rr
from .. import plot_iot_data_name_lens
from .. import plot_common as pc

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


@pytest.mark.parametrize(
    "iot_data_csvs, exp_name_frag",
    [
        (["IoTFinder"], "iotfinder"),
        (["MonIoTr"], "moniotr"),
        (["YourThings"], "yourthings"),
        (["dns_packets_ixp_2022_week"], "ixp"),
        (["10.1109-EuroSP48549.2020.00037", "MonIoTr"], "iotfinder+moniotr"),
        (["10.1109-SP.2019.00013", "iotfinder"], "iotfinder+yourthings"),
        (
            ["10.1145-3355369.3355577", "iotfinder", "yourthings"],
            "iotfinder+moniotr+yourthings",
        ),
    ],
)
def test_main_no_others_list(mocker, iot_data_csvs, exp_name_frag):
    savefig = mocker.patch("matplotlib.pyplot.savefig")
    # libertine font in ACM style causes problems when running in tox/pytest
    mocker.patch("sys.argv", ["test", "-s", "mlenders_simple.mplstyle"] + iot_data_csvs)
    mocker.patch("plot.plot_iot_data_rr.open", side_effect=FileNotFoundError)

    mocker.patch(
        "pandas.read_csv",
        lambda *args, **kwargs: pandas.DataFrame(
            data={
                "msg_type": ["query"] + (3 * ["response"]),
                "name": [
                    "example.com.",
                    "example.org.",
                    "www.example.org.",
                    "www.example.com.",
                ],
                "rdata": 4 * [None],
                "section": 4 * ["qd"],
                "transport": ["Do53", "Do53", "MDNS", "Do53"],
                "class": 4 * ["IN"],
                "type": ["A", "AAAA", "CNAME", "A"],
            }
        ),
    )

    plot_iot_data_rr.main()
    if "ixp" == exp_name_frag:
        # only filters used are all, qrys_only, qd_only, qd_an_only
        filters_count = 4
    else:
        filters_count = len(plot_iot_data_name_lens.FILTERS)
        if "iotfinder" in exp_name_frag:
            # qrys_only and no_mdns_qrys_only are skipped
            filters_count -= 2
    assert savefig.call_count == filters_count * len(pc.OUTPUT_FORMATS)
    for i, ext in enumerate(pc.OUTPUT_FORMATS):
        assert f"@{exp_name_frag}.{ext}" in savefig.call_args_list[i][0][0]


def test_main_others_list(mocker):
    iot_data_csvs = ["MonIoTr"]
    exp_name_frag = "moniotr"
    savefig = mocker.patch("matplotlib.pyplot.savefig")
    mocker.patch("sys.argv", ["test", "-s", "mlenders_simple.mplstyle"] + iot_data_csvs)
    open_mock = mocker.mock_open(
        read_data="""
iotfinder:
  all:
    OPT: 0.0004785446227478921
    PTR: 0.38435108950368196
    RRSIG: 9.115135671388422e-05
    SOA: 0.026604802240864953
    TXT: 0.004899385423371276"""
    )
    mocker.patch("plot.plot_iot_data_rr.open", open_mock)

    mocker.patch(
        "pandas.read_csv",
        lambda *args, **kwargs: pandas.DataFrame(
            data={
                "msg_type": 26 * (["query"] + (3 * ["response"])),
                "name": 26
                * [
                    "example.com.",
                    "example.org.",
                    "www.example.org.",
                    "www.example.com.",
                ],
                "rdata": 104 * [None],
                "section": 104 * ["qd"],
                "transport": 104 * ["Do53"],
                "class": 104 * ["IN"],
                "type": ["A", "AAAA", "CNAME", "A"] + 100 * ["A"],
            }
        ),
    )

    plot_iot_data_rr.main()
    filters_count = len(plot_iot_data_name_lens.FILTERS)
    assert savefig.call_count == filters_count * len(pc.OUTPUT_FORMATS)
    for i, ext in enumerate(pc.OUTPUT_FORMATS):
        assert f"@{exp_name_frag}.{ext}" in savefig.call_args_list[i][0][0]
