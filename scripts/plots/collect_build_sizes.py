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

import ast
import json
import os
import logging
import subprocess
import sys

import riotctrl.ctrl

try:
    from . import plot_common as pc
except ImportError:
    import plot_common as pc

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


REQUESTER_PATH = os.path.join(pc.SCRIPT_PATH, "..", "..", "apps", "requester")


def cosy(transport, with_get=False):
    env = {
        "ASYNC": "0",
        "DNS_TRANSPORT": transport,
        "COSY_NO_WEBSERVER": "1",
        "ONLY_FETCH": str(int(not with_get)),
        "QUIETER": "1",
    }
    cosy_syms = []
    ctrl = riotctrl.ctrl.RIOTCtrl(REQUESTER_PATH, env=env)
    ctrl.MAKE_ARGS = ("-j",)
    try:
        ctrl_out = ctrl.make_run(
            ["clean", "all", "cosy"], stdout=subprocess.PIPE, check=True
        ).stdout
    except subprocess.CalledProcessError as e:
        logging.error(e)
        return []
    for line in ctrl_out.splitlines():
        try:
            # single quotes are not JSON, so parse as Python dicts
            sym = ast.literal_eval(line.decode())
        except (SyntaxError, ValueError):
            continue
        if not isinstance(sym, dict) or any(
            key not in sym for key in ["obj", "size", "sym", "type"]
        ):
            continue
        cosy_syms.append(sym)
    return cosy_syms


def filename(transport, with_get=False):
    return os.path.join(
        pc.DATA_PATH,
        f"doc-eval-build-sizes-{transport}%s.json"
        % (f"-get{with_get:d}" if transport in pc.COAP_TRANSPORTS else ""),
    )


def write_json(json_filename, cosy_syms):
    with open(json_filename, "w") as json_file:
        json.dump(cosy_syms, json_file, indent=1)


def read_json(json_filename):
    with open(json_filename) as json_file:
        return json.load(json_file)


def get_syms(transport, with_get=False):
    res = cosy(transport, with_get)
    write_json(filename(transport, with_get), res)
    return res


def main():
    for transport in pc.TRANSPORTS:
        for with_get in [False, True]:
            if transport not in pc.COAP_TRANSPORTS and with_get:
                continue
            get_syms(transport, with_get)
            print(".", end="")
            sys.stdout.flush()
    print("")


if __name__ == "__main__":
    main()
