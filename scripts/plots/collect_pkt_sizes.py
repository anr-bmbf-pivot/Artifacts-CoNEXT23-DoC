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
import base64
import copy
import json
import os
import pprint
import re
import subprocess

from scapy.all import rdpcap as scapy_rdpcap, conf as scapy_conf, load_contrib, DNS


try:
    from . import plot_common as pc
except ImportError:
    import plot_common as pc

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


PCAP_PATTERN = r"{}.pcap(.gz|ng)?".format(
    pc.FILENAME_PATTERN_FMT.format(
        exp_type=r"(load|proxy)",
        link_layer=r"(ble|ieee802154)",
        transport=r"(?P<transport>coaps?|dtls|udp|oscore)",
        method=r"(fetch|get|post)",
        blocksize=r"(\d+|None)",
        proxied=r"(0|1)",
        delay_time=r"(\d+\.\d+|None)",
        delay_queries=r"(\d+|None)",
        queries=r"\d+",
        record=r"A{1,4}",
        avg_queries_per_sec=r"\d+.\d+",
    )
)
TSHARK_BIN = os.environ.get("TSHARK_BIN", "tshark")


class PacketList:
    def __init__(self, pcap_file, device_id=None):
        self._pcap_file = pcap_file
        self._device_id = device_id
        self._tshark_data = None
        self._scapy_data = None

    @property
    def device_id(self):
        return self._device_id

    @property
    def pcap_file(self):
        return self.pcap_file

    @property
    def scapy_data(self):
        return self._get_scapy_data()

    @property
    def tshark_data(self):
        return self._get_dns_tshark_data()

    def __len__(self):
        return len(self.tshark_data)

    def _tshark_frame_to_pkt(self, tshark_frame):
        frame = tshark_frame["_source"]["layers"]
        frame_num = int(frame["frame"]["frame.number"])
        return _Packet(self, frame, frame_num)

    def __getitem__(self, idx):
        return self._tshark_frame_to_pkt(self.tshark_data[idx])

    def __iter__(self):
        for frame in self.tshark_data:
            yield self._tshark_frame_to_pkt(frame)

    def frame(self, frame_num):
        for frame in self.tshark_data:
            frame = frame["_source"]["layers"]
            if int(frame["frame"]["frame.number"]) == frame_num:
                return _Packet(self, frame, frame_num)
        raise ValueError(f"No frame with number {frame_num} in Tshark data")

    def _get_dns_tshark_data(self):
        if self._tshark_data is None:
            q = (
                # catch identified application traffic
                "dns || coap || dtls || "
                # and fragments
                "6lowpan.frag.tag"
            )
            if self._device_id is not None:
                q = f"zep.device_id == {self._device_id} && ({q})"
            output = subprocess.check_output(
                [TSHARK_BIN, "-r", self._pcap_file, "-Tjson", "-q", q]
            )
            self._tshark_data = json.loads(
                output, object_pairs_hook=self._strip_zep_headers_from_json
            )
        return self._tshark_data

    def _get_scapy_data(self):
        if self._scapy_data is None:
            scapy_conf.dot15d4_protocol = "sixlowpan"
            self._scapy_data = scapy_rdpcap(self._pcap_file)
        return self._scapy_data

    @staticmethod
    def _strip_zep_headers_from_json(ordered_pairs):
        d = {}
        key_count = {}
        outer_udp = True
        frame_len = None
        for k, v in ordered_pairs:
            if (k in ["eth", "ip", "ipv6", "udp"] and outer_udp) or k in ["zep"]:
                if k == "zep":
                    frame_len = v["zep.length"]
                if k == "udp":
                    outer_udp = False
                continue
            if k in d:
                if k not in key_count:
                    key_count[k] = 1
                else:
                    key_count[k] += 1
                d[f"{k}[{key_count[k]}]"] = v
            else:
                d[k] = v
        if "frame" in d:
            d["frame"]["frame.encap_type"] = "104"
            d["frame"]["frame.cap_len"] = frame_len
            d["frame"]["frame.len"] = frame_len
            d["frame"]["frame.protocols"] = d["frame"]["frame.protocols"].replace(
                "eth:ethertype:ip:udp:zep:", ""
            )
        for k in key_count:
            v = d.pop(k)
            d[f"{k}[0]"] = v
        return d


class _Packet:
    def __init__(self, packet_list, frame, frame_num):
        self._packet_list = packet_list
        self._frame = frame
        self._frame_num = frame_num
        self._layers = None
        self._scapyfied = None
        self._wpan_hdr_len = None
        self._6lowpan_hdr_len = None
        self._coap_hdr_len = None
        self._oscore_hdr_len = None
        self._dns_len = None

    def __eq__(self, other):
        return self._frame_num == other._frame_num

    def __str__(self):
        return pprint.pformat(self._frame, sort_dicts=False)

    def __repr__(self):
        return str(self)

    def __getitem__(self, key):
        return self._frame[key]

    def __contains__(self, key):
        return key in self._frame

    def __iter__(self):
        assert "frame" in self._frame
        for k, v in sorted(
            self._frame.items(),
            key=lambda l: self.layers.index(l[0]),
        ):
            yield k, v

    @property
    def frame_num(self):
        return self._frame_num

    @property
    def scapyfied(self):
        if self._scapyfied is None:
            self._scapyfied = self._packet_list.scapy_data[self._frame_num - 1]
        return self._scapyfied

    @property
    def layers(self):
        if self._layers is None:

            def _layer_sort_key(layer):
                try:
                    return self._frame["frame"]["frame.protocols"].index(layer[0])
                except ValueError:
                    return -1

            self._layers = sorted(self._frame.keys(), key=_layer_sort_key)
        return self._layers

    def get(self, key, default=None):
        return self._frame.get(key, default)

    def is_prot(self):
        return any(k in self._frame for k in ["dns", "coap", "dtls"])

    def is_fragment(self):
        return (
            "6lowpan" in self._frame
            and "Fragmentation Header" in self._frame["6lowpan"]
        )

    def _tshark_fragments_to_fragment_list(self, pkt):
        fragments = pkt["6lowpan"]["6lowpan.fragments"]
        fragment_dict = {
            k: int(v) for k, v in fragments.items() if k.startswith("6lowpan.fragment[")
        }
        try:
            return [
                self._packet_list.frame(fragment_dict[f"6lowpan.fragment[{i}]"])
                for i in range(len(fragment_dict))
            ]
        except ValueError:
            return []

    def get_6lowpan_fragments(self):
        if not self.is_fragment():
            return []
        sixlo = self._frame["6lowpan"]
        if "6lowpan.fragments" in sixlo:
            return self._tshark_fragments_to_fragment_list(self)
        for pkt in self._packet_list:
            if "6lowpan" not in pkt or "6lowpan.fragments" not in pkt["6lowpan"]:
                continue
            res = self._tshark_fragments_to_fragment_list(pkt)
            if any(v == self for v in res):
                return res
        return []

    def get_wpan_hdr_len(self):
        if self._wpan_hdr_len is None:
            wpan_layers = [
                layer.__name__
                for layer in self.scapyfied.layers()
                if layer.__module__.endswith("dot15d4")
            ]
            if not wpan_layers:
                return None
            scapyfied = copy.deepcopy(self.scapyfied)
            scapyfied[wpan_layers[-1]].remove_payload()
            self._wpan_hdr_len = len(scapyfied[wpan_layers[0]])
        return self._wpan_hdr_len

    def get_wpan_payload_len(self):
        return self.get_wpan_len() - self.get_wpan_hdr_len() - 2

    def get_wpan_len(self):
        return int(self._frame["frame"]["frame.len"])

    def get_6lowpan_hdr_len(self):
        if self._6lowpan_hdr_len is None:
            sixlo_layers = [
                layer.__name__
                for layer in self.scapyfied.layers()
                if layer.__module__.endswith("sixlowpan")
            ]
            if not sixlo_layers:
                return None
            scapyfied = copy.deepcopy(self.scapyfied)
            scapyfied[sixlo_layers[-1]].remove_payload()
            self._6lowpan_hdr_len = len(scapyfied[sixlo_layers[0]])
        return self._6lowpan_hdr_len

    def get_6lowpan_payload_len(self):
        return self.get_wpan_payload_len() - self.get_6lowpan_hdr_len()

    def get_6lowpan_len(self):
        return self.get_6lowpan_hdr_len() + self.get_6lowpan_payload_len()

    def get_dtls_hdr_len(self):
        if "dtls" not in self._frame:
            return None
        return int(self._frame["udp"]["udp.length"]) - 8 - self.get_dtls_payload_len()

    def get_dtls_payload_len(self):
        if "dtls" not in self._frame:
            return None
        if self._frame["dtls"]["dtls.record"]["dtls.record.content_type"] == "23":
            return int(self._frame["dtls"]["dtls.record"]["dtls.record.length"])
        return 0

    def get_dtls_len(self):
        if "dtls" not in self._frame:
            return None
        return self.get_dtls_hdr_len() + self.get_dtls_payload_len()

    def get_coap_hdr_len(self):
        if "coap" not in self._frame:
            return None
        if self._coap_hdr_len is None:
            coap_hdr = self._frame["coap"]
            assert coap_hdr["coap.version"] == "1", "Unsupported CoAP version"
            coap_hdr_len = 4
            coap_hdr_len += len(coap_hdr["coap.token_len"])
            if "coap.opt.end_marker" in coap_hdr:
                coap_hdr_len += 1
            opts = [
                v for k, v in coap_hdr.items() if k.startswith("coap.opt.name_tree[")
            ]
            for opt in opts:
                # TODO account for compression algorithm
                coap_hdr_len += int(opt["coap.opt.length"]) + 1
            self._coap_hdr_len = coap_hdr_len
        return self._coap_hdr_len

    def get_coap_payload_len(self):
        if "coap" not in self._frame:
            return None
        coap_hdr = self._frame["coap"]
        if "coap.payload_tree" not in coap_hdr:
            return 0
        return int(coap_hdr["coap.payload_tree"]["coap.payload_length"])

    def get_coap_len(self):
        if "coap" not in self._frame:
            return None
        return self.get_coap_hdr_len() + self.get_coap_payload_len()

    def get_oscore_hdr_len(self):
        if "oscore" not in self._frame:
            return None
        if self._oscore_hdr_len is None:
            oscore_hdr = self._frame["oscore"]
            oscore_hdr_len = 1
            if "oscore.opt.end_marker" in oscore_hdr:
                oscore_hdr_len += 1
            opts = [
                v
                for k, v in oscore_hdr.items()
                if k.startswith("oscore.opt.name_tree[")
            ]
            for opt in opts:
                # TODO account for compression algorithm
                oscore_hdr_len += int(opt["oscore.opt.length"]) + 1
            self._oscore_hdr_len = oscore_hdr_len
        return self._oscore_hdr_len

    def get_oscore_payload_len(self):
        if "oscore" not in self._frame:
            return None
        oscore_hdr = self._frame["oscore"]
        if "oscore.payload_tree" not in oscore_hdr:
            return 0
        return int(oscore_hdr["oscore.payload_tree"]["oscore.payload_length"])

    def get_oscore_len(self):
        if "oscore" not in self._frame:
            return None
        return self.get_oscore_hdr_len() + self.get_oscore_payload_len()

    def get_dns_len(self):
        if "dns" not in self._frame:
            return None
        if self._dns_len is None:
            dns = self._frame["dns"]
            assert (
                dns["dns.count.auth_rr"] == "0" and dns["dns.count.add_rr"] == "0"
            ), "Unsupported sections have content"
            dns_len = 12
            for qry in dns.get("Queries", {}).values():
                dns_len += 4
                dns_len += int(qry["dns.qry.name.len"]) + 2
            for resp in dns.get("Answers", {}).values():
                assert "Queries" in dns, (
                    "Need to assume name compression as tshark does not show "
                    "if name is compressed or its structure as in dns.qry"
                )
                dns_len += 12
                dns_len += int(resp["dns.resp.len"])
            self._dns_len = dns_len
        return self._dns_len

    def _classify_dns(self):
        dns = self._frame["dns"]
        if "Answers" in dns:
            answers = dns["Answers"]
            if len(answers) == 1:
                answer = list(answers.values())[0]
                if (
                    int(answer["dns.resp.type"]) == 1
                    and int(answer["dns.resp.class"], base=16) == 1
                ):
                    return "response_a"
                elif (
                    int(answer["dns.resp.type"]) == 28
                    and int(answer["dns.resp.class"], base=16) == 1
                ):
                    return "response_aaaa"
        elif "Queries" in dns:
            return "query"
        return None

    def _classify_dtls(self):
        dtls = self._frame["dtls"]
        if len(dtls) == 1:
            record = dtls["dtls.record"]
            content_type = record["dtls.record.content_type"]
            if content_type == "20":
                return "dtls_change_cipher_spec"
            if content_type == "22":
                if "dtls.handshake" in record:
                    hs = record["dtls.handshake"]
                    hs_type = hs["dtls.handshake.type"]
                    if hs_type == "1":
                        if "dtls.handshake.cookie" in hs:
                            return "dtls_client_hello+cookie"
                        return "dtls_client_hello"
                    if hs_type == "2":
                        return "dtls_server_hello"
                    if hs_type == "3":
                        return "dtls_hello_verify_req"
                    if hs_type == "14":
                        return "dtls_server_hello_done"
                    if hs_type == "16":
                        return "dtls_client_key_exc"
                    if hs_type == "20":
                        return "dtls_finish"
        return None

    def _classify_coap(self):
        coap = self._frame["coap"]
        if coap["coap.code"] == "1":
            opts = [v for k, v in coap.items() if k.startswith("coap.opt.name_tree[")]
            for opt in opts:
                if "coap.opt.uri_query" in opt and "dns=" in opt["coap.opt.uri_query"]:
                    dns_query64 = opt["coap.opt.uri_query"][4:]
                    # python's base64 only understands encoding with padding, so
                    # add '=' padding if needed
                    dns_query = DNS(
                        base64.urlsafe_b64decode(
                            dns_query64 + "=" * (4 - len(dns_query64) % 4)
                        )
                    )
                    if (
                        dns_query.opcode == 0
                        and dns_query.qdcount == 1
                        and dns_query.ancount == 0
                        and dns_query.nscount == 0
                        and dns_query.arcount == 0
                    ):
                        return "query"
        return None

    def _classify_fragment(self):
        cls = None
        for frag in self.get_6lowpan_fragments():
            key = "Fragmentation Header"
            self_offset = self["6lowpan"][key].get("6lowpan.frag.offset", 0)
            frag_offset = frag["6lowpan"][key].get("6lowpan.frag.offset", 0)
            if self == frag or self_offset == frag_offset:
                continue
            frag_cls = frag.classify()
            if frag_cls is not None:
                if cls is None:
                    cls = frag_cls
                else:
                    # multiple potential classes, rather return none
                    return None
        return cls

    def classify(self):
        if "dns" in self._frame:
            res = self._classify_dns()
            if res:
                return res
        elif "oscore" in self._frame and self._frame["oscore"]["oscore.code"] == "129":
            return "oscore_unauth_response"
        elif "dtls" in self._frame:
            res = self._classify_dtls()
            if res:
                return res
        elif "coap" in self._frame:
            res = self._classify_coap()
            if res:
                return res
        elif "icmpv6" in self:
            return None
        elif self.is_fragment():
            return self._classify_fragment()
        return None


def valid_pcap_name(value, pat=re.compile(PCAP_PATTERN)):
    if not pat.search(value):
        raise argparse.ArgumentTypeError(
            "PCAP file {value} does not follow the expected naming scheme."
        )
    if not os.path.isfile(value):
        raise argparse.ArgumentTypeError(
            f"PCAP file {value} is not a file or does not exist."
        )
    return value


def iotlab_name_to_dev_id(iotlab_name):
    if iotlab_name.startswith("m3-"):
        try:
            return 0x3000 | int(iotlab_name[3:])
        except ValueError:
            pass
    raise argparse.ArgumentTypeError(
        f"Cannot convert IoT-LAB node name '{iotlab_name}' to ZEP device ID"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pcap", type=valid_pcap_name)
    parser.add_argument(
        "-n",
        "--node",
        help="IoT-LAB node to take PCAP data from",
        type=iotlab_name_to_dev_id,
        dest="device_id",
    )
    args = parser.parse_args()
    load_contrib("coap")
    pkts = PacketList(args.pcap, device_id=args.device_id)
    i, pkt = None, None
    for i, pkt in enumerate(pkts):
        print(pkt.frame_num, pkt.classify())


if __name__ == "__main__":
    main()
