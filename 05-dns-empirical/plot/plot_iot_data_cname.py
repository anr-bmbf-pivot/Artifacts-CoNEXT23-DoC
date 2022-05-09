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
import ast
import re
import os

import matplotlib.pyplot
import networkx
import numpy
import pandas

from networkx.drawing.nx_pydot import write_dot as networkx_write_dot

try:
    from . import plot_common as pc
    from . import plot_iot_data_name_lens as name_len
    from . import plot_iot_data_hostname_lens as hostname_len
except ImportError:
    import plot_common as pc
    import plot_iot_data_name_lens as name_len
    import plot_iot_data_hostname_lens as hostname_len

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


CDNS = [
    "amazonaws.com",
    "arrayent.com",
    "cloudapp.net",
    "cloudfront.net.",
    "facebook.com",
    "samsung-svoice.com",
    "samsungcloudsolution.net",
]


def pseudonize_hostname(name):
    name = name.strip(".")
    if (
        name.endswith(".local")
        or name.endswith(".dada.lab")
        or name.endswith(".moniotr.lab")
    ):
        name = re.sub(
            "[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-f]{12}",
            "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
            name,
        )
        name = re.sub("[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}", "XX:XX:XX:XX:XX:XX", name)
    if ".awsdns-" in name:
        name = re.sub(r"awsdns-\d+\.([^.]+)$", r"awsdns-X.\1", name)
    hostname = hostname_len.extract_hostname(name)
    pseudonized = re.sub(r"\d+", "X", hostname)
    return name.replace(hostname, pseudonized)


def pseudonize_ipv4_address(address):
    if address.startswith("192.168.") or address.startswith("10."):
        return "Local IPv4"
    return "Global IPv4"


def pseudonize_ipv6_address(address):
    if address.startswith("fe80:"):
        return "Link local IPv6"
    if address.startswith("fc") or address.startswith("fd"):
        return "IPv6 ULA"
    return "Global IPv6"


def pseudonize(cnames):
    mapping = {}
    for node in cnames.nodes:
        node_type = cnames.nodes[node]["type"]
        if node_type == "ipv4":
            mapping[node] = pseudonize_ipv4_address(node)
        elif node_type == "ipv6":
            mapping[node] = pseudonize_ipv6_address(node)
        elif node_type == "name":
            mapping[node] = pseudonize_hostname(node)
        else:
            assert node_type in ["ipv4", "ipv6", "name"]
    return networkx.relabel_nodes(cnames, mapping)


def get_cname_chain_lengths(cnames):
    cname_chain_lengths = []
    subgraphs = [
        cnames.subgraph(n).copy() for n in networkx.weakly_connected_components(cnames)
    ]
    roots = set()
    leaves = set()
    for graph in subgraphs:
        for node in graph.nodes:
            if graph.in_degree(node) == 0:
                roots.add(node)
            elif graph.out_degree(node) == 0 or all(
                graph.nodes[neighbor]["type"] in ["ipv4", "ipv6"]
                for neighbor in graph.neighbors(node)
            ):
                if graph.nodes[node]["type"] in ["ipv4", "ipv6"]:
                    continue
                leaves.add(node)
    for root in roots:
        for leaf in leaves:
            try:
                shortest_path = networkx.shortest_path(cnames, root, leaf)
            except networkx.NetworkXNoPath:
                continue
            sp_length = len(shortest_path) - 1
            cname_chain_lengths.append(sp_length)
    return cname_chain_lengths


def main():
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, "mlenders_usenix.mplstyle"))
    parser = argparse.ArgumentParser()
    parser.add_argument("iot_data_csvs", nargs="+")
    args = parser.parse_args()
    args.iot_data_csvs = sorted(set(args.iot_data_csvs))
    data_src = []
    for iot_data_csv in args.iot_data_csvs:
        for doi in name_len.DOI_TO_NAME.keys():
            if doi in iot_data_csv.lower():
                data_src.append(name_len.DOI_TO_NAME[doi])
    assert data_src, "Data source can not inferred from CSV name"
    data_src = "+".join(sorted(data_src))
    for filt_name, filt in name_len.FILTERS:
        if "qd_an_only" in filt_name or "no_mdns" in filt_name:
            continue
        if "iotfinder" in data_src and "qrys_only" in filt_name:
            continue
        cnames = networkx.DiGraph()
        for iot_data_csv in args.iot_data_csvs:
            df = pandas.read_csv(iot_data_csv)
            df = name_len.filter_data_frame(df, filt)
            for _, row in df[
                ((df["type"] == "A") | (df["type"] == "AAAA") | (df["type"] == "CNAME"))
                & (df["section"] != "qd")
            ][["type", "name", "rdata"]].iterrows():
                name = row["name"].lower()
                typ = row["type"]
                if typ == "CNAME":
                    # CNAME rdata is present in Python binary string representation
                    cname = ast.literal_eval(row["rdata"]).decode().lower()
                    cnames.add_edge(name, cname, label=typ)
                    cnames.nodes[name]["type"] = "name"
                    cnames.nodes[cname]["type"] = "name"
                elif typ in ["A", "AAAA"]:
                    cnames.add_edge(name, row["rdata"], label=typ)
                    cnames.nodes[name]["type"] = "name"
                    cnames.nodes[row["rdata"]]["type"] = (
                        "ipv4" if typ == "A" else "ipv6"
                    )
            del df
        if not len(cnames.nodes):
            continue
        chain_lengths = numpy.array(get_cname_chain_lengths(cnames))
        networkx_write_dot(
            pseudonize(cnames),
            os.path.join(
                pc.DATA_PATH, f"iot-data-cname-chains-{filt_name}@{data_src}.dot"
            ),
        )
        bins = chain_lengths.max() - chain_lengths.min()
        if bins < 1:  # pragma: no cover
            bins = numpy.arange(chain_lengths.min(), chain_lengths.max() + 2)
        matplotlib.pyplot.hist(chain_lengths, bins=bins, density=True, histtype="step")
        matplotlib.pyplot.xticks(numpy.arange(0, 8, 1))
        matplotlib.pyplot.xlim((0, 7.5))
        matplotlib.pyplot.xlabel(r"CNAME chain lengths [\# linked CNAME records]")
        matplotlib.pyplot.ylim((-0.01, 1.01))
        matplotlib.pyplot.ylabel("Density")
        matplotlib.pyplot.tight_layout()
        for ext in pc.OUTPUT_FORMATS:
            matplotlib.pyplot.savefig(
                os.path.join(
                    pc.DATA_PATH,
                    f"iot-data-cname-chain-lens-{filt_name}@{data_src}.{ext}",
                ),
                bbox_inches="tight",
                pad_inches=0.01,
            )
        matplotlib.pyplot.clf()


if __name__ == "__main__":
    main()
