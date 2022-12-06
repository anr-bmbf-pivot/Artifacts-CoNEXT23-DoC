#! /usr/bin/env python3

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
import multiprocessing
import os
import queue
import re
import subprocess
import threading

import networkx

try:
    from . import plot_common as pc
except ImportError:  # pragma: no cover
    import plot_common as pc

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021-22 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


CSV_NAME = os.path.join(pc.DATA_PATH, "doc-eval-max_age-link_utilization.csv")
TSHARK_FIELDS = [
    "-e",
    "frame.number",
    "-e",
    "wpan.src64",
    "-e",
    "wpan.dst64",
    "-e",
    "6lowpan.frag.tag",
    "-e",
    "zep.length",
    "-e",
    "_ws.col.Protocol",
    "-e",
    "_ws.col.Info",
]
RESULT_FIELDS = [
    "exp_timestamp",
    "max_age_config",
    "method",
    "dns_cache",
    "client_coap_cache",
    "proxied",
    "node",
    "distance",
    "queries_bytes",
    "queries_packets",
    "queries_frags",
    "responses_bytes",
    "responses_packets",
    "responses_frags",
]
FILTER_FMT = (
    "zep.device_id == {device_id} && "
    "(!icmpv6) && (wpan.frame_type == 0x1) && "
    "(wpan.src64 == {src}) && (wpan.dst64 == {dst})"
)
METHODS = [
    "fetch",
]
PROXIED = [
    0,
    1,
]
CLIENT_COAP_CACHE = [
    0,
    1,
]
DNS_CACHE = [
    0,
    1,
]
MAX_AGE_CONFIGS = [
    "min",
    "subtract",
]


def edge_arg(value):
    try:
        u, v = map(int, value.split(","))
        return u, v
    except ValueError as exc:
        raise ValueError(
            'Edge must be of format "u,v" with u, v being integer'
        ) from exc


def read_pcap(filename, direction, filt):
    proc = subprocess.Popen(
        ["tshark", "-Tfields"] + TSHARK_FIELDS + ["-Y", filt, "-r", filename],
        stdout=subprocess.PIPE,
        bufsize=1,
        universal_newlines=True,
    )
    reader = csv.DictReader(
        proc.stdout, fieldnames=[f for f in TSHARK_FIELDS if f != "-e"], delimiter="\t"
    )
    packets = 0
    frags = 0
    byts = 0
    for row in reader:
        packets += 1
        if row["6lowpan.frag.tag"]:
            frags += 1
        byts += int(row["zep.length"])
    proc.wait()
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, proc.args)
    return {
        f"{direction}_packets": packets,
        f"{direction}_bytes": byts,
        f"{direction}_frags": frags,
    }


def get_link(nodes, match, file, edge, params, distance, sync_queue):
    row = {
        "exp_timestamp": int(match["timestamp"]),
        "distance": distance,
        "node": edge[1],
    }
    row.update(params)
    device_id = 0x3000 | edge[1]
    filter_query = FILTER_FMT.format(
        device_id=device_id, src=nodes[edge[1]], dst=nodes[edge[0]]
    )
    filter_resp = FILTER_FMT.format(
        device_id=device_id, src=nodes[edge[0]], dst=nodes[edge[1]]
    )
    row.update(read_pcap(file, "queries", filter_query))
    row.update(read_pcap(file, "responses", filter_resp))
    sync_queue.put(row)


def get_nodes(files, sink, graph):
    nodes = {}
    for _, file in files:
        with open(
            file.replace(".pcap.gz", ".border-router.log"), encoding="utf-8"
        ) as f:
            for line in f:
                match = re.search(
                    r"Long HWaddr:\s+(([0-9A-F]{2}:){7}[0-9A-F]{2})", line
                )
                if match:
                    addr = match[1].lower()
                    if sink in nodes and nodes[sink] != addr:
                        raise ValueError(  # pragma: no cover
                            f"m3-{sink} address differs in {f.name}: "
                            f"{addr} != {nodes[sink]}"
                        )
                    nodes[sink] = addr
                    break
        with open(file.replace(".pcap.gz", ".log"), encoding="utf-8") as f:
            for line in f:
                match = re.search(
                    r";m3-(\d+);.*Long HWaddr:\s+(([0-9A-F]{2}:){7}[0-9A-F]{2})", line
                )
                if match:
                    node_id = int(match[1])
                    addr = match[2].lower()
                    if node_id in nodes and nodes[node_id] != addr:
                        raise ValueError(  # pragma: no cover
                            f"m3-{sink} address differs in {f.name}: "
                            f"{addr} != {nodes[sink]}"
                        )
                    nodes[node_id] = addr
    if files:
        diff = set(graph.nodes) - set(nodes.keys())
        if diff != set():
            raise ValueError(
                "Nodes of graph not found in files "
                f"({', '.join(f[1] for f in files)}): {diff}"
            )
        diff = set(nodes.keys()) - set(graph.nodes)
        if files and diff != set():
            raise ValueError(
                "Nodes in file not found in graph "
                f"({', '.join(f[1] for f in files)}): {diff}"
            )
    return nodes


def extract_from_pcaps(files, sink, graph, params):
    sync_queue = queue.Queue()
    threads = []
    nodes = get_nodes(files, sink, graph)
    res = []
    for match, file in files:
        for edge in networkx.bfs_edges(graph, sink):
            thread = threading.Thread(
                target=get_link,
                args=(
                    nodes,
                    match,
                    file,
                    edge,
                    params,
                    networkx.shortest_path_length(graph, sink, edge[1]),
                    sync_queue,
                ),
            )
            threads.append(thread)
            thread.start()
            if len(threads) > (multiprocessing.cpu_count() * 2):
                threads[0].join()
                threads.pop(0)
            if sync_queue.full():  # pragma: no cover
                try:
                    while True:
                        res.append(sync_queue.get_nowait())
                        sync_queue.task_done()
                except queue.Empty:
                    pass
    for thread in threads:
        thread.join()
    try:
        while True:
            res.append(sync_queue.get_nowait())
            sync_queue.task_done()
    except queue.Empty:
        pass
    sync_queue.join()
    return res


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "sink",
        type=int,
        help="Node number of sink",
    )
    parser.add_argument(
        "edges",
        nargs="+",
        metavar="u,v",
        type=edge_arg,
        help="Link in the network (pair of node numbers, e.g. 205,202 for link "
        "between m3-205 and m3-202)",
    )
    args = parser.parse_args()

    res = []

    graph = networkx.DiGraph()
    graph.add_edges_from(args.edges)
    if args.sink not in graph.nodes:
        raise ValueError("sink not in provided edges")

    pc.CSV_NAME_PATTERN_FMT = rf"{pc.FILENAME_PATTERN_FMT}.pcap.gz"
    pc.CSV_EXT_FILTER = ["pcap.gz"]
    for max_age_config in MAX_AGE_CONFIGS:
        for method in METHODS:
            for dns_cache in DNS_CACHE:
                for client_coap_cache in CLIENT_COAP_CACHE:
                    for proxied in PROXIED:
                        params = {
                            "max_age_config": max_age_config,
                            "method": method,
                            "dns_cache": dns_cache,
                            "client_coap_cache": client_coap_cache,
                            "proxied": proxied,
                        }
                        files = pc.get_files(
                            exp_type="max_age",
                            transport="coap",
                            avg_queries_per_sec=5.0,
                            **params,
                        )
                        res.extend(
                            extract_from_pcaps(
                                files[-pc.RUNS :], args.sink, graph, params
                            )
                        )
    with open(CSV_NAME, "w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, RESULT_FIELDS)
        writer.writeheader()
        for row in res:
            writer.writerow(row)


if __name__ == "__main__":
    main()  # pragma: no cover
