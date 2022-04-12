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

import os
import pprint

import matplotlib.pyplot
import numpy

try:
    from . import plot_common as pc
    from . import collect_build_sizes
except ImportError:
    import plot_common as pc
    import collect_build_sizes

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"

MODULES = [
    "dtls",
    "sock",
    "coap",
    "oscore",
    "dns",
    "app",
    "dns_get",
]
MODULE_MAPPING = {
    "dtls": {
        "ccm.o": None,
        "crypto.o": None,
        "dtls.o": None,
        "dtls_debug.o": None,
        "dtls_prng.o": None,
        "dtls_time.o": None,
        "ecc.o": None,
        "hmac.o": None,
        "netq.o": None,
        "peer.o": None,
        "rijndael.o": None,
        "rijndael_wrap.o": None,
        "session.o": None,
    },
    "sock": {
        "credman.o": None,
        "gnrc_sock.o": None,
        "gnrc_sock_udp.o": None,
        "sock_async_event.o": None,
        "sock_dtls.o": None,
    },
    "coap": {
        "dsm.o": None,
        "gcoap.o": None,
        "nanocoap.o": None,
    },
    "oscore": {
        "AEAD_Poly1305_64.o": None,
        "aes_decrypt.o": None,
        "aes_encrypt.o": None,
        "cbc_mode.o": None,
        "ccm_mode.o": None,
        "cmac_mode.o": None,
        "context_b1.o": None,
        "contextpair.o": None,
        "context_primitive.o": None,
        "cose_common.o": None,
        "cose_crypto.o": None,
        "cose_encrypt.o": None,
        "cose_hdr.o": None,
        "cose_key.o": None,
        "cose_recipient.o": None,
        "cose_signature.o": None,
        "cose_sign.o": None,
        "ctr_mode.o": None,
        "ctr_prng.o": None,
        "ecc_dh.o": None,
        "ecc_dsa.o": None,
        "ecc.o": None,
        "FStar.o": None,
        "Hacl_Chacha20.o": None,
        "Hacl_Chacha20Poly1305.o": None,
        "Hacl_Curve25519.o": None,
        "Hacl_Ed25519.o": None,
        "Hacl_HMAC_SHA2_256.o": None,
        "haclnacl.o": None,
        "hacl.o": None,
        "Hacl_Policies.o": None,
        "Hacl_Poly1305_32.o": None,
        "Hacl_Poly1305_64.o": None,
        "Hacl_Salsa20.o": None,
        "Hacl_SHA2_256.o": None,
        "Hacl_SHA2_384.o": None,
        "Hacl_SHA2_512.o": None,
        "hkdf.o": None,
        "hmac.o": None,
        "hmac_prng.o": None,
        "kremlib.o": None,
        "libcose.o": None,
        "NaCl.o": None,
        "oscore_message.o": None,
        "oscore_msg_native.o": None,
        "oscore_test.o": None,
        "protection.o": None,
        "sha256.o": None,
        "tinycrypt.o": None,
        "utils.o": None,
    },
    "dns": {
        "base64.o": None,
        "dns.o": None,
        "msg.o": {  # dns_msg mixed with core_msg here so hand-pick functions
            "dns_msg_parse_reply",
            "dns_msg_compose_query",
            "_enc_domain_name",
            "_skip_hostname",
        },
        "sock_dodtls.o": None,
        "uri_parser.o": None,
        "ut_process.o": None,
    },
    "app": {
        "main.o": None,  # None == take all
    },
}
MODULE_READABLE = {
    "app": "Application",
    "dns": "DNS (w/o GET)",
    "dns_get": "DNS (GET)",
    "oscore": "OSCORE",
    "coap": "CoAP",
    "sock": "sock",
    "dtls": "DTLS",
}
MODULE_STYLE = {
    "app": {"color": "C4"},
    "dns": {"color": "C0", "hatch": "////"},
    "dns_get": {"color": "C0"},
    "oscore": {"color": "C3", "hatch": "////"},
    "coap": {"color": "C2"},
    "sock": {"color": "C1"},
    "dtls": {"color": "C3"},
}
MEMS = ["ROM", "RAM"]


def sum_syms(transport, syms):
    res = {mem: {mod: 0 for mod in MODULES} for mem in MEMS}
    for module in MODULES:
        for sym in syms:
            # hmac.o appears in both libOSCORE and TinyDTLS.
            # Ignore the respective other.
            if module == "oscore" and transport != "oscore":
                continue
            if module == "dtls" and transport not in ["dtls", "coaps"]:
                continue
            if module not in MODULE_MAPPING:
                continue
            if sym["obj"] in MODULE_MAPPING[module]:
                obj = MODULE_MAPPING[module][sym["obj"]]
                if obj is not None and sym["sym"] not in obj:
                    # ignore any symbol not listed in the dict
                    continue
                if sym["type"] in ["t", "d"]:
                    res["ROM"][module] += sym["size"]
                if sym["type"] in ["d", "b"]:
                    res["RAM"][module] += sym["size"]
    return res


def plot(sums):
    fig, axs = matplotlib.pyplot.subplots(1, 2, sharey=True)
    transports = numpy.array(
        [str(pc.TRANSPORTS_READABLE[t]) for t in reversed(pc.TRANSPORTS)]
    )
    for i, mem in enumerate(MEMS):
        bottom = None
        for mod in MODULES:
            sizes = (
                numpy.array([sums[i][mem][mod] for i, _ in enumerate(transports)])
                / 1024
            )
            axs[i].bar(
                numpy.arange(len(pc.TRANSPORTS)),
                sizes,
                bottom=0 if bottom is None else bottom,
                label=MODULE_READABLE[mod],
                alpha=0.99,  # show hatches, see https://stackoverflow.com/a/59389823
                **MODULE_STYLE[mod],
            )
            if bottom is None:
                bottom = sizes
            else:
                bottom += sizes
        axs[i].set_xticks(numpy.arange(len(pc.TRANSPORTS)))
        axs[i].set_xticklabels(
            labels=transports,
            rotation=45,
            rotation_mode="anchor",
            horizontalalignment="right",
            verticalalignment="top",
        )
        axs[i].set_ylim((0, 60))
        axs[i].set_yticks(numpy.arange(0, 61, step=10))
        axs[i].grid(True, axis="y")
        axs[i].set_title(MEMS[i])
        if mem == "RAM":
            axs[i].legend()
        else:
            axs[i].set_ylabel("Build size [kBytes]")
    matplotlib.pyplot.tight_layout()
    for ext in pc.OUTPUT_FORMATS:
        matplotlib.pyplot.savefig(
            os.path.join(
                pc.DATA_PATH,
                f"doc-eval-build_sizes.{ext}",
            ),
            bbox_inches="tight",
            pad_inches=0.01,
        )


def main():
    matplotlib.style.use(os.path.join(pc.SCRIPT_PATH, "mlenders_usenix.mplstyle"))
    matplotlib.rcParams["figure.figsize"] = (
        matplotlib.rcParams["figure.figsize"][0],
        matplotlib.rcParams["figure.figsize"][1] * 1.42,
    )
    matplotlib.rcParams["hatch.color"] = "white"
    matplotlib.rcParams["hatch.linewidth"] = 2
    matplotlib.rcParams["legend.handletextpad"] = 0.2
    matplotlib.rcParams["legend.fontsize"] = "xx-small"
    matplotlib.rcParams["patch.linewidth"] = 0.5
    sums = []
    for transport in reversed(pc.TRANSPORTS):
        tsums = {}
        for with_get in [False, True]:
            if (
                transport not in pc.COAP_TRANSPORTS or transport == "oscore"
            ) and with_get:
                continue
            json_filename = collect_build_sizes.filename(transport, with_get)
            if os.path.exists(json_filename):
                syms = collect_build_sizes.read_json(json_filename)
            else:
                syms = collect_build_sizes.get_syms(transport, with_get)
            tsums[with_get] = sum_syms(transport, syms)
        if True in tsums:
            for mem in MEMS:
                dns_get = sum(tsums[True][mem].values()) - sum(
                    tsums[False][mem].values()
                )
                if dns_get:
                    tsums[False][mem]["dns_get"] = dns_get
        tsums = tsums[False]
        sums.append(tsums)
    pprint.pprint(sums)
    plot(sums)


if __name__ == "__main__":
    main()
