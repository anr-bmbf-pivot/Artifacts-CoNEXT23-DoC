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
import tarfile

from scapy.all import rdpcap
from scapy.layers.dns import DNSRRNSEC, DNSRRSRV, DNSRRSOA

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"

PROGRESS_LENGTH = 25
RECORD_FIELDS = [
    "pcap_name",
    "frame_no",
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


class Ignore(Exception):
    pass


def get_transport(pkt):
    if "UDP" in pkt:
        udp = pkt["UDP"]
        if pkt["DNS"].qr:
            if udp.sport == 53:
                return "Do53", pkt["UDP"].len - 8
            if udp.sport == 5353:
                return "MDNS", pkt["UDP"].len - 8
            logging.error("Unknown sport in %r", pkt)
        else:
            if udp.dport == 53:
                return "Do53", pkt["UDP"].len - 8
            if udp.dport == 5353:
                return "MDNS", pkt["UDP"].len - 8
            logging.error("Unknown dport in %r", pkt)
    elif "ICMP" in pkt:
        raise Ignore
    else:
        logging.error("Unknown transport for %r", pkt)
    return None, None


def get_rdata(record):
    if isinstance(record, (DNSRRNSEC, DNSRRSRV, DNSRRSOA)):
        return "|".join(
            f"{f.name}={getattr(record, f.name)}"
            for f in record.fields_desc
            if f not in ["rrname", "type", "rclass", "ttl", "rdlen"]
        )
    try:
        return record.rdata
    except AttributeError:
        logging.error("%r has no rdata attribute", record)
        raise


def analyze_queries(pcap_file, pcap_filename=None):
    # pylint: disable=too-many-locals,too-many-branches
    rows = []
    for frame_no, pkt in enumerate(rdpcap(pcap_file)):
        if "DNS" not in pkt:
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
                qd = dns.qd[i]
                name = qd.qname.decode()
                typ = qd.fields_desc[1].i2repr(qd, qd.qtype)
                if transport == "MDNS":
                    cls = qd.fields_desc[2].i2repr(qd, qd.qclass & 0b0111111111111111)
                else:
                    cls = qd.fields_desc[2].i2repr(qd, qd.qclass)
                rows.append(
                    {
                        "pcap_name": pcap_file.name
                        if pcap_filename is None
                        else pcap_filename,
                        "frame_no": frame_no,
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
                        "pcap_name": pcap_file.name
                        if pcap_filename is None
                        else pcap_filename,
                        "frame_no": frame_no,
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
    printEnd="\r",
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
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    progress_bar = fill * filledLength + "-" * (length - filledLength)
    print(f"\r{prefix} |{progress_bar}| {percent}% {suffix}", end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()


def analyze_tarball(tar_filename):
    with tarfile.open(tar_filename) as tarball, open(
        f"{tar_filename}.csv", "w", encoding="utf-8"
    ) as csvfile:
        fieldnames = RECORD_FIELDS
        writer = csv.DictWriter(csvfile, fieldnames)
        writer.writeheader()
        csvfile.flush()
        print("Loading tarball...", end="\r")
        total = len(tarball.getnames())
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
            if not info.isfile() or ".pcap" not in info.name:
                continue
            with tarball.extractfile(info) as pcap:
                logging.info("Analyzing %s in %s", info.name, tar_filename)
                queries = analyze_queries(pcap, info.name)
                for query in queries:
                    writer.writerow(query)
                csvfile.flush()
        print_progress(
            total,
            total,
            prefix="Progress: ",
            suffix=f"Complete ({total}/{total} PCAPs scanned)",
            length=PROGRESS_LENGTH,
        )


def main():
    # logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("tarfile")
    args = parser.parse_args()

    analyze_tarball(args.tarfile)


if __name__ == "__main__":
    main()
