#! /usr/bin/env python
#
# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

import pandas
import pytest

from .. import plot_iot_data_resp_lens
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
def test_main_base(mocker, iot_data_csvs, exp_name_frag):
    savefig = mocker.patch("matplotlib.pyplot.savefig")
    mocker.patch("sys.argv", ["test"] + iot_data_csvs)

    mocker.patch(
        "pandas.read_csv",
        lambda *args, **kwargs: pandas.DataFrame(
            data={
                "pcap_name": 4 * ["test.pcap"],
                "frame_no": list(range(4)),
                "msg_type": 4 * ["response"],
                "msg_len": [44, 45, 46, 47],
                "name": [
                    "example.com.",
                    "example.org.",
                    "www.example.org.",
                    "www.example.com.",
                ],
                "rdata": 4 * [None],
                "section": 4 * ["qd"],
                "transport": ["Do53", "Do53", "MDNS", "Do53"],
                "type": 4 * ["A"],
            }
        ),
    )

    plot_iot_data_resp_lens.main()
    if "ixp" == exp_name_frag:
        # only filter used is all
        filters_count = 1
    else:
        # qd_an_only, qrys_only, no_mdns_qd_an_only, no_mdns_qrys_only filters are
        # always skipped
        filters_count = len(plot_iot_data_name_lens.FILTERS) - 4
    assert savefig.call_count == filters_count * len(pc.OUTPUT_FORMATS)
    for i, ext in enumerate(pc.OUTPUT_FORMATS):
        assert f"@{exp_name_frag}.{ext}" in savefig.call_args_list[i][0][0]


def test_main_no_name_lens(mocker):
    iot_data_csvs = ["10.1109-EuroSP48549.2020.00037", "MonIoTr"]
    savefig = mocker.patch("matplotlib.pyplot.savefig")
    mocker.patch("sys.argv", ["test"] + iot_data_csvs)

    mocker.patch(
        "pandas.read_csv",
        lambda *args, **kwargs: pandas.DataFrame(
            data={
                "pcap_name": 4 * ["test.pcap"],
                "frame_no": list(range(4)),
                "msg_type": 4 * ["query"],
                "msg_len": [44, 45, 46, 47],
                "name": [
                    "example.com.",
                    "example.org.",
                    "www.example.org.",
                    "www.example.com.",
                ],
                "rdata": 4 * [None],
                "section": 4 * ["qd"],
                "transport": ["Do53", "Do53", "MDNS", "Do53"],
                "type": 4 * ["A"],
            }
        ),
    )

    plot_iot_data_resp_lens.main()
    savefig.assert_not_called()


def test_main_too_long_names(mocker, capsys):
    iot_data_csvs = ["10.1109-SP.2019.00013", "iotfinder", "yourthings"]
    exp_name_frag = "iotfinder+yourthings+yourthings"
    savefig = mocker.patch("matplotlib.pyplot.savefig")
    mocker.patch("sys.argv", ["test"] + iot_data_csvs)

    mocker.patch(
        "pandas.read_csv",
        lambda *args, **kwargs: pandas.DataFrame(
            data={
                "pcap_name": 4 * ["test.pcap"],
                "frame_no": list(range(4)),
                "msg_type": 4 * ["response"],
                "msg_len": [44, 45, 1520, 1520],
                "name": [
                    "example.com.",
                    "example.org.",
                    "www.example.org.",
                    "www.example.com.",
                ],
                "rdata": 4 * [None],
                "section": 4 * ["qd"],
                "transport": ["Do53", "Do53", "MDNS", "Do53"],
                "type": 4 * ["A"],
            }
        ),
    )

    plot_iot_data_resp_lens.main()
    # qd_an_only, qrys_only, no_mdns_qd_an_only, no_mdns_qrys_only filters are
    # always skipped
    filters_count = len(plot_iot_data_name_lens.FILTERS) - 4
    assert savefig.call_count == filters_count * len(pc.OUTPUT_FORMATS)
    for i, ext in enumerate(pc.OUTPUT_FORMATS):
        assert f"@{exp_name_frag}.{ext}" in savefig.call_args_list[i][0][0]
    assert "WILL NOT BE PLOTTED! 1520" in capsys.readouterr().out
