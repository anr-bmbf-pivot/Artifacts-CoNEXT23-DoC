# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

import io
import logging
import os
import shutil
import time

import pytest
from scapy.all import Ether, IP, IPv6, ICMP, UDP, DNS, raw
from scapy.all import DNSQR, DNSRR, DNSRRNSEC
from scapy.all import PcapWriter

from .. import scan_iot_data


__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


@pytest.mark.parametrize(
    "pkt, exp",
    [
        (Ether() / IPv6() / UDP(sport=53, dport=51703) / DNS(), ("Do53", 12)),
        (Ether() / IPv6() / UDP(sport=30056, dport=53) / DNS(), ("Do53", 12)),
        (Ether() / IPv6() / UDP(sport=53, dport=53) / DNS(), ("Do53", 12)),
        (Ether() / IPv6() / UDP(sport=5353, dport=50285) / DNS(), ("MDNS", 12)),
        (Ether() / IPv6() / UDP(sport=36888, dport=5353) / DNS(), ("MDNS", 12)),
        (Ether() / IPv6() / UDP(sport=5353, dport=5353) / DNS(), ("MDNS", 12)),
        (
            bytes.fromhex(
                "abcdef012345678901abcdef080045000053049e400040065a8cc0007219c0002907a1"
                "550035c51465c63cfcbfe4801801fadbc000000101080ae6dfed4b4d11b19e001ded35"
                "01000001000000000000076578616d706c65036f726700001c0001"
            ),
            ("DoTCP", 29),
        ),
        (
            bytes.fromhex(
                "abcdef012345678901abcdef080045000053049e400040065a8cc0007219c000290700"
                "35051dc51465c63cfcbfe4801801fadbc000000101080ae6dfed4b4d11b19e001ded35"
                "01000001000000000000076578616d706c65036f726700001c0001"
            ),
            ("DoTCP", 29),
        ),
        (
            bytes.fromhex(
                "abcdef012345678901abcdef080045000053049e400040065a8cc0007219c000290700"
                "350035c51465c63cfcbfe4801801fadbc000000101080ae6dfed4b4d11b19e001ded35"
                "01000001000000000000076578616d706c65036f726700001c0001"
            ),
            ("DoTCP", 29),
        ),
        (Ether() / IPv6() / UDP(sport=5353, dport=5353) / DNS(), ("MDNS", 12)),
    ],
)
def test_get_transport(pkt, exp):
    pkt = Ether(raw(pkt))
    assert scan_iot_data.get_transport(pkt) == exp


def test_get_transport__unknown_udp_port(caplog):
    with caplog.at_level(logging.ERROR):
        test_get_transport(
            Ether() / IPv6() / UDP(sport=54878, dport=51703) / DNS(), (None, None)
        )
    assert "Unknown port in " in caplog.text


def test_get_transport__unknown_transport(caplog):
    with caplog.at_level(logging.ERROR):
        test_get_transport(
            Ether() / IPv6(nh=33) / UDP(sport=53, dport=51703) / DNS(), (None, None)
        )
    assert "Unknown transport for " in caplog.text


def test_get_transport__ignore_icmp():
    with pytest.raises(scan_iot_data.Ignore):
        test_get_transport(
            Ether() / IP() / ICMP(type=3, code=1) / IP() / UDP(sport=53), (None, None)
        )


@pytest.mark.parametrize(
    "record, exp",
    [
        (DNSRR(type="A", rdata="192.0.197.122"), "192.0.197.122"),
        (DNSRR(type="AAAA", rdata="2001:db8::1"), "2001:db8::1"),
        (
            DNSRRNSEC(),
            "rrname=b'.'|type=47|rclass=1|ttl=0|rdlen=None|nextname=b'.'|"
            "typebitmaps=b''",
        ),
    ],
)
def test_get_rdata(record, exp):
    assert str(scan_iot_data.get_rdata(record)) == exp


@pytest.mark.parametrize(
    "pkt, device_mapping, exp",
    [
        (UDP(), {"192.0.140.200": "Test device"}, None),
        (IP(src="192.0.140.200"), None, None),
        (
            IP(src="192.0.140.200"),
            {"192.0.140.200": scan_iot_data.EXCLUDED_DEVICES[0]},
            None,
        ),
        (IP(src="192.0.140.200"), {"192.0.140.200": "Gateway"}, None),
        (IP(src="192.0.140.200"), {"192.0.140.200": "Test device"}, "Test device"),
        (IP(dst="192.0.140.200"), {"192.0.140.200": "Test device"}, "Test device"),
        (
            IP(src="192.0.140.200", dst="192.0.140.201"),
            {"192.0.140.200": "Test device 1", "192.0.140.201": "Test device 2"},
            ("Test device 1", "Test device 2"),
        ),
        (
            IP(src="192.0.140.201", dst="192.0.140.200"),
            {"192.0.140.200": "Test device 1", "192.0.140.201": "Test device 2"},
            ("Test device 2", "Test device 1"),
        ),
    ],
)
def test_get_device(pkt, device_mapping, exp):
    assert scan_iot_data.get_device(pkt, device_mapping) == exp


PCAP_FILENAME = "test.pcap"
TARBALL_FILENAME = "test.tar.gz"


@pytest.fixture
def pcap_file(tmpdir_factory, pkts):
    path = tmpdir_factory.mktemp("data")
    fn = path.join(PCAP_FILENAME)
    pcap = PcapWriter(str(fn), append=True)
    for pkt in pkts:
        pcap.write(Ether() / pkt)
    pcap.close()
    yield str(fn)
    shutil.rmtree(path)


@pytest.mark.parametrize(
    "pkts, pcap_filename, device_mapping, exp",
    [
        ([IP() / UDP(sport=1234, dport=1234) / "abcdfg"], None, None, []),
        (
            [
                IP(src="192.0.31.55")
                / UDP(sport=53)
                / DNS(qd=[DNSQR(qname="www.example.com")])
            ],
            None,
            None,
            [
                {
                    "tarball": TARBALL_FILENAME,
                    "pcap_name": PCAP_FILENAME,
                    "frame_no": 0,
                    "device": None,
                    "transport": "Do53",
                    "tid": 0,
                    "msg_type": "query",
                    "msg_len": 33,
                    "qdcount": 1,
                    "ancount": 0,
                    "nscount": 0,
                    "arcount": 0,
                    "section": "qd",
                    "name": "www.example.com.",
                    "type": "A",
                    "class": "IN",
                }
            ],
        ),
        (
            [
                IP(src="192.0.31.55")
                / UDP(sport=53)
                / DNS(qd=[DNSQR(qname="www.example.com")])
            ],
            "pcap_test.pcap",
            None,
            [
                {
                    "tarball": TARBALL_FILENAME,
                    "pcap_name": "pcap_test.pcap",
                    "frame_no": 0,
                    "device": None,
                    "transport": "Do53",
                    "tid": 0,
                    "msg_type": "query",
                    "msg_len": 33,
                    "qdcount": 1,
                    "ancount": 0,
                    "nscount": 0,
                    "arcount": 0,
                    "section": "qd",
                    "name": "www.example.com.",
                    "type": "A",
                    "class": "IN",
                }
            ],
        ),
        (
            [
                IP(src="192.0.31.55")
                / UDP(sport=53)
                / DNS(qd=[DNSQR(qname="www.example.com")])
            ],
            None,
            {"192.0.31.54": "Test device"},
            [],
        ),
        (
            [
                IP(src="192.0.31.55")
                / UDP(sport=53)
                / DNS(qd=[DNSQR(qname="www.example.com")])
            ],
            None,
            {"192.0.31.55": "Test device"},
            [
                {
                    "tarball": TARBALL_FILENAME,
                    "pcap_name": PCAP_FILENAME,
                    "frame_no": 0,
                    "device": "Test device",
                    "transport": "Do53",
                    "tid": 0,
                    "msg_type": "query",
                    "msg_len": 33,
                    "qdcount": 1,
                    "ancount": 0,
                    "nscount": 0,
                    "arcount": 0,
                    "section": "qd",
                    "name": "www.example.com.",
                    "type": "A",
                    "class": "IN",
                }
            ],
        ),
        (
            [
                IP(src="192.0.31.55")
                / UDP(dport=5353, sport=33540)
                / DNS(qd=[DNSQR(qclass=0x8001, qname="www.example.com")])
            ],
            None,
            {"192.0.31.55": "Test device"},
            [
                {
                    "tarball": TARBALL_FILENAME,
                    "pcap_name": PCAP_FILENAME,
                    "frame_no": 0,
                    "device": "Test device",
                    "transport": "MDNS",
                    "tid": 0,
                    "msg_type": "query",
                    "msg_len": 33,
                    "qdcount": 1,
                    "ancount": 0,
                    "nscount": 0,
                    "arcount": 0,
                    "section": "qd",
                    "name": "www.example.com.",
                    "type": "A",
                    "class": "IN",
                }
            ],
        ),
        (
            [
                IP(src="192.0.31.55")
                / ICMP(type=3, code=1)
                / IP(dst="192.0.31.55")
                / UDP(sport=53)
                / DNS(qd=[DNSQR(qname="www.example.com")])
            ],
            None,
            None,
            [],
        ),
        (
            [IP(src="192.0.31.55") / UDP(sport=53) / DNS()],
            None,
            None,
            [],
        ),
        (
            [
                IP(src="192.0.31.55")
                / UDP(sport=53)
                / DNS(
                    qr=1,
                    qd=[DNSQR(qname="www.example.com")],
                    an=[DNSRR(rrname="www.example.com", ttl=42, rdata="192.0.106.165")],
                )
            ],
            None,
            {"192.0.31.55": "Test device"},
            [
                {
                    "tarball": TARBALL_FILENAME,
                    "pcap_name": PCAP_FILENAME,
                    "frame_no": 0,
                    "device": "Test device",
                    "transport": "Do53",
                    "tid": 0,
                    "msg_type": "response",
                    "msg_len": 64,
                    "qdcount": 1,
                    "ancount": 1,
                    "nscount": 0,
                    "arcount": 0,
                    "section": "qd",
                    "name": "www.example.com.",
                    "type": "A",
                    "class": "IN",
                },
                {
                    "tarball": TARBALL_FILENAME,
                    "pcap_name": PCAP_FILENAME,
                    "frame_no": 0,
                    "device": "Test device",
                    "transport": "Do53",
                    "tid": 0,
                    "msg_type": "response",
                    "msg_len": 64,
                    "qdcount": 1,
                    "ancount": 1,
                    "nscount": 0,
                    "arcount": 0,
                    "section": "an",
                    "name": "www.example.com.",
                    "type": "A",
                    "class": "IN",
                    "ttl": 42,
                    "rdata": "192.0.106.165",
                },
            ],
        ),
    ],
)
def test_analyze_queries(caplog, pcap_file, pcap_filename, device_mapping, exp):
    for e in exp:
        if e and "pcap_name" in e and e["pcap_name"] == PCAP_FILENAME:
            e["pcap_name"] = pcap_file
    with open(pcap_file, "rb") as pcap, caplog.at_level(logging.ERROR):
        assert (
            scan_iot_data.analyze_queries(
                pcap, TARBALL_FILENAME, pcap_filename, device_mapping=device_mapping
            )
            == exp
        )


def test_analyze_queries__no_pcap_file(caplog):
    with open(__file__, "rb") as pcap, caplog.at_level(logging.ERROR):
        assert scan_iot_data.analyze_queries(pcap, TARBALL_FILENAME, None) == []


@pytest.mark.parametrize(
    "pkts",
    [IP(src="192.0.31.55") / UDP(sport=53) / DNS(qd=[DNSQR(qname="www.example.com")])],
)
def test_analyze_queries__no_transport(monkeypatch, caplog, pcap_file):
    monkeypatch.setattr(scan_iot_data, "get_transport", lambda pkt: (None, 55))
    with open(pcap_file, "rb") as pcap, caplog.at_level(logging.ERROR):
        assert scan_iot_data.analyze_queries(pcap, TARBALL_FILENAME, None) == [
            {
                "ancount": 0,
                "arcount": 0,
                "class": "IN",
                "device": None,
                "frame_no": 0,
                "msg_len": 55,
                "msg_type": "query",
                "name": "www.example.com.",
                "nscount": 0,
                "pcap_name": pcap_file,
                "qdcount": 1,
                "section": "qd",
                "tarball": "test.tar.gz",
                "tid": 0,
                "transport": None,
                "type": "A",
            },
        ]
    assert "No transport for" in caplog.text


def test_print_progress(capsys):
    scan_iot_data.print_progress(90, 100, length=10)
    captured = capsys.readouterr()
    assert captured.out == "\r |█████████-| 90.0% \r"
    scan_iot_data.print_progress(100, 100, length=10)
    captured = capsys.readouterr()
    assert captured.out == "\r |██████████| 100.0% \r\n"


def test_print_loading(capsys):
    test = scan_iot_data.PrintLoading("Test load")
    test.start()
    time.sleep(0.5)
    test.stop()
    captured = capsys.readouterr()
    assert "Test load ⠋\rTest load ⠙\r" in captured.out


@pytest.fixture
def the_tarball():
    script_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(script_path, "test-fixtures", "test.tgz")


def test_analyze_tarball(the_tarball):
    csvfile = io.StringIO()
    scan_iot_data.analyze_tarball(the_tarball, csvfile)
    assert (
        csvfile.getvalue()
        == "test.tgz,test01.pcap,1,,Do53,0,query,33,1,0,0,0,qd,www.example.com.,A,IN,,"
        "\r\n"
        "test.tgz,test02.pcap,0,,Do53,0,query,33,1,0,0,0,qd,www.example.com.,A,IN,,\r\n"
    )


def test_tarfile_to_csv(mocker):
    csv_open = mocker.mock_open()
    mocker.patch("builtins.open", csv_open)
    analyze_tarball = mocker.patch("collect.scan_iot_data.analyze_tarball")
    scan_iot_data.tarfile_to_csv("test.tgz")
    analyze_tarball.assert_called_once()
    handle = csv_open()
    handle.write.assert_called_once_with(f"{','.join(scan_iot_data.RECORD_FIELDS)}\r\n")


def test_find_device_mapping():
    script_path = os.path.dirname(os.path.realpath(__file__))
    dirname = os.path.join(script_path, "test-fixtures")
    assert scan_iot_data.find_device_mapping(dirname) == {"192.0.223.215": "The device"}


def test_tarfile_dir_to_csv(mocker):
    csv_open = mocker.mock_open()
    open_mock = mocker.patch("builtins.open", csv_open)
    analyze_tarball = mocker.patch("collect.scan_iot_data.analyze_tarball")
    mocker.patch("tarfile.is_tarfile", lambda x: True)
    script_path = os.path.dirname(os.path.realpath(__file__))
    dirname = os.path.join(script_path, "test-fixtures")
    scan_iot_data.tarfile_dir_to_csv(dirname)
    analyze_tarball.assert_called()
    handle = csv_open()
    handle.write.assert_called_once_with(f"{','.join(scan_iot_data.RECORD_FIELDS)}\r\n")

    open_mock.reset_mock()
    analyze_tarball.reset_mock()
    mocker.patch("tarfile.is_tarfile", lambda x: False)
    dirname += "/"
    scan_iot_data.tarfile_dir_to_csv(dirname)
    analyze_tarball.assert_not_called()
    handle = csv_open()
    handle.write.assert_called_once_with(f"{','.join(scan_iot_data.RECORD_FIELDS)}\r\n")


def test_main(mocker):
    mocker.patch("sys.argv", ["cmd", "testfile"])
    mocker.patch("os.path.isdir", lambda x: True)
    tarfile_dir_to_csv = mocker.patch("collect.scan_iot_data.tarfile_dir_to_csv")
    tarfile_to_csv = mocker.patch("collect.scan_iot_data.tarfile_to_csv")
    scan_iot_data.main()
    tarfile_to_csv.assert_not_called()
    tarfile_dir_to_csv.assert_called_once_with("testfile")

    mocker.patch("os.path.isdir", lambda x: False)
    tarfile_dir_to_csv.reset_mock()
    scan_iot_data.main()
    tarfile_to_csv.assert_called_once_with("testfile")
    tarfile_dir_to_csv.assert_not_called()
