# Copyright (C) 2021-22 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

from .. import parse_load_results

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021-22 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


def test_parse_load_results(mocker):
    mocker.patch.object(
        parse_load_results,
        "open",
        mocker.mock_open(
            read_data="""
Starting run doc-eval-load-dtls-1.0-25-100x5.0-284361-1635776340
1635776367.615709;m3-281;query_bulk exec h.de inet6
1635776367.817829;m3-281;q;48257.h.de
1635776367.818065;m3-281;t;48257
1635776367.896382;m3-281;r;48257.h.de
1635776368.011819;m3-281;q;48258.h.de
1645851637.899136;m3-281;b;48258
1645851637.899244;m3-281;t;48258
1645851637.930830;m3-281;c2;48258
1645851637.931080;m3-281;b2;40004
1645851637.931198;m3-281;t;40004
1635776368.082952;m3-281;r;48258.h.de
1635776368.201337;m3-281;q;48259.h.de
1635776368.203072;m3-281;t;48259
1635776368.273088;m3-281;r;48259.h.de
1635776387.532727;m3-281;q;48356.h.de
1635776387.532948;m3-281;t;48356
1635776387.601553;m3-281;> r;48356.h.de
1637840810.202737;m3-281;  RX packets 266  bytes 22585,
""".encode()
        ),
    )
    mocker.patch(
        "os.listdir",
        return_value=[
            "foobar.log",
            "doc-eval-load-coap-1.0-25-100x5.0-284361-1635777176.log",
            "doc-eval-load-coaps-None-None-100x10.0-A-284623-1636045983.log",
            "doc-eval-load-dtls-1.0-25-100x5.0-284361-1635776340.log",
        ],
    )
    mocker.patch("multiprocessing.cpu_count", return_value=1)
    mocker.patch("sys.argv", ["cmd"])
    parse_load_results.main()
