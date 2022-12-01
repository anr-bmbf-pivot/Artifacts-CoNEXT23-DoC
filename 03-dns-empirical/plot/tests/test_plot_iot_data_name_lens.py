#! /usr/bin/env python
#
# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

import pandas
import pytest

from .. import plot_iot_data_name_lens
from .. import plot_common as pc

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


@pytest.mark.parametrize(
    "filt, exp_df",
    [
        (
            "all",
            pandas.DataFrame(
                data={
                    "msg_type": ["query", "response", "response", "response", "query"],
                    "transport": ["MDNS"] + (4 * ["Do53"]),
                    "section": ["qd", "qd", "an", "ar", "qd"],
                },
                index=[0, 1, 2, 4, 5],
            ),
        ),
        (
            "qrys_only",
            pandas.DataFrame(
                data={
                    "msg_type": ["query", "query"],
                    "transport": ["MDNS", "Do53"],
                    "section": ["qd", "qd"],
                },
                index=[0, 5],
            ),
        ),
        (
            "qd_only",
            pandas.DataFrame(
                data={
                    "msg_type": ["query", "response", "query"],
                    "transport": ["MDNS", "Do53", "Do53"],
                    "section": ["qd", "qd", "qd"],
                },
                index=[0, 1, 5],
            ),
        ),
        (
            "qd_an_only",
            pandas.DataFrame(
                data={
                    "msg_type": ["query", "response", "response", "query"],
                    "transport": ["MDNS"] + (3 * ["Do53"]),
                    "section": ["qd", "qd", "an", "qd"],
                },
                index=[0, 1, 2, 5],
            ),
        ),
        (
            "no_mdns",
            pandas.DataFrame(
                data={
                    "msg_type": ["response", "response", "response", "query"],
                    "transport": 4 * ["Do53"],
                    "section": ["qd", "an", "ar", "qd"],
                },
                index=[1, 2, 4, 5],
            ),
        ),
        (
            "no_mdns_qrys_only",
            pandas.DataFrame(
                data={
                    "msg_type": ["query"],
                    "transport": ["Do53"],
                    "section": ["qd"],
                },
                index=[5],
            ),
        ),
        (
            "no_mdns_qd_only",
            pandas.DataFrame(
                data={
                    "msg_type": ["response", "query"],
                    "transport": 2 * ["Do53"],
                    "section": 2 * ["qd"],
                },
                index=[1, 5],
            ),
        ),
        (
            "no_mdns_qd_an_only",
            pandas.DataFrame(
                data={
                    "msg_type": ["response", "response", "query"],
                    "transport": 3 * ["Do53"],
                    "section": ["qd", "an", "qd"],
                },
                index=[1, 2, 5],
            ),
        ),
    ],
)
def test_filter_data_frame(filt, exp_df):
    df = pandas.DataFrame(
        data={
            "msg_type": ["query", "response", "response", "query", "response", "query"],
            "transport": ["MDNS", "Do53", "Do53", "DoTCP", "Do53", "Do53"],
            "section": ["qd", "qd", "an", "qd", "ar", "qd"],
        },
    )
    filt_func = dict(plot_iot_data_name_lens.FILTERS)[filt]
    assert plot_iot_data_name_lens.filter_data_frame(df, filt_func).equals(exp_df)


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
def test_main_no_stats_csv(mocker, iot_data_csvs, exp_name_frag):
    savefig = mocker.patch("matplotlib.pyplot.savefig")
    to_csv = mocker.patch("pandas.DataFrame.to_csv")
    # libertine font in ACM style causes problems when running in tox/pytest
    mocker.patch("sys.argv", ["test", "-s", "mlenders_usenix.mplstyle"] + iot_data_csvs)

    def read_csv_mock(file, *args, **kwargs):
        if "iot-data-name-lens-stats.csv" in file:
            raise FileNotFoundError()
        else:
            return pandas.DataFrame(
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
            )

    mocker.patch("pandas.read_csv", read_csv_mock)
    plot_iot_data_name_lens.main()
    if "ixp" == exp_name_frag:
        # only filters used are qrys_only and qd_only
        filters_count = 2
    else:
        filters_count = len(plot_iot_data_name_lens.FILTERS)
        if "iotfinder" in exp_name_frag:
            # qrys_only and no_mdns_qrys_only are skipped
            filters_count -= 2
    assert to_csv.call_count == filters_count
    assert savefig.call_count == filters_count * len(pc.OUTPUT_FORMATS)
    for i, ext in enumerate(pc.OUTPUT_FORMATS):
        assert f"@{exp_name_frag}.{ext}" in savefig.call_args_list[i][0][0]


def test_main_with_stats_csv(mocker):
    iot_data_csvs = ["IoTFinder"]
    exp_name_frag = "iotfinder"
    savefig = mocker.patch("matplotlib.pyplot.savefig")
    to_csv = mocker.patch("pandas.DataFrame.to_csv")
    mocker.patch("sys.argv", ["test", "-s", "mlenders_usenix.mplstyle"] + iot_data_csvs)

    def read_csv_mock(file, *args, **kwargs):
        if "iot-data-name-lens-stats.csv" in file:
            raise FileNotFoundError()
        else:
            return pandas.DataFrame(
                data={
                    "msg_type": 4 * ["query"],
                    "name_len": [7, 8, 9, 10],
                    "rdata": 4 * [None],
                    "section": 4 * ["qd"],
                    "transport": ["Do53", "Do53", "MDNS", "Do53"],
                    "type": 4 * ["A"],
                }
            )

    mocker.patch("pandas.read_csv", read_csv_mock)
    plot_iot_data_name_lens.main()
    # qrys_only and no_mdns_qrys_only are skipped
    filters_count = len(plot_iot_data_name_lens.FILTERS) - 2
    assert to_csv.call_count == filters_count
    assert savefig.call_count == filters_count * len(pc.OUTPUT_FORMATS)
    for i, ext in enumerate(pc.OUTPUT_FORMATS):
        assert f"@{exp_name_frag}.{ext}" in savefig.call_args_list[i][0][0]


def test_main_name_len_instead_of_name(mocker):
    iot_data_csvs = ["IoTFinder"]
    exp_name_frag = "iotfinder"
    savefig = mocker.patch("matplotlib.pyplot.savefig")
    to_csv = mocker.patch("pandas.DataFrame.to_csv")
    mocker.patch("sys.argv", ["test", "-s", "mlenders_usenix.mplstyle"] + iot_data_csvs)

    def read_csv_mock(file, *args, **kwargs):
        if "iot-data-name-lens-stats.csv" in file:
            return pandas.DataFrame(
                data={
                    "data_src": ["iotfinder"],
                    "filter": ["all"],
                    "min": [0.0],
                    "max": [82.0],
                    "μ": [29.21793349168646],
                    "σ": [11.161511258610323],
                    "mode": [24.0],
                    "Q1": [22.0],
                    "Q2": [26.0],
                    "Q3": [38.0],
                },
            ).set_index(["data_src", "filter"])
        else:
            return pandas.DataFrame(
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
            )

    mocker.patch("pandas.read_csv", read_csv_mock)
    plot_iot_data_name_lens.main()
    # qrys_only and no_mdns_qrys_only are skipped
    filters_count = len(plot_iot_data_name_lens.FILTERS) - 2
    assert to_csv.call_count == filters_count
    assert savefig.call_count == filters_count * len(pc.OUTPUT_FORMATS)
    for i, ext in enumerate(pc.OUTPUT_FORMATS):
        assert f"@{exp_name_frag}.{ext}" in savefig.call_args_list[i][0][0]
