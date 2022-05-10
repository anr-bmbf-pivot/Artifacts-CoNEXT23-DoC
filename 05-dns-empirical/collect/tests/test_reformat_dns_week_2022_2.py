# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

import gzip
import os

import pytest

from .. import reformat_dns_week_2022_2


__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


@pytest.mark.parametrize(
    "typ, exp",
    [
        (1, "A"),
        (2, "NS"),
        (3, "MD"),
        (5, "CNAME"),
        (255, "ALL"),
        (65280, 65280),
        (65535, "RESERVED"),
    ],
)
def test_to_dnstype_str(typ, exp):
    assert reformat_dns_week_2022_2.to_dnstype_str(typ) == exp


@pytest.mark.parametrize(
    "field, value, exp",
    [
        ("udp.length", 20, ("msg_len", 12)),
        ("dns.flags.response", 1, ("msg_type", "response")),
        ("dns.flags.response", 0, ("msg_type", "query")),
        ("dns.count.queries", "foobar", ("qdcount", "foobar")),
        ("dns.count.answers", "foobar", ("ancount", "foobar")),
        ("dns.count.auth_rr", "foobar", ("nscount", "foobar")),
        ("dns.count.add_rr", "foobar", ("arcount", "foobar")),
        ("dns.qry.class", "", ("class", None)),
        ("dns.qry.class", "0x1", ("class", "IN")),
        ("dns.qry.class", "0x3", ("class", "CH")),
        ("dns.qry.type", "", ("type", None)),
        ("dns.qry.type", "1", ("type", "A")),
        ("dns.qry.name.len", 42, ("name_len", 42)),
    ],
)
def test_map_field(field, value, exp):
    assert reformat_dns_week_2022_2.map_field(field, value) == exp


EXP_OUT_CSV_LINES = (
    "tarball,pcap_name,frame_no,device,transport,tid,msg_type,msg_len,qdcount,ancount,"
    "nscount,arcount,section,name_len,type,class,ttl,rdata_len\r\n",
    ",tests/test-fixtures/test.csv.gz,2,,,2,query,51,1,0,0,0,qd,34,A,IN,,\r\n",
    ",tests/test-fixtures/test.csv.gz,4,,,4,response,1048,1,0,6,1,qd,31,A,IN,,\r\n",
    ",tests/test-fixtures/test.csv.gz,6,,,6,response,1027,1,0,6,1,qd,10,A,IN,,\r\n",
    ",tests/test-fixtures/test.csv.gz,6,,,6,response,1027,1,0,6,1,ns,,NSEC,IN,,15\r\n",
    ",tests/test-fixtures/test.csv.gz,7,,,7,response,836,1,0,10,16,qd,16,AAAA,IN,,\r\n",
    ",tests/test-fixtures/test.csv.gz,7,,,7,response,836,1,0,10,16,ns,,NS,IN,,8\r\n",
    ",tests/test-fixtures/test.csv.gz,7,,,7,response,836,1,0,10,16,ns,,NS,IN,,4\r\n",
    ",tests/test-fixtures/test.csv.gz,7,,,7,response,836,1,0,10,16,ns,,NS,IN,,4\r\n",
    ",tests/test-fixtures/test.csv.gz,12,,,12,query,51,2,0,0,0,qd,34,A,IN,,\r\n",
    ",tests/test-fixtures/test.csv.gz,12,,,12,query,51,2,0,0,0,qd,46,AAAA,IN,,\r\n",
    ",tests/test-fixtures/test.csv.gz,13,,,13,query,51,2,0,0,0,qd,34,,,,\r\n",
    ",tests/test-fixtures/test.csv.gz,13,,,13,query,51,2,0,0,0,qd,46,AAAA,IN,,\r\n",
    ",tests/test-fixtures/test.csv.gz,14,,,14,response,51,2,2,0,0,qd,34,A,IN,,\r\n",
    ",tests/test-fixtures/test.csv.gz,14,,,14,response,51,2,2,0,0,qd,46,AAAA,IN,,\r\n",
    ",tests/test-fixtures/test.csv.gz,14,,,14,response,51,2,2,0,0,an,,A,IN,,34\r\n",
    ",tests/test-fixtures/test.csv.gz,14,,,14,response,51,2,2,0,0,an,,AAAA,IN,,46\r\n",
    ",tests/test-fixtures/test.csv.gz,15,,,15,response,51,2,1,1,0,qd,34,A,IN,,\r\n",
    ",tests/test-fixtures/test.csv.gz,15,,,15,response,51,2,1,1,0,qd,46,AAAA,IN,,\r\n",
    ",tests/test-fixtures/test.csv.gz,15,,,15,response,51,2,1,1,0,an,,A,IN,,34\r\n",
    ",tests/test-fixtures/test.csv.gz,15,,,15,response,51,2,1,1,0,ns,,AAAA,IN,,46\r\n",
    ",tests/test-fixtures/test.csv.gz,16,,,16,response,51,2,1,0,1,qd,34,A,IN,,\r\n",
    ",tests/test-fixtures/test.csv.gz,16,,,16,response,51,2,1,0,1,qd,46,AAAA,IN,,\r\n",
    ",tests/test-fixtures/test.csv.gz,16,,,16,response,51,2,1,0,1,an,,A,IN,,34\r\n",
    ",tests/test-fixtures/test.csv.gz,16,,,16,response,51,2,1,0,1,ar,,AAAA,IN,,46\r\n",
    ",tests/test-fixtures/test.csv.gz,17,,,17,response,51,2,2,0,0,qd,34,A,IN,,\r\n",
    ",tests/test-fixtures/test.csv.gz,17,,,17,response,51,2,2,0,0,qd,46,AAAA,IN,,\r\n",
    ",tests/test-fixtures/test.csv.gz,17,,,17,response,51,2,2,0,0,an,,A,IN,,34\r\n",
    ",tests/test-fixtures/test.csv.gz,17,,,17,response,51,2,2,0,0,an,,,,,46\r\n",
)


def test_reformat_dns_scan(monkeypatch, mocker):
    gzip_open_count = 0
    out = mocker.mock_open()
    gzip_open_orig = gzip.open

    def gzip_open_mock(*args, **kwargs):
        nonlocal gzip_open_count
        gzip_open_count += 1
        if gzip_open_count == 1:
            return gzip_open_orig(*args, **kwargs)
        else:
            return out(*args, **kwargs)

    monkeypatch.setattr(gzip, "open", gzip_open_mock)

    script_path = os.path.dirname(os.path.realpath(__file__))
    csvfile = os.path.join(script_path, "test-fixtures", "test.csv.gz")
    reformat_dns_week_2022_2.reformat_dns_scan(csvfile)
    handle = out()
    assert handle.write.call_args_list == [((line,),) for line in EXP_OUT_CSV_LINES]


def test_reformat_dns_scan__too_many_response_records(monkeypatch, mocker):
    gzip_open_count = 0
    out_open = mocker.mock_open()
    in_open = mocker.mock_open(
        read_data="|".join(reformat_dns_week_2022_2.SHARK_FIELDS)
        + "\n2022-05-12 14:54:20.000000|4|844|0|1|0|0|1|0|0|0|0x0001|28|16|"
        "0x0001,0x0001,0x0001|2,2,2|8,4,4"
    )

    def gzip_open_mock(*args, **kwargs):
        nonlocal gzip_open_count
        gzip_open_count += 1
        if gzip_open_count == 1:
            return in_open(*args, **kwargs)
        else:
            return out_open(*args, **kwargs)

    monkeypatch.setattr(gzip, "open", gzip_open_mock)

    script_path = os.path.dirname(os.path.realpath(__file__))
    csvfile = os.path.join(script_path, "test-fixtures", "test.csv.gz")
    with pytest.raises(AssertionError):
        reformat_dns_week_2022_2.reformat_dns_scan(csvfile)


def test_main(mocker):
    mocker.patch("sys.argv", ["cmd", "testfile"])
    reformat_dns_scan = mocker.patch(
        "collect.reformat_dns_week_2022_2.reformat_dns_scan"
    )
    reformat_dns_week_2022_2.main()
    reformat_dns_scan.assert_called_once_with("testfile")
