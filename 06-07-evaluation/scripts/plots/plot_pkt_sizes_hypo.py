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
import os

import matplotlib.lines
import matplotlib.patches
import matplotlib.pyplot

try:
    from . import plot_common as pc
    from . import plot_pkt_sizes as pkt_sizes
except ImportError:
    import plot_common as pc
    import plot_pkt_sizes as pkt_sizes

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"

MSG_TYPES = [
    "query",
    "response_aaaa",
]
IEEE802154_HDRS = {
    "802154_worst": (
        2  # IEEE 802.15.4 FCF
        + 1  # IEEE 802.15.4 Sequence number
        + 10  # IEEE 802.15.4 Destination address + PAN
        + 10  # IEEE 802.15.4 Source address + PAN
        + 14  # IEEE 802.15.4 Auxiliary Security Header
        + 8  # IEEE 802.15.4 MIC
    ),
    "802154_best": (
        2  # IEEE 802.15.4 FCF
        + 1  # IEEE 802.15.4 Sequence number
        + 2  # IEEE 802.15.4 Destination address
        + 4  # IEEE 802.15.4 Source address + PAN
        + 0  # IEEE 802.15.4 Auxiliary Security Header
        + 2  # IEEE 802.15.4 FCF
    ),
    "802154_best_sec": (
        2  # IEEE 802.15.4 FCF
        + 1  # IEEE 802.15.4 Sequence number
        + 2  # IEEE 802.15.4 Destination address
        + 4  # IEEE 802.15.4 Source address + PAN
        + 0  # IEEE 802.15.4 Auxiliary Security Header
        + 5  # IEEE 802.15.4 Auxiliary Security Header
        + 8  # IEEE 802.15.4 MIC
    ),
    "802154_riot": (
        2  # IEEE 802.15.4 FCF
        + 1  # IEEE 802.15.4 Sequence number
        + 8  # IEEE 802.15.4 Destination address
        + 10  # IEEE 802.15.4 Source address + PAN
        + 0  # IEEE 802.15.4 Auxiliary Security Header
        + 2  # IEEE 802.15.4 FCF
    ),
    "802154_riot_sec": (
        2  # IEEE 802.15.4 FCF
        + 1  # IEEE 802.15.4 Sequence number
        + 8  # IEEE 802.15.4 Destination address
        + 10  # IEEE 802.15.4 Source address + PAN
        + 5  # IEEE 802.15.4 Auxiliary Security Header
        + 8  # IEEE 802.15.4 MIC
    ),
}
SIXLOWPAN_HDRS = {
    "802154_worst": (1 + 40),  # 6LoWPAN uncompressed dispatch + IPv6 header
    "802154_best": (
        2  # 6LoWPAN IPHC dispatch
        + 2  # 6LoWPAN IPHC source address residue
        + 2  # 6LoWPAN IPHC destination address residue
        + 1  # 6LoWPAN UDP NHC dispatch
        + 1  # 6LoWPAN UDP NHC ports residue
    ),
    "802154_best_sec": (
        2  # 6LoWPAN IPHC dispatch
        + 2  # 6LoWPAN IPHC source address residue
        + 2  # 6LoWPAN IPHC destination address residue
        + 1  # 6LoWPAN UDP NHC dispatch
        + 1  # 6LoWPAN UDP NHC ports residue
    ),
    "802154_riot": (
        2  # 6LoWPAN IPHC dispatch
        + 1  # 6LoWPAN HL residue
        + 16  # 6LoWPAN IPHC source address residue
        + 16  # 6LoWPAN IPHC destination address residue
        + 1  # 6LoWPAN UDP NHC dispatch
        + 4  # 6LoWPAN UDP NHC ports residue
        + 2  # 6LoWPAN UDP NHC checksum residue
    ),
    "802154_riot_sec": (
        2  # 6LoWPAN IPHC dispatch
        + 1  # 6LoWPAN HL residue
        + 16  # 6LoWPAN IPHC source address residue
        + 16  # 6LoWPAN IPHC destination address residue
        + 1  # 6LoWPAN UDP NHC dispatch
        + 4  # 6LoWPAN UDP NHC ports residue
        + 2  # 6LoWPAN UDP NHC checksum residue
    ),
}
COAP_REQUEST_OUTER_HDRS = {
    "coap_worst": (
        1  # Ver + T + TKL
        + 1  # Code
        + 2  # MID
        + 8  # Token
        + 1  # End of options marker
        + 1  # OSCORE option header
        + 5  # 5 bytes Partial IV
        + 1  # KID context (could be longer)?
    ),
    "coap_best": (
        1  # Ver + T + TKL
        + 1  # Code
        + 2  # MID
        + 1  # Token
        + 1  # End of options marker
        + 1  # OSCORE option header
    ),
    "coap_exp": (
        1  # Ver + T + TKL
        + 1  # Code
        + 2  # MID
        + 2  # Token
        + 4  # OSCORE option
        + 1  # End of options marker
    ),
}
COAP_RESPONSE_OUTER_HDRS = {
    "coap_worst": (
        1  # Ver + T + TKL
        + 1  # Code
        + 2  # MID
        + 8  # Token
        + 1  # End of options marker
        + 1  # OSCORE option header
        + 5  # 5 bytes Partial IV
        # + KID context?
        + 8  # E-Tag
    ),
    "coap_best": (
        1  # Ver + T + TKL
        + 1  # Code
        + 2  # MID
        + 1  # Token
        + 1  # End of options marker
        + 1  # OSCORE option header
    ),
    "coap_exp": (
        1  # Ver + T + TKL
        + 1  # Code
        + 2  # MID
        + 2  # Token
        + 1  # OSCORE option
        + 1  # End of options marker
    ),
}
COAP_REQUEST_INNER_HDRS = {
    "coap_worst": (
        1  # Code
        + 4  # URI-Path option for /dns
        + 3  # Content-Format option with 2 bytes C-F ID
        + 3  # Accept option with 2 bytes C-F ID
        + 1  # End of options marker
    ),
    "coap_best": (
        1  # Code
        + 1  # URI-Path option for /d
        + 2  # Content-Format option with 1 byte C-F ID
        + 1  # End of options marker
    ),
    "coap_exp": (
        1  # Code
        + 4  # URI-Path option for /dns
        + 3  # Content-Format option with 2 bytes C-F ID
        + 3  # Accept option with 2 bytes C-F ID
        + 1  # End of options marker
    ),
}
COAP_RESPONSE_INNER_HDRS = {
    "coap_worst": (
        1  # Code
        + 3  # Content-Format option with 2 bytes C-F ID
        + 1  # End of options marker
    ),
    "coap_best": (
        1  # Code
        + 2  # Content-Format option with 1 byte C-F ID
        + 1  # End of options marker
    ),
    "coap_exp": (
        1  # Code
        + 3  # Content-Format option with 2 bytes C-F ID
        + 1  # End of options marker
    ),
}
DNS_QUERY_BASE = (
    12  # Static fields (TID, Flags, Section Counts)
    + 2  # Name 2 marker bytes
    + 2  # Type
    + 2  # Class
)
DNS_RESPONSE_AAAA_BASE = (
    12  # Static fields (TID, Flags, Section Counts)
    + 2  # Name compressed
    + 2  # Type
    + 2  # Class
    + 4  # TTL
    + 2  # Data length
    + 16  # IPv6 address
)

SIXLOWPAN_FRAG1_HDR = 4
SIXLOWPAN_FRAGN_HDR = 5
OSCORE_CCM8 = 8  # maybe even 16 for worst?
SCENARIOS_LOWER = [
    "802154_worst",
    "802154_best",
    "802154_best_sec",
    "802154_riot",
    "802154_riot_sec",
]
SCENARIOS_COAP = [
    "coap_worst",
    "coap_best",
    "coap_exp",
]
SCENARIOS_DNS = [
    "dns_min",
    "dns_median",
    "dns_mean",
    "dns_max",
]
SCENARIOS_LOWER_FRAGY = {
    "802154_worst": [127, 254, 381],
    "802154_best": [127, 254, 381],
    "802154_best_sec": [127, 254, 381],
    "802154_riot": [127, 254, 381],
    "802154_riot_sec": [127, 254, 381],
}
SCENARIOS_LOWER_READABLE = {
    "802154_worst": "IEEE 802.15.4+6LoWPAN worst header",
    "802154_best": "IEEE 802.15.4+6LoWPAN best header (w/o L2 security)",
    "802154_best_sec": "IEEE 802.15.4+6LoWPAN best header (w/ L2 security, 16-bit key)",
    "802154_riot": "IEEE 802.15.4+6LoWPAN RIOT-most (w/o L2 security)",
    "802154_riot_sec": "IEEE 802.15.4+6LoWPAN RIOT-most (w/ L2 security)",
}
SCENARIOS_COAP_READABLE = {
    "coap_worst": "CoAP ``worst'' header (URI-Path ``/dns'')",
    "coap_best": "CoAP ``best'' header (URI-Path ``/d'')",
    "coap_exp": "CoAP with OSCORE, Content-Format and URI-Path ``/dns''",
}


def get_lower_hdr_size(scenario_lower):
    return IEEE802154_HDRS.get(scenario_lower, 0) + SIXLOWPAN_HDRS.get(
        scenario_lower, 0
    )


def get_coap_outer_hdr_size(scenario_coap, msg_type):
    if msg_type == "query":
        return COAP_REQUEST_OUTER_HDRS.get(scenario_coap, 0)
    elif msg_type.startswith("response_"):
        return COAP_RESPONSE_OUTER_HDRS.get(scenario_coap, 0)
    else:
        assert False, f"'coap' not defined for {msg_type}"


def get_oscore_hdr_size(scenario_coap, msg_type):
    if msg_type:
        return OSCORE_CCM8
    else:
        assert False, f"'oscore' not defined for {msg_type}"


def get_coap_inner_hdr_size(scenario_coap, msg_type):
    if msg_type == "query":
        return COAP_REQUEST_INNER_HDRS.get(scenario_coap, 0)
    elif msg_type.startswith("response_"):
        return COAP_RESPONSE_INNER_HDRS.get(scenario_coap, 0)
    else:
        assert False, f"'coap_inner' not defined for {msg_type}"


def get_dns_size(name_lens, scenario_dns, msg_type):
    if msg_type == "query":
        return DNS_QUERY_BASE + name_lens.get(scenario_dns, 0)
    elif msg_type.startswith("response_"):
        return DNS_RESPONSE_AAAA_BASE + name_lens.get(scenario_dns, 0)
    else:
        assert False, f"'dns' not defined for {msg_type}"


class DNSNameLengths:
    _KEY_MAPPING = {
        "dns_min": "min",
        "dns_max": "max",
        "dns_mean": "μ",
        "dns_median": "Q2",
    }

    def __init__(self, csvfile):
        self._csvfile = csvfile
        self._stats = None

    @property
    def csvfile(self):
        return self._csvfile

    @csvfile.setter
    def csvfile(self, csvfile):
        self._csvfile = csvfile
        self._stats = None

    def __getitem__(self, stat):
        if self._stats is None:
            self._read_csv()
        return self._stats[stat]

    def get(self, stat, *args, **kwargs):
        if self._stats is None:
            self._read_csv()
        return self._stats.get(stat, *args, **kwargs)

    def _read_csv(self):
        with open(self._csvfile) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if (
                    row["data_src"] == "iotfinder+yourthings+moniotr"
                    and row["filter"] == "qd_only"
                ):
                    self._stats = {
                        k: float(row[self._KEY_MAPPING[k]]) for k in self._KEY_MAPPING
                    }
                    break
            assert (
                self._stats is not None
            ), f"Did not find data_src iotfinder+yourthings+monitor in {self._csvfile}"


def get_frag_size(scenario_lower, lower_size, frag_num, fragy, last_frag_size):
    if scenario_lower.startswith("802154"):
        mhdr = IEEE802154_HDRS.get(scenario_lower)
        if frag_num == 0:
            if lower_size > fragy:
                not_div8 = (fragy - mhdr - SIXLOWPAN_FRAG1_HDR) % 8
                res = fragy - ((8 - not_div8) if not_div8 else 0)
                return (
                    res,
                    res - mhdr - SIXLOWPAN_FRAG1_HDR - SIXLOWPAN_HDRS[scenario_lower],
                )
            return (
                lower_size,
                lower_size - mhdr - SIXLOWPAN_HDRS[scenario_lower],
            )
        if lower_size + SIXLOWPAN_FRAGN_HDR + mhdr > fragy:
            not_div8 = (fragy - mhdr - SIXLOWPAN_FRAGN_HDR) % 8
            res = fragy - ((8 - not_div8) if not_div8 else 0)
            return res, res - mhdr - SIXLOWPAN_FRAGN_HDR
        return (
            lower_size + SIXLOWPAN_FRAGN_HDR + mhdr,
            lower_size,
        )
    assert False, f"Do not know how to handle fragmentation for {scenario_lower}"


def get_pkt_sizes(
    scenario_lower,
    fragys,
    lower_hdr_size,
    coap_outer_hdr_size,
    oscore_hdr_size,
    coap_inner_hdr_size,
    dns_size,
):
    hdr_sizes = {"coap": 0}
    hdr_sizes["oscore"] = hdr_sizes["coap"] + coap_outer_hdr_size
    hdr_sizes["coap_inner"] = hdr_sizes["oscore"] + oscore_hdr_size
    hdr_sizes["dns"] = hdr_sizes["coap_inner"] + coap_inner_hdr_size
    current_size = (
        dns_size
        + coap_inner_hdr_size
        + oscore_hdr_size
        + coap_outer_hdr_size
        + lower_hdr_size
    )
    last_frag_size = 0
    last_fragy = 0
    res = {k: [] for k in hdr_sizes}
    res["lower"] = []
    for frag_num, fragy in enumerate(fragys):
        frag_size, inner_frag_size = get_frag_size(
            scenario_lower, current_size, frag_num, fragy - last_fragy, last_frag_size
        )
        for layer in pkt_sizes.LAYERS:
            if layer not in res:
                continue
            if layer == "lower":
                res[layer].append(frag_size)
            else:
                layer_frag_size = inner_frag_size - hdr_sizes[layer]
                if layer_frag_size <= 0:
                    res[layer].append(0)
                else:
                    res[layer].append(layer_frag_size)
        for layer in hdr_sizes:
            hdr_sizes[layer] -= inner_frag_size
            if hdr_sizes[layer] < 0:
                hdr_sizes[layer] = 0
        if frag_num == 0:
            if frag_size == current_size:
                current_size -= frag_size
            elif scenario_lower.startswith("802154"):
                current_size -= frag_size - SIXLOWPAN_FRAG1_HDR
            else:
                assert (
                    frag_size == current_size
                ), f"Unexpected scenario {scenario_lower}"
        else:
            current_size -= inner_frag_size
        if current_size <= 0:
            break
        last_frag_size = frag_size
        last_fragy = fragy
    return res


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--style-file", default="mlenders_acm.mplstyle")
    parser.add_argument(
        "stat_file",
        nargs="?",
        default=os.path.join(pc.DATA_PATH, "iot-data-name-lens-stats.csv"),
    )
    args = parser.parse_args()
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, args.style_file))
    pkt_sizes.FRAG_MARKER_STYLE.update({"linewidth": 1.5})
    pkt_sizes.PLOT_LAYERS = True
    dns_name_lens = DNSNameLengths(args.stat_file)
    scenarios_dns_readable = {}
    MATH_MAPPING = {
        "dns_min": "min",
        "dns_max": "max",
        "dns_mean": r"mean",
        "dns_median": "median",
    }
    for scenario_dns in SCENARIOS_DNS:
        scenarios_dns_readable[scenario_dns] = (
            "\\textbf{{Name length = "
            + (
                f"{dns_name_lens[scenario_dns]:.01f}"
                if (dns_name_lens[scenario_dns] != int(dns_name_lens[scenario_dns]))
                else f"{int(dns_name_lens[scenario_dns])}"
            )
            + f" chars}}\n({MATH_MAPPING[scenario_dns]})"
        )
    rows = len(SCENARIOS_LOWER) * len(SCENARIOS_COAP)
    cols = len(SCENARIOS_DNS)
    matplotlib.rcParams["figure.figsize"] = (
        cols * matplotlib.rcParams["figure.figsize"][0] * 0.85,
        rows * matplotlib.rcParams["figure.figsize"][1] * 1.2,
    )
    figure = matplotlib.pyplot.gcf()
    subfigs = figure.subfigures(
        rows,
        1,
    )
    ridx = 0
    hypo_pkt_sizes = {}
    for scenario_lower in SCENARIOS_LOWER:
        lower_hdr_size = get_lower_hdr_size(scenario_lower)
        fragys = SCENARIOS_LOWER_FRAGY.get(scenario_lower, float("inf"))
        for msg_type in MSG_TYPES:
            for scenario_coap in SCENARIOS_COAP:
                coap_outer_hdr_size = get_coap_outer_hdr_size(scenario_coap, msg_type)
                oscore_hdr_size = get_oscore_hdr_size(scenario_coap, msg_type)
                coap_inner_hdr_size = get_coap_inner_hdr_size(scenario_coap, msg_type)
                for scenario_dns in SCENARIOS_DNS:
                    dns_size = get_dns_size(dns_name_lens, scenario_dns, msg_type)
                    scenario = f"{scenario_lower}_{scenario_coap}_{scenario_dns}"
                    hypo_pkt_sizes[scenario] = hypo_pkt_sizes.get(scenario, {})
                    hypo_pkt_sizes[scenario][msg_type] = get_pkt_sizes(
                        scenario_lower,
                        fragys,
                        lower_hdr_size,
                        coap_outer_hdr_size,
                        oscore_hdr_size,
                        coap_inner_hdr_size,
                        dns_size,
                    )
    for scenario_lower in SCENARIOS_LOWER:
        fragys = SCENARIOS_LOWER_FRAGY.get(scenario_lower, [float("inf")])
        for scenario_coap in SCENARIOS_COAP:
            subfigs[ridx].suptitle(
                f"{SCENARIOS_LOWER_READABLE[scenario_lower]}\n"
                f"{SCENARIOS_COAP_READABLE[scenario_coap]}",
                y=0.90,
                fontsize="large",
            )
            axs = subfigs[ridx].subplots(nrows=1, ncols=cols, sharex=True, sharey=True)
            scenarios = [
                f"{scenario_lower}_{scenario_coap}_{scenario_dns}"
                for scenario_dns in SCENARIOS_DNS
            ]
            pkt_sizes.plot_pkt_sizes_for_transports(
                axs,
                transports=scenarios,
                transport_figure={s: i for i, s in enumerate(scenarios)},
                transport_readable=None,
                pkt_sizes=hypo_pkt_sizes,
                fragys=fragys,
                set_xlabels=(ridx + 1) == rows,
                xhorizontalalignment="center",
                xrotation=None,
                ymax=360,
            )
            if ridx == 0:
                for cidx, scenario_dns in enumerate(SCENARIOS_DNS):
                    axs[cidx].set_title(
                        scenarios_dns_readable[scenario_dns],
                        y=1.4,
                        fontsize="x-large",
                    )
            ridx += 1
    pkt_sizes.add_legends(
        figure, layers=["lower", "coap", "oscore", "dns"], legend_pad=0.04
    )
    matplotlib.pyplot.tight_layout(w_pad=0)
    matplotlib.pyplot.subplots_adjust(top=0.7, bottom=0)
    for ext in pc.OUTPUT_FORMATS:
        matplotlib.pyplot.savefig(
            os.path.join(
                pc.DATA_PATH,
                f"doc-eval-pkt-size-hypothetical-l2-best.{ext}",
            ),
            bbox_inches="tight",
            pad_inches=0.01,
        )


if __name__ == "__main__":
    main()
