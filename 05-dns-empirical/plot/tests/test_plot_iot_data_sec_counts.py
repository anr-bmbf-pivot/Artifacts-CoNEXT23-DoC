#! /usr/bin/env python
#
# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

import pandas
import pytest

from .. import plot_iot_data_sec_counts
from .. import plot_iot_data_name_lens
from .. import plot_common as pc


__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


@pytest.mark.parametrize(
    "iot_data_csvs, exp_name_frag, msg_types, ancounts",
    [
        (["IoTFinder"], "iotfinder", None, None),
        (["MonIoTr"], "moniotr", None, None),
        (["YourThings"], "yourthings", None, None),
        (["dns_packets_ixp_2022_week"], "ixp", None, None),
        (
            ["10.1109-EuroSP48549.2020.00037", "MonIoTr"],
            "iotfinder+moniotr",
            None,
            None,
        ),
        (["10.1109-SP.2019.00013", "iotfinder"], "iotfinder+yourthings", None, None),
        (
            ["10.1145-3355369.3355577", "iotfinder", "yourthings"],
            "iotfinder+moniotr+yourthings",
            None,
            None,
        ),
        (["IoTFinder"], "iotfinder", 4 * ["query"], None),
        (["IoTFinder"], "iotfinder", None, [1, 2, 3, 4]),
    ],
)
def test_main(mocker, iot_data_csvs, exp_name_frag, msg_types, ancounts):
    savefig = mocker.patch("matplotlib.pyplot.savefig")
    mocker.patch("sys.argv", ["test"] + iot_data_csvs)
    if msg_types is None:
        msg_types = 4 * ["response"]
    if ancounts is None:
        ancounts = 4 * [1]

    mocker.patch(
        "pandas.read_csv",
        lambda *args, **kwargs: pandas.DataFrame(
            data={
                "pcap_name": 4 * ["test.pcap"],
                "frame_no": list(range(4)),
                "msg_type": msg_types,
                "name": [
                    "example.com.",
                    "example.org.",
                    "www.example.org.",
                    "www.example.com.",
                ],
                "rdata": 4 * [None],
                "qdcount": 4 * [1],
                "ancount": ancounts,
                "nscount": 4 * [0],
                "arcount": 4 * [0],
                "section": 4 * ["qd"],
                "transport": ["Do53", "Do53", "MDNS", "Do53"],
                "class": 4 * ["IN"],
                "type": ["A", "AAAA", "CNAME", "A"],
            }
        ),
    )

    plot_iot_data_sec_counts.main()
    # qrys_only, qd_an_only, qd_only and their respective no_mdns filters are skipped
    filters_count = len(plot_iot_data_name_lens.FILTERS) - 6
    if "ixp" in exp_name_frag:
        # all no_mdns filters are skipped
        filters_count /= 2
    assert savefig.call_count == filters_count * len(pc.OUTPUT_FORMATS)
    for i, ext in enumerate(pc.OUTPUT_FORMATS):
        assert f"@{exp_name_frag}.{ext}" in savefig.call_args_list[i][0][0]
