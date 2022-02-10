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
import csv
import gzip
import os
import subprocess

from pprint import pformat

from scapy.layers.dns import dnstypes, dnsqtypes, dnsclasses

from scan_iot_data import RECORD_FIELDS, print_progress

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
DATA_PATH = os.environ.get(
    "DATA_PATH", os.path.join(SCRIPT_PATH, "..", "..", "..", "results")
)


def to_dnstype_str(typ):
    return dnstypes.get(int(typ), dnsqtypes.get(int(typ), int(typ)))


PROGRESS_LENGTH = 40
SHARK_FIELDS = [
    "_ws.col.Time",
    "ip.version",
    "udp.length",
    "dns.flags.opcode",
    "dns.flags.response",
    "dns.flags.authoritative",
    "dns.flags.rcode",
    "dns.count.queries",
    "dns.count.answers",
    "dns.count.auth_rr",
    "dns.count.add_rr",
    "dns.qry.class",
    "dns.qry.type",
    "dns.qry.name.len",
    "dns.resp.class",
    "dns.resp.type",
    "dns.resp.len",
]
COUNT_FIELDS = [
    "dns.count.queries",
    "dns.count.answers",
    "dns.count.auth_rr",
    "dns.count.add_rr",
]
SHARK_RECORD_MAPPING = {
    "udp.length": lambda x: ("msg_len", int(x) - 8),
    "dns.flags.response": lambda x: ("msg_type", "response" if int(x) else "query"),
    "dns.count.queries": "qdcount",
    "dns.count.answers": "ancount",
    "dns.count.auth_rr": "nscount",
    "dns.count.add_rr": "arcount",
    "dns.qry.class": lambda x: (
        "class",
        dnsclasses.get(int(x[2:], base=16), int(x[2:], base=16)) if x else None,
    ),
    "dns.qry.type": lambda x: ("type", to_dnstype_str(x) if x else None),
    "dns.qry.name.len": "name_len",
}


def map_field(field, value):
    new_field = SHARK_RECORD_MAPPING[field]
    if callable(new_field):
        return new_field(value)
    return new_field, value


def reformat_dns_scan(csv_gz_name):  # noqa: C901
    # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    out_name = os.path.join(os.path.join(DATA_PATH, os.path.basename(csv_gz_name)))
    with gzip.open(csv_gz_name, "rt") as in_csvfile, gzip.open(
        out_name, "wt"
    ) as out_csvfile:
        reader = csv.DictReader(in_csvfile, fieldnames=SHARK_FIELDS, delimiter="|")
        record_fields = [
            "name_len" if f == "name" else "rdata_len" if f == "rdata" else f
            for f in RECORD_FIELDS
        ]
        writer = csv.DictWriter(out_csvfile, fieldnames=record_fields)
        writer.writeheader()
        total = int(subprocess.check_output(f"zcat {csv_gz_name} | wc -l", shell=True))
        print_progress(
            0,
            total,
            prefix="Progress: ",
            length=PROGRESS_LENGTH,
        )
        count = 0
        for id_, row in enumerate(reader):
            if row["ip.version"] not in ["4", "6"]:
                continue
            if not row["dns.qry.class"]:
                continue
            for field in COUNT_FIELDS:
                try:
                    row[field] = int(row[field])
                except ValueError:
                    row[field] = float("inf")
            if any(row[f] > 10000 for f in COUNT_FIELDS):
                # use count fields as gauge if valid DNS
                continue
            classes = row["dns.qry.class"].split(",")
            types = row["dns.qry.type"].split(",")
            name_lens = row["dns.qry.name.len"].split(",")
            resp_classes = row["dns.resp.class"].split(",")
            resp_types = row["dns.resp.type"].split(",")
            rdata_lens = [r for r in row["dns.resp.len"].split(",") if r]
            if len(name_lens) != row["dns.count.queries"]:
                continue
            if any(not int(r) for r in rdata_lens):
                continue
            if any(
                int(c[2:], base=16) not in dnsclasses if c else False for c in classes
            ) or any(
                int(c[2:], base=16) not in dnsclasses if c else False
                for c in resp_classes
            ):
                continue
            count += 1
            if len(name_lens) > 1:
                assert (
                    len(classes)
                    == len(types)
                    == len(name_lens)
                    == row["dns.count.queries"]
                ), (
                    f"Unbalanced sub-queries {row['dns.count.queries']}|"
                    f"{row['dns.qry.class']}|{row['dns.qry.type']}|"
                    f"{row['dns.qry.name.len']}"
                )
                for cls, typ, name_len in zip(classes, types, name_lens):
                    tmp_row = dict(
                        map_field(k, v)
                        for k, v in row.items()
                        if k in SHARK_RECORD_MAPPING
                        and k
                        not in ["dns.qry.class", "dns.qry.type", "dns.qry.name.len"]
                    )
                    out_row = dict(tmp_row.items())
                    out_row["pcap_name"] = csv_gz_name
                    out_row["frame_no"] = id_
                    out_row["tid"] = id_
                    out_row["section"] = "qd"
                    if cls:
                        cls = int(cls[2:], base=16)
                        out_row["class"] = dnsclasses.get(cls, cls)
                    if typ:
                        out_row["type"] = to_dnstype_str(typ)
                    out_row["name_len"] = int(name_len)
                    writer.writerow(out_row)
            else:
                out_row = dict(
                    map_field(k, v) for k, v in row.items() if k in SHARK_RECORD_MAPPING
                )
                out_row["pcap_name"] = csv_gz_name
                out_row["frame_no"] = id_
                out_row["section"] = "qd"
                out_row["tid"] = id_
                writer.writerow(out_row)

            if len(rdata_lens):
                answers = int(row["dns.count.answers"])
                auth_rr = int(row["dns.count.auth_rr"])
                add_rr = int(row["dns.count.add_rr"])
                for section_count, (cls, typ, rdata_len) in enumerate(
                    zip(resp_classes, resp_types, rdata_lens)
                ):
                    tmp_row = dict(
                        map_field(k, v)
                        for k, v in row.items()
                        if k in SHARK_RECORD_MAPPING
                        and k
                        not in ["dns.qry.class", "dns.qry.type", "dns.qry.name.len"]
                    )
                    if (answers - section_count) > 0:
                        section = "an"
                    elif ((auth_rr + answers) - section_count) > 0:
                        section = "ns"
                    elif ((add_rr + auth_rr + answers) - section_count) > 0:
                        section = "ar"
                    else:
                        assert False, f"Too many response records in\n{pformat(row)}"
                    out_row = dict(tmp_row.items())
                    out_row["pcap_name"] = csv_gz_name
                    out_row["frame_no"] = id_
                    out_row["tid"] = id_
                    out_row["section"] = section
                    if cls:
                        cls = int(cls[2:], base=16)
                        out_row["class"] = dnsclasses.get(cls, cls)
                    if typ:
                        out_row["type"] = to_dnstype_str(typ)
                    out_row["rdata_len"] = int(rdata_len)
                    writer.writerow(out_row)
            print_progress(
                id_ + 1,
                total,
                prefix="Progress: ",
                length=PROGRESS_LENGTH,
            )
    print(f"\n\nFound {count} legitimate DNS messages")


def main():
    # logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_gz")
    args = parser.parse_args()

    reformat_dns_scan(args.csv_gz)


if __name__ == "__main__":
    main()
