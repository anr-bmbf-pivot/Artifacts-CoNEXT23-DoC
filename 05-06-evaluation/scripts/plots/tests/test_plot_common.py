# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring,missing-class-docstring
# pylint: disable=missing-function-docstring

import logging
import math

import pytest

from .. import plot_common as pc

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


def row_as_expected(exp_row, row):
    CAN_HAVE_NANS = ["transmissions", "cache_hits", "client_cache_hits"]
    assert {k: v for k, v in exp_row.items() if k not in CAN_HAVE_NANS} == {
        k: v for k, v in row.items() if k not in CAN_HAVE_NANS
    }
    assert "transmissions" in exp_row
    for can_nan in CAN_HAVE_NANS:
        assert len(row.get(can_nan, [])) == len(exp_row.get(can_nan, []))
        for trans, exp_trans in zip(row.get(can_nan, []), exp_row.get(can_nan, [])):
            if math.isnan(exp_trans):
                assert math.isnan(trans)
            else:
                assert exp_trans == trans


@pytest.mark.parametrize(
    "kwargs, exp_error, exp_res, exp_row",
    [
        (
            {"row": {"id": 1234, "query_time": 0.1234}},
            None,
            (1234, 0.1234),
            {"id": 0, "query_time": 0, "transmissions": []},
        ),
        (
            {"row": {"id": "not a duck", "query_time": 0.1234}},
            ValueError,
            None,
            None,
        ),
        (
            {"row": {"id": 1234, "query_time": "also not a duck"}},
            ValueError,
            None,
            None,
        ),
        (
            {"row": {"id": 1234, "query_time": 0.1234}, "base_id": 123},
            None,
            (123, 0.1234),
            {"id": 1111, "query_time": 0, "transmissions": []},
        ),
        (
            {"row": {"id": "not a duck", "query_time": 0.1234}, "base_id": 123},
            ValueError,
            None,
            None,
        ),
        (
            {"row": {"id": 1234, "query_time": 0.1234}, "base_id": "not a duck"},
            TypeError,
            None,
            None,
        ),
        (
            {"row": {"id": 1234, "query_time": 2}, "base_time": 1},
            None,
            (1234, 1),
            {"id": 0, "query_time": 1, "transmissions": []},
        ),
        (
            {"row": {"id": 1234, "query_time": "also not a duck"}, "base_time": 1},
            ValueError,
            None,
            None,
        ),
        (
            {"row": {"id": 1234, "query_time": 2}, "base_time": "also not a duck"},
            TypeError,
            None,
            None,
        ),
        (
            {"row": {"id": 1234, "query_time": 1234, "response_time": 3456}},
            None,
            (1234, 1234),
            {"id": 0, "query_time": 0, "response_time": 2222, "transmissions": []},
        ),
        (
            {
                "row": {"id": 1234, "query_time": 1234, "response_time": 3456},
                "base_time": 123,
            },
            None,
            (1234, 123),
            {"id": 0, "query_time": 1111, "response_time": 3333, "transmissions": []},
        ),
        (
            {
                "row": {
                    "id": 1234,
                    "query_time": 1234,
                    "response_time": "definitely not a duck",
                }
            },
            ValueError,
            None,
            None,
        ),
        (
            {
                "row": {
                    "id": 1234,
                    "query_time": 1234,
                    "response_time": 3456,
                    "transmissions": "[1235, 2345]",
                }
            },
            None,
            (1234, 1234),
            {
                "id": 0,
                "query_time": 0,
                "response_time": 2222,
                "transmissions": [1, 1111],
            },
        ),
        pytest.param(
            {
                "row": {
                    "id": 1234,
                    "query_time": 1234,
                    "response_time": 3456,
                    "transmissions": "[1235, 'foobar']",
                }
            },
            None,
            (1234, 1234),
            {
                "id": 0,
                "query_time": 0,
                "response_time": 2222,
                "transmissions": [1, float("nan")],
            },
            id="non-float transmission",
        ),
        pytest.param(
            {
                "row": {
                    "id": 1234,
                    "query_time": 1234,
                    "response_time": 3456,
                    "transmissions": "",
                }
            },
            None,
            (1234, 1234),
            {
                "id": 0,
                "query_time": 0,
                "response_time": 2222,
                "transmissions": [],
            },
            id="transmissions as empty string",
        ),
        pytest.param(
            {
                "row": {
                    "id": 1234,
                    "query_time": 1234,
                    "response_time": 3456,
                    "transmissions": "IS this (even valid??!?",
                }
            },
            "Unable to parse transmissions in row {'id': 0, 'query_time': 0.0, "
            "'response_time': 2222.0, 'transmissions': 'IS this (even valid??!?'} for"
            " query at timestamp 1234",
            (1234, 1234),
            {
                "id": 0,
                "query_time": 0,
                "response_time": 2222,
                "transmissions": [],
            },
            id="transmissions not parsable",
        ),
        pytest.param(
            {
                "row": {
                    "id": 1234,
                    "query_time": 1234,
                    "response_time": 3456,
                    "transmissions": [1235, 2345],
                }
            },
            None,
            (1234, 1234),
            {
                "id": 0,
                "query_time": 0,
                "response_time": 2222,
                "transmissions": [],
            },
            id="transmissions not as string",
        ),
        (
            {
                "row": {
                    "id": 1234,
                    "query_time": 1234,
                    "response_time": 3456,
                    "cache_hits": "[1235, 2345]",
                }
            },
            None,
            (1234, 1234),
            {
                "id": 0,
                "query_time": 0,
                "response_time": 2222,
                "cache_hits": [1, 1111],
                "transmissions": [],
            },
        ),
        pytest.param(
            {
                "row": {
                    "id": 1234,
                    "query_time": 1234,
                    "response_time": 3456,
                    "cache_hits": "[1235, 'foobar']",
                }
            },
            None,
            (1234, 1234),
            {
                "id": 0,
                "query_time": 0,
                "response_time": 2222,
                "cache_hits": [1, float("nan")],
                "transmissions": [],
            },
            id="non-float cache-hit",
        ),
        pytest.param(
            {
                "row": {
                    "id": 1234,
                    "query_time": 1234,
                    "response_time": 3456,
                    "cache_hits": "",
                }
            },
            None,
            (1234, 1234),
            {
                "id": 0,
                "query_time": 0,
                "response_time": 2222,
                "cache_hits": [],
                "transmissions": [],
            },
            id="cache_hits as empty string",
        ),
        pytest.param(
            {
                "row": {
                    "id": 1234,
                    "query_time": 1234,
                    "response_time": 3456,
                    "cache_hits": "IS this (even valid??!?",
                }
            },
            "Unable to parse cache_hits in row {'id': 0, 'query_time': 0.0, "
            "'response_time': 2222.0, 'cache_hits': 'IS this (even valid??!?', "
            "'transmissions': []} for query at timestamp 1234",
            (1234, 1234),
            {
                "id": 0,
                "query_time": 0,
                "response_time": 2222,
                "cache_hits": [],
                "transmissions": [],
            },
            id="cache_hits not parsable",
        ),
        pytest.param(
            {
                "row": {
                    "id": 1234,
                    "query_time": 1234,
                    "response_time": 3456,
                    "cache_hits": [1235, 2345],
                }
            },
            None,
            (1234, 1234),
            {
                "id": 0,
                "query_time": 0,
                "response_time": 2222,
                "cache_hits": [],
                "transmissions": [],
            },
            id="cache_hits not as string",
        ),
        (
            {
                "row": {
                    "id": 1234,
                    "query_time": 1234,
                    "unauth_time": 2345,
                }
            },
            None,
            (1234, 1234),
            {
                "id": 0,
                "query_time": 0,
                "unauth_time": 1111,
                "transmissions": [],
            },
        ),
    ],
)
def test_normalize_times_and_ids(caplog, kwargs, exp_error, exp_res, exp_row):
    row = kwargs["row"]
    if exp_error:
        if isinstance(exp_error, str):
            with caplog.at_level(logging.ERROR):
                assert pc.normalize_times_and_ids(**kwargs) == exp_res
                row_as_expected(exp_row, row)
            assert exp_error in caplog.text
        else:
            with pytest.raises(exp_error):
                pc.normalize_times_and_ids(**kwargs)
    else:
        assert pc.normalize_times_and_ids(**kwargs) == exp_res
        row_as_expected(exp_row, row)


def test_transports_readable():
    tr = pc.TRANSPORTS_READABLE
    assert str(tr["coap"]) == "CoAP"
    assert str(tr["coap"][None]) == "CoAP (FETCH)"
    assert str(tr["coap"]["fetch"]) == "CoAP (FETCH)"
    assert str(tr["coap"]["get"]) == "CoAP (GET)"
    assert str(tr["coap"]["post"]) == "CoAP (POST)"

    assert str(tr["coaps"]) == "CoAPSv1.2"
    assert str(tr["coaps"][None]) == "CoAPSv1.2 (FETCH)"
    assert str(tr["coaps"]["fetch"]) == "CoAPSv1.2 (FETCH)"
    assert str(tr["coaps"]["get"]) == "CoAPSv1.2 (GET)"
    assert str(tr["coaps"]["post"]) == "CoAPSv1.2 (POST)"

    assert str(tr["dtls"]) == "DTLSv1.2"
    assert str(tr["dtls"][None]) == "DTLSv1.2"
    assert str(tr["dtls"]["fetch"]) == "DTLSv1.2"
    assert str(tr["dtls"]["get"]) == "DTLSv1.2"
    assert str(tr["dtls"]["post"]) == "DTLSv1.2"

    assert str(tr["oscore"]) == "OSCORE"
    assert str(tr["oscore"][None]) == "OSCORE (FETCH)"
    assert str(tr["oscore"]["fetch"]) == "OSCORE (FETCH)"
    assert str(tr["oscore"]["get"]) == "OSCORE (GET)"
    assert str(tr["oscore"]["post"]) == "OSCORE (POST)"

    assert str(tr["udp"]) == "UDP"
    assert str(tr["udp"][None]) == "UDP"
    assert str(tr["udp"]["fetch"]) == "UDP"
    assert str(tr["udp"]["get"]) == "UDP"
    assert str(tr["udp"]["post"]) == "UDP"


def test_transports_style():
    tr = pc.TRANSPORTS_STYLE

    assert tr["coap"] == {"color": "C4"}
    assert tr["coap"][None] == {"color": "C4"}
    assert tr["coap"]["fetch"] == {"color": "C4", "linestyle": "-"}
    assert tr["coap"]["get"] == {"color": "C4", "linestyle": ":"}
    assert tr["coap"]["post"] == {"color": "C4", "linestyle": "--"}

    assert tr["coaps"] == {"color": "C3"}
    assert tr["coaps"][None] == {"color": "C3"}
    assert tr["coaps"]["fetch"] == {"color": "C3", "linestyle": "-"}
    assert tr["coaps"]["get"] == {"color": "C3", "linestyle": ":"}
    assert tr["coaps"]["post"] == {"color": "C3", "linestyle": "--"}

    assert tr["dtls"] == {"color": "C1"}
    assert tr["dtls"][None] == {"color": "C1"}

    assert tr["oscore"] == {"color": "C2"}
    assert tr["oscore"][None] == {"color": "C2"}
    assert tr["oscore"]["fetch"] == {"color": "C2", "linestyle": "-"}
    assert tr["oscore"]["get"] == {"color": "C2", "linestyle": ":"}
    assert tr["oscore"]["post"] == {"color": "C2", "linestyle": "--"}

    assert tr["udp"] == {"color": "C0"}
    assert tr["udp"][None] == {"color": "C0"}

    with pytest.raises(KeyError):
        tr["udp"]["test"]
