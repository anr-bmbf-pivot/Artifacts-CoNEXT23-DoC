#! /usr/bin/env python
#
# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import argparse
import logging
import csv
import os
import tarfile
import time
import threading

from scapy.all import PcapReader, Scapy_Exception
from scapy.layers.dns import DNSRR

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"

PROGRESS_LENGTH = 25
RECORD_FIELDS = [
    "tarball",
    "pcap_name",
    "frame_no",
    "device",
    "transport",
    "tid",
    "msg_type",
    "msg_len",
    "qdcount",
    "ancount",
    "nscount",
    "arcount",
    "section",
    "name",
    "type",
    "class",
    "ttl",
    "rdata",
]
EXCLUDED_DEVICES = [
    "AndroidTablet",
    "iPhone",
    "iPad",
    "MyCloudEX2Ultra",
    "NintendoSwitch",
    "PlayStation4",
    "TP-LinkWiFiPlug",
    "UbuntuDesktop",
    "XboxOneX",
]


class Ignore(Exception):
    pass


def get_transport(pkt):
    if "UDP" in pkt:
        udp = pkt["UDP"]
        if udp.sport == 53 or udp.dport == 53:
            return "Do53", pkt["UDP"].len - 8
        if udp.sport == 5353 or udp.dport == 5353:
            return "MDNS", pkt["UDP"].len - 8
        logging.error("Unknown port in %r", pkt)
    elif "TCP" in pkt:
        return "DoTCP", pkt["DNS"].length
    elif "ICMP" in pkt:
        raise Ignore
    else:
        logging.error("Unknown transport for %r", pkt)
    return None, None


def get_rdata(record):
    if isinstance(record, DNSRR):
        return record.rdata
    return "|".join(
        f"{f.name}={getattr(record, f.name)}"
        for f in record.fields_desc
        if f not in ["rrname", "type", "rclass", "ttl", "rdlen"]
    )


def get_device(pkt, device_mapping=None):
    device = None
    if device_mapping and "IP" in pkt:
        if pkt["IP"].src in device_mapping:
            device = device_mapping[pkt["IP"].src]
        if pkt["IP"].dst in device_mapping:
            if device is None:
                device = device_mapping[pkt["IP"].dst]
            else:
                device = (device, device_mapping[pkt["IP"].dst])
    if device is not None:
        if device == "Gateway":
            # exclude messages only involving the Gateway
            return None
        for excluded_device in EXCLUDED_DEVICES:
            if excluded_device in device:
                return None
    return device


def analyze_queries(  # noqa: C901
    pcap_file, tar_filename, pcap_filename=None, device_mapping=None
):
    # pylint: disable=too-many-locals,too-many-branches
    rows = []
    try:
        pkts = PcapReader(pcap_file)
    except Scapy_Exception as exc:
        logging.error("%s", exc)
        return rows
    tar_filename = os.path.basename(tar_filename)
    spinner = "⠧⠦⠤⠠⠠⠤⠦⠧⠇⠃⠁⠃⠇"
    for frame_no, pkt in enumerate(pkts):
        if "DNS" not in pkt:
            continue
        device = get_device(pkt, device_mapping)
        if device_mapping is not None and device is None:
            continue
        dns = pkt["DNS"]
        try:
            transport, msg_len = get_transport(pkt)
        except Ignore:
            continue
        if transport is None:
            logging.error("No transport for %r in %s", pkt, pcap_file)
        if dns.qr:
            msg_type = "response"
        else:
            msg_type = "query"
        if dns.qd:
            for i in range(len(dns.qd.layers())):
                question = dns.qd[i]
                name = question.qname.decode()
                typ = question.fields_desc[1].i2repr(question, question.qtype)
                if transport == "MDNS":
                    cls = question.fields_desc[2].i2repr(
                        question, question.qclass & 0b0111111111111111
                    )
                else:
                    cls = question.fields_desc[2].i2repr(question, question.qclass)
                rows.append(
                    {
                        "tarball": tar_filename,
                        "pcap_name": pcap_file.name
                        if pcap_filename is None
                        else pcap_filename,
                        "frame_no": frame_no,
                        "device": device,
                        "transport": transport,
                        "tid": dns.id,
                        "msg_type": msg_type,
                        "msg_len": msg_len,
                        "qdcount": dns.qdcount,
                        "ancount": dns.ancount,
                        "nscount": dns.nscount,
                        "arcount": dns.arcount,
                        "section": "qd",
                        "name": name,
                        "type": typ,
                        "class": cls,
                    }
                )
        for sname, section in [("an", dns.an), ("ns", dns.ns), ("ar", dns.ar)]:
            if not section:
                continue
            for i in range(len(section.layers())):
                record = section[i]
                name = record.rrname.decode()
                typ = record.fields_desc[1].i2repr(record, record.type)
                cls = record.fields_desc[2].i2repr(record, record.rclass)
                rdata = get_rdata(record)
                # TODO: parse EDNS(0) options properly?     pylint: disable=fixme
                rows.append(
                    {
                        "tarball": tar_filename,
                        "pcap_name": pcap_file.name
                        if pcap_filename is None
                        else pcap_filename,
                        "frame_no": frame_no,
                        "device": device,
                        "transport": transport,
                        "tid": dns.id,
                        "msg_type": msg_type,
                        "msg_len": msg_len,
                        "qdcount": dns.qdcount,
                        "ancount": dns.ancount,
                        "nscount": dns.nscount,
                        "arcount": dns.arcount,
                        "section": sname,
                        "name": name,
                        "type": typ,
                        "class": cls,
                        "ttl": record.ttl if hasattr(record, "ttl") else None,
                        "rdata": rdata,
                    }
                )
        print(f"{spinner[(frame_no // 100) % len(spinner)]}oading :", end="\r")
    return rows


# Print iterations progress
def print_progress(  # pylint: disable=too-many-arguments
    iteration,
    total,
    prefix="",
    suffix="",
    decimals=1,
    length=100,
    fill="█",
    print_end="\r",
):
    """
    See https://stackoverflow.com/a/34325723
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        print_end   - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    progress_bar = fill * filled_length + "-" * (length - filled_length)
    print(f"\r{prefix} |{progress_bar}| {percent}% {suffix}", end=print_end)
    # Print New Line on Complete
    if iteration == total:
        print()


class PrintLoading(threading.Thread):
    def __init__(self, msg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.msg = msg
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def run(self):
        count = 0
        spinner = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        while not self._stop.is_set():
            print(f"{self.msg} {spinner[count % len(spinner)]}", end="\r")
            count += 1
            time.sleep(1 / 12)


def analyze_tarball(tar_filename, csvfile, device_mapping=None):
    with tarfile.open(tar_filename) as tarball:
        writer = csv.DictWriter(csvfile, RECORD_FIELDS)
        csvfile.flush()
        print_loading = PrintLoading("Loading tarball...")
        print_loading.start()
        try:
            total = len(tarball.getnames())
        finally:
            print_loading.stop()
            del print_loading
        print_progress(
            0,
            total,
            prefix="Progress: ",
            suffix=f"Complete (0/{total} PCAPs scanned)",
            length=PROGRESS_LENGTH,
        )
        for i, info in enumerate(tarball):
            print_progress(
                i,
                total,
                prefix="Progress: ",
                suffix=f"Complete ({i}/{total} PCAPs scanned)",
                length=PROGRESS_LENGTH,
            )
            if not info.isfile():
                continue
            with tarball.extractfile(info) as pcap:
                logging.info("Analyzing %s in %s", info.name, tar_filename)
                writer.writerows(
                    analyze_queries(
                        pcap,
                        tar_filename,
                        info.name,
                        device_mapping=device_mapping,
                    )
                )
                csvfile.flush()
        print_progress(
            total,
            total,
            prefix="Progress: ",
            suffix=f"Complete ({total}/{total} PCAPs scanned)",
            length=PROGRESS_LENGTH,
        )


def tarfile_to_csv(tar_filename):
    with open(f"{tar_filename}.csv", "w", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, RECORD_FIELDS)
        writer.writeheader()
        analyze_tarball(tar_filename, csvfile)


def find_device_mapping(dirname):
    device_mapping_file = None
    for root, _, files in os.walk(dirname):
        for filename in files:
            filename = os.path.join(root, filename)
            if filename.endswith("/device_mapping.csv"):
                assert device_mapping_file is None, "Multiple device mappings found"
                device_mapping_file = filename
    res = {}
    with open(device_mapping_file, encoding="utf-8") as csv_map_file:
        csv_map = csv.DictReader(csv_map_file, fieldnames=["device", "address"])
        for row in csv_map:
            assert row["address"] not in res
            res[row["address"]] = row["device"]
    return res


def tarfile_dir_to_csv(dirname):
    while dirname.endswith(os.sep):
        dirname = dirname[:-1]
    device_mapping = find_device_mapping(dirname)
    with open(f"{dirname}.csv", "w", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, RECORD_FIELDS)
        writer.writeheader()
        for root, _, files in os.walk(dirname):
            for filename in files:
                filename = os.path.join(root, filename)
                if tarfile.is_tarfile(filename):
                    analyze_tarball(filename, csvfile, device_mapping=device_mapping)


def main():
    # logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument(dest="tarfile", metavar="tarfile or directory")
    args = parser.parse_args()
    if os.path.isdir(args.tarfile):
        tarfile_dir_to_csv(args.tarfile)
    else:
        tarfile_to_csv(args.tarfile)


if __name__ == "__main__":
    main()  # pragma: no cover
