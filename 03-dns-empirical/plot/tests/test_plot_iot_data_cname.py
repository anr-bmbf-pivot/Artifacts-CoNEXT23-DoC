#! /usr/bin/env python
#
# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

import networkx
import pandas
import pytest

from .. import plot_iot_data_cname
from .. import plot_common as pc

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


def test_pseudonize_assertion_error():
    cnames = networkx.DiGraph()
    cnames.add_edge("12:34:56:78:90:ab.local.", "blafoo", label="TXT")
    cnames.nodes["12:34:56:78:90:ab.local."]["type"] = "name"
    cnames.nodes["blafoo"]["type"] = "txt"
    with pytest.raises(AssertionError):
        plot_iot_data_cname.pseudonize(cnames)


@pytest.mark.parametrize(
    "iot_data_csvs, exp_name_frag",
    [
        (["IoTFinder"], "iotfinder"),
        (["MonIoTr"], "moniotr"),
        (["YourThings"], "yourthings"),
        (["10.1109-EuroSP48549.2020.00037", "MonIoTr"], "iotfinder+moniotr"),
        (["10.1109-SP.2019.00013", "iotfinder"], "iotfinder+yourthings"),
        (
            ["10.1145-3355369.3355577", "iotfinder", "yourthings"],
            "iotfinder+moniotr+yourthings",
        ),
    ],
)
def test_main(mocker, iot_data_csvs, exp_name_frag):
    write_dot = mocker.patch("plot.plot_iot_data_cname.networkx_write_dot")
    savefig = mocker.patch("matplotlib.pyplot.savefig")
    # libertine font in ACM style causes problems when running in tox/pytest
    mocker.patch("sys.argv", ["test", "-s", "mlenders_usenix.mplstyle"] + iot_data_csvs)
    mocker.patch(
        "pandas.read_csv",
        lambda *args, **kwargs: pandas.DataFrame(
            data={
                "msg_type": 4 * ["response"],
                "name": [
                    "example.com",
                    "example.org",
                    "www.example.org",
                    "www.example.com",
                ],
                "rdata": [
                    "b'Hello world'",
                    "b'www.example.org'",
                    "192.168.1.1",
                    "2001:db8::1",
                ],
                "section": 4 * ["an"],
                "transport": ["Do53", "Do53", "MDNS", "Do53"],
                "type": ["TXT", "CNAME", "A", "AAAA"],
            }
        ),
    )
    plot_iot_data_cname.main()
    write_dot.assert_called_once()
    assert isinstance(write_dot.call_args[0][0], networkx.DiGraph)
    assert f"@{exp_name_frag}.dot" in write_dot.call_args[0][1]
    assert savefig.call_count == len(pc.OUTPUT_FORMATS)
    for i, ext in enumerate(pc.OUTPUT_FORMATS):
        assert f"@{exp_name_frag}.{ext}" in savefig.call_args_list[i][0][0]
