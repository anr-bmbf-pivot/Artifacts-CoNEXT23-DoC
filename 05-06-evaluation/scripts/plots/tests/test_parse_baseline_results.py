# Copyright (C) 2021-22 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import os.path

import pytest

from .. import parse_baseline_results

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021-22 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


@pytest.mark.flaky(reruns=3)
@pytest.mark.parametrize(
    "read_data, exp_assert_fail",
    [
        pytest.param(
            """
Starting run doc-eval-baseline-dtls-1.0-25-100x5.0-284361-1635776340
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
""",
            False,
            id="success",
        ),
        pytest.param(
            """
Starting run doc-eval-baseline-dtls-1.0-25-100x5.0-284361-1635776340
1635776367.615709;m3-281;query_bulk exec h.de inet6
""",
            False,
            id="empty CSV",
        ),
        pytest.param(
            """
Starting run doc-eval-baseline-dtls-1.0-25-100x5.0-284361-1635776340
1635776367.615709;m3-281;query_bulk exec h.de inet6
1635776367.817829;m3-281;q;48257.h.de
1635776367.818065;m3-281;t;48257
1635776367.818065;m3-281;t;48258
""",
            True,
            id="stray transmission",
        ),
        pytest.param(
            """
Starting run doc-eval-baseline-dtls-1.0-25-100x5.0-284361-1635776340
1635776367.615709;m3-281;query_bulk exec h.de inet6
1635776367.817829;m3-281;q;48257.h.de
1635776367.818065;m3-281;t;48257
1645851637.899136;m3-281;b;48258
""",
            True,
            id="stray block",
        ),
        pytest.param(
            """
Starting run doc-eval-baseline-dtls-1.0-25-100x5.0-284361-1635776340
1635776367.615709;m3-281;query_bulk exec h.de inet6
1635776367.817829;m3-281;q;48257.h.de
1635776367.818065;m3-281;t;48257
1645851637.899136;m3-281;b;48257
1645851637.899136;m3-281;b;48257
""",
            False,
            id="duplicate block",
        ),
        pytest.param(
            """
Starting run doc-eval-baseline-oscore-fetch-None-None-50x5.0-AAAA-297517-1645841251
1645841327.121886;m3-290;query_bulk exec id.exp.example.org inet6 fetch
1645841327.314033;m3-290;q;62005
1645841327.329911;m3-290;t;48793
1645841327.409853;m3-290;u;48793
1645841327.329911;m3-290;t;48794
1645841327.409853;m3-290;r;62005
""",
            False,
            id="unauthorized exchange",
        ),
        pytest.param(
            """
Starting run doc-eval-baseline-oscore-fetch-None-None-50x5.0-AAAA-297517-1645841251
1645841327.121886;m3-290;query_bulk exec id.exp.example.org inet6 fetch
1645841327.314033;m3-290;q;62005
1645841327.329911;m3-290;t;48793
1645841327.409853;m3-290;u;48794
1645841327.409853;m3-290;u;48794
""",
            True,
            id="stray unauthorized",
        ),
        pytest.param(
            """
Starting run doc-eval-baseline-oscore-fetch-None-None-50x5.0-AAAA-297517-1645841251
1645841327.121886;m3-290;query_bulk exec id.exp.example.org inet6 fetch
1645841327.314033;m3-290;q;62005
1645841327.409853;m3-290;A;62005
""",
            False,
            id="legal but for other experiment types",
        ),
        pytest.param(
            """
Starting run doc-eval-baseline-oscore-fetch-None-None-50x5.0-AAAA-297517-1645841251
1645841327.121886;m3-290;query_bulk exec id.exp.example.org inet6 fetch
1645841327.409853;m3-290;Nope;62005
""",
            False,
            id="illegal message type",
        ),
    ],
)
def test_parse_baseline_results(mocker, read_data, exp_assert_fail):
    mocker.patch.object(
        parse_baseline_results,
        "open",
        mocker.mock_open(read_data=read_data.encode()),
    )
    mocker.patch(
        "os.listdir",
        return_value=[
            "foobar.log",
            "doc-eval-baseline-coap-1.0-25-100x5.0-284361-1635777176.log",
            "doc-eval-baseline-coaps-None-None-100x10.0-A-284623-1636045983.log",
            "doc-eval-baseline-dtls-1.0-25-100x5.0-284361-1635776340.log",
        ],
    )
    mocker.patch("multiprocessing.cpu_count", return_value=1)
    mocker.patch("sys.argv", ["cmd"])
    mocker.patch("os.path.exists", return_value=False)
    if exp_assert_fail:
        with pytest.raises(AssertionError):
            parse_baseline_results.main()
    else:
        parse_baseline_results.main()


@pytest.mark.flaky(reruns=3)
def test_parse_baseline_results__delete_after(mocker):
    mocker.patch.object(
        parse_baseline_results,
        "open",
        mocker.mock_open(
            read_data="""
Starting run doc-eval-baseline-oscore-fetch-None-None-50x5.0-AAAA-297517-1645841251
1645841327.121886;m3-290;query_bulk exec id.exp.example.org inet6 fetch
1645841327.314033;m3-290;q;62005
1645841327.329911;m3-290;t;48793
1645841327.409853;m3-290;u;48794
""".encode()
        ),
    )
    mocker.patch(
        "os.listdir",
        return_value=[
            "foobar.log",
            "doc-eval-baseline-coap-1.0-25-100x5.0-284361-1635777176.log",
            "doc-eval-baseline-coaps-None-None-100x10.0-A-284623-1636045983.log",
            "doc-eval-baseline-dtls-1.0-25-100x5.0-284361-1635776340.log",
        ],
    )
    mocker.patch("multiprocessing.cpu_count", return_value=1)
    mocker.patch("sys.argv", ["cmd"])
    mocker.patch("os.path.exists", return_value=True)
    remove = mocker.patch("os.remove")
    with pytest.raises(AssertionError):
        parse_baseline_results.main()
    # check for successful cleanup
    assert (
        mocker.call(
            os.path.join(
                parse_baseline_results.pc.DATA_PATH,
                "doc-eval-baseline-coap-1.0-25-100x5.0-284361-1635777176.times.csv",
            )
        )
        in remove.mock_calls
    )
    assert (
        mocker.call(
            os.path.join(
                parse_baseline_results.pc.DATA_PATH,
                "doc-eval-baseline-coap-1.0-25-100x5.0-284361-1635777176.stats.csv",
            )
        )
        in remove.mock_calls
    )
