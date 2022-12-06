# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import queue
import subprocess
import sys

import pytest

from .. import plot_common as pc
from .. import parse_max_age_link_util

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021-22 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


@pytest.fixture
def isolate_globals():
    csv_name_pattern_fmt = pc.CSV_NAME_PATTERN_FMT
    csv_ext_filter = pc.CSV_EXT_FILTER
    yield
    pc.CSV_NAME_PATTERN_FMT = csv_name_pattern_fmt
    pc.CSV_EXT_FILTER = csv_ext_filter


def test_edge_arg():
    assert parse_max_age_link_util.edge_arg("209,205") == (209, 205)
    assert parse_max_age_link_util.edge_arg("205, 290") == (205, 290)
    with pytest.raises(ValueError):
        assert parse_max_age_link_util.edge_arg("209,test")


def test_read_pcap(mocker):
    popen = mocker.patch("subprocess.Popen")
    popen.return_value.stdout = (
        "8932\t66:4e:6f:87:a1:fa:2f:3e\t5e:8f:89:df:81:3d:33:b3\t\t124\tCoAP\tCON\n",
        "8933\t66:4e:6f:87:a1:fa:2f:3e\t5e:8f:89:df:81:3d:33:b3\t0x0001\t12\t6LoWPAN\t"
        "Data\n",
    )
    popen.return_value.returncode = 0
    res = parse_max_age_link_util.read_pcap("the_pcap", "queries", "the_filter")
    assert res["queries_packets"] == 2
    assert res["queries_bytes"] == 136
    assert res["queries_frags"] == 1
    popen.assert_called_once_with(
        ["tshark", "-Tfields"]
        + parse_max_age_link_util.TSHARK_FIELDS
        + ["-Y", "the_filter", "-r", "the_pcap"],
        stdout=subprocess.PIPE,
        bufsize=1,
        universal_newlines=True,
    )


def test_read_pcap_tshark_error(mocker):
    popen = mocker.patch("subprocess.Popen")
    popen.return_value.stdout = ""
    popen.return_value.returncode = 1
    with pytest.raises(subprocess.CalledProcessError):
        parse_max_age_link_util.read_pcap("the_pcap", "queries", "the_filter")
    popen.assert_called_once_with(
        ["tshark", "-Tfields"]
        + parse_max_age_link_util.TSHARK_FIELDS
        + ["-Y", "the_filter", "-r", "the_pcap"],
        stdout=subprocess.PIPE,
        bufsize=1,
        universal_newlines=True,
    )


def test_get_link(mocker):
    sync_queue = queue.Queue()
    popen = mocker.patch("subprocess.Popen")
    popen.return_value.stdout = (
        "8932\t66:4e:6f:87:a1:fa:2f:3e\t5e:8f:89:df:81:3d:33:b3\t\t124\tCoAP\tCON\n",
        "8933\t66:4e:6f:87:a1:fa:2f:3e\t5e:8f:89:df:81:3d:33:b3\t0x0001\t12\t6LoWPAN\t"
        "Data\n",
    )
    popen.return_value.returncode = 0
    nodes = {
        202: "00:11:22:33:44:55:66:77",
        205: "00:11:22:33:44:55:66:78",
        209: "00:11:22:33:44:55:66:76",
        290: "00:11:22:33:44:55:66:79",
    }
    parse_max_age_link_util.get_link(
        nodes,
        {"timestamp": 1670318606},
        "the_pcap",
        (209, 205),
        {
            "max_age_config": "eol-ttls",
            "method": "fetch",
            "dns_cache": 0,
            "client_coap_cache": 1,
            "proxied": 1,
        },
        1,
        sync_queue,
    )
    res = sync_queue.get()
    assert res["queries_packets"] == 2
    assert res["queries_bytes"] == 136
    assert res["queries_frags"] == 1
    assert res["responses_packets"] == 2
    assert res["responses_bytes"] == 136
    assert res["responses_frags"] == 1
    exp_popen_calls = [
        mocker.call(
            ["tshark", "-Tfields"]
            + parse_max_age_link_util.TSHARK_FIELDS
            + [
                "-Y",
                f"zep.device_id == {0x3000 | 205} && "
                "(!icmpv6) && (wpan.frame_type == 0x1) "
                f"&& (wpan.src64 == {nodes[209]}) && (wpan.dst64 == {nodes[205]})",
                "-r",
                "the_pcap",
            ],
            stdout=subprocess.PIPE,
            bufsize=1,
            universal_newlines=True,
        ),
        mocker.call(
            ["tshark", "-Tfields"]
            + parse_max_age_link_util.TSHARK_FIELDS
            + [
                "-Y",
                f"zep.device_id == {0x3000 | 205} && "
                "(!icmpv6) && (wpan.frame_type == 0x1) "
                f"&& (wpan.src64 == {nodes[205]}) && (wpan.dst64 == {nodes[209]})",
                "-r",
                "the_pcap",
            ],
            stdout=subprocess.PIPE,
            bufsize=1,
            universal_newlines=True,
        ),
    ]
    popen.assert_has_calls(exp_popen_calls, any_order=True)


def test_parse_max_age_link_util(isolate_globals, monkeypatch, mocker):
    # pylint: disable=redefined-outer-name,unused-argument
    monkeypatch.setattr(sys, "argv", ["cmd", "209", "209,205", "205,202", "205,290"])
    file_op = mocker.patch.object(
        parse_max_age_link_util,
        "open",
        mocker.mock_open(
            read_data="""
Long HWaddr: 00:11:22:33:44:55:66:76
;m3-202;Long HWaddr: 00:11:22:33:44:55:66:77
;m3-205;Long HWaddr: 00:11:22:33:44:55:66:78
;m3-290;Long HWaddr: 00:11:22:33:44:55:66:79
"""
        ),
    )
    timestamp = [1648850339, 1649070431]
    mocker.patch(
        "os.listdir",
        return_value=[
            "foobar.log",
            "doc-eval-max_age-ieee802154-min-coap-fetch-dc0-ccc0-proxied0-None-"
            f"None-50x5.0-AAAA-308576-{timestamp[0]}.pcap.gz",
            "doc-eval-max_age-ieee802154-subtract-coap-fetch-dc1-ccc1-proxied1-None-"
            f"None-50x5.0-AAAA-308768-{timestamp[1]}.pcap.gz",
        ],
    )
    mocker.patch("multiprocessing.cpu_count", return_value=1)
    popen = mocker.patch("subprocess.Popen")
    popen.return_value.stdout = (
        "8932\t66:4e:6f:87:a1:fa:2f:3e\t5e:8f:89:df:81:3d:33:b3\t\t124\tCoAP\tCON\n",
        "8933\t66:4e:6f:87:a1:fa:2f:3e\t5e:8f:89:df:81:3d:33:b3\t0x0001\t12\t6LoWPAN\t"
        "Data\n",
    )
    popen.return_value.returncode = 0
    parse_max_age_link_util.main()
    exp_write_calls = [
        mocker.call(f"{timestamp[0]},min,fetch,0,0,0,205,1,136,2,1,136,2,1\r\n"),
        mocker.call(f"{timestamp[0]},min,fetch,0,0,0,202,2,136,2,1,136,2,1\r\n"),
        mocker.call(f"{timestamp[0]},min,fetch,0,0,0,290,2,136,2,1,136,2,1\r\n"),
        mocker.call(f"{timestamp[1]},subtract,fetch,1,1,1,205,1,136,2,1,136,2,1\r\n"),
        mocker.call(f"{timestamp[1]},subtract,fetch,1,1,1,202,2,136,2,1,136,2,1\r\n"),
        mocker.call(f"{timestamp[1]},subtract,fetch,1,1,1,290,2,136,2,1,136,2,1\r\n"),
    ]
    file_op().write.assert_has_calls(exp_write_calls)


def test_parse_max_age_link_util__sink_not_in_edges(isolate_globals, monkeypatch):
    # pylint: disable=redefined-outer-name,unused-argument
    monkeypatch.setattr(sys, "argv", ["cmd", "210", "209,205", "205,202", "205,290"])
    with pytest.raises(ValueError):
        parse_max_age_link_util.main()


@pytest.mark.parametrize(
    "log_data",
    [
        pytest.param("", id="empty log"),
        pytest.param(
            """
Long HWaddr: 00:11:22:33:44:55:66:76
;m3-202;Long HWaddr: 00:11:22:33:44:55:66:77
;m3-205;Long HWaddr: 00:11:22:33:44:55:66:78
;m3-290;Long HWaddr: 00:11:22:33:44:55:66:79
;m3-289;Long HWaddr: 00:11:22:33:44:55:66:80
""",
            id="superfluous nodes in log",
        ),
    ],
)
def test_parse_max_age_link_util__log_errors(
    isolate_globals, monkeypatch, mocker, log_data
):
    # pylint: disable=redefined-outer-name,unused-argument
    monkeypatch.setattr(sys, "argv", ["cmd", "209", "209,205", "205,202", "205,290"])
    timestamp = [1648850339, 1649070431]
    mocker.patch(
        "os.listdir",
        return_value=[
            "foobar.log",
            "doc-eval-max_age-ieee802154-min-coap-fetch-dc0-ccc0-proxied0-None-"
            f"None-50x5.0-AAAA-308576-{timestamp[0]}.pcap.gz",
            "doc-eval-max_age-ieee802154-subtract-coap-fetch-dc1-ccc1-proxied1-None-"
            f"None-50x5.0-AAAA-308768-{timestamp[1]}.pcap.gz",
        ],
    )
    mocker.patch.object(
        parse_max_age_link_util, "open", mocker.mock_open(read_data=log_data)
    )
    with pytest.raises(ValueError):
        parse_max_age_link_util.main()
