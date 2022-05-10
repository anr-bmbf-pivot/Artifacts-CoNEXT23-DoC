#! /usr/bin/env python
#
# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

import pandas
import pytest

from .. import plot_iot_data_hostname_lens
from .. import plot_iot_data_name_lens
from .. import plot_common as pc


__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


@pytest.mark.parametrize(
    "tld_exception",
    [
        "amazonaws.com",
        "azurewebsites.net",
        "cloudapp.net",
        "cloudfront.net",
        "dyndns.org",
        "elasticbeanstalk.com",
        "fastly.net",
        "googleapis.com",
    ],
)
def test_extract_hostname_tld_exceptions(tld_exception):
    assert (
        plot_iot_data_hostname_lens.extract_hostname(f"example.{tld_exception}")
        == "example"
    )


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
def test_main(mocker, iot_data_csvs, exp_name_frag):
    savefig = mocker.patch("matplotlib.pyplot.savefig")
    mocker.patch("sys.argv", ["test"] + iot_data_csvs)

    mocker.patch(
        "pandas.read_csv",
        lambda *args, **kwargs: pandas.DataFrame(
            data={
                "msg_type": 4 * ["query"],
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

    if "ixp" == exp_name_frag:
        with pytest.raises(ValueError):
            plot_iot_data_hostname_lens.main()
    else:
        plot_iot_data_hostname_lens.main()
        filters_count = len(plot_iot_data_name_lens.FILTERS)
        if "iotfinder" in exp_name_frag:
            # qrys_only and no_mdns_qrys_only are skipped
            filters_count -= 2
        assert savefig.call_count == filters_count * len(pc.OUTPUT_FORMATS)
        for i, ext in enumerate(pc.OUTPUT_FORMATS):
            assert f"@{exp_name_frag}.{ext}" in savefig.call_args_list[i][0][0]
