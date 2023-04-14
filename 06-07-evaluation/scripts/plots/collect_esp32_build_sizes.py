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

import csv
import logging
import pathlib
import re
import subprocess

import riotctrl.ctrl

try:
    from . import plot_common as pc
except ImportError:  # pragma: no cover
    import plot_common as pc

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"

SCRIPT_PATH = pathlib.Path(pc.SCRIPT_PATH)
BASE_PATH = (SCRIPT_PATH / ".." / "..").resolve()
REQUESTER_PATH = BASE_PATH / "apps" / "requester"
RIOT_PATH = BASE_PATH / "RIOT"
QUANT_PATH = BASE_PATH / "quant"
QUANT_APP_PATH = QUANT_PATH / "riot"
QUANT_PATCH_PATH = BASE_PATH / "quant-patches"
QUANT_BASE_COMMIT = "d24351769f9001ac3d210b99a7136db1394ca516"
BOARD = "esp32-wroom-32"


def prepare_quant():
    picotls_path = QUANT_PATH / "lib" / "deps" / "picotls"
    warpcore_path = QUANT_PATH / "lib" / "deps" / "warpcore"
    subprocess.run(["git", "am", "--abort"], cwd=picotls_path, check=False)
    subprocess.run(["git", "am", "--abort"], cwd=warpcore_path, check=False)
    subprocess.run(["git", "am", "--abort"], cwd=QUANT_PATH, check=False)
    subprocess.check_call(["git", "reset", "--hard", QUANT_BASE_COMMIT], cwd=QUANT_PATH)
    subprocess.check_call(
        ["git", "submodule", "update", "--init", "--recursive"], cwd=QUANT_PATH
    )
    subprocess.check_call(
        f"git am {QUANT_PATCH_PATH / 'picotls' / '*.patch'}",
        cwd=picotls_path,
        shell=True,
    )
    subprocess.check_call(
        f"git am {QUANT_PATCH_PATH / 'warpcore' / '*.patch'}",
        cwd=warpcore_path,
        shell=True,
    )
    subprocess.check_call(
        f"git am {QUANT_PATCH_PATH / '*.patch'}",
        cwd=QUANT_PATH,
        shell=True,
    )
    build_dir = QUANT_PATH / "Debug"
    build_dir.mkdir(exist_ok=True)
    subprocess.check_call(["cmake", ".."], cwd=build_dir)


def build_app(app, transport=None):
    env = {
        "ASYNC": "0",
        "ONLY_FETCH": "1",
        "QUIETER": "1",
        "BOARD": BOARD,
    }
    if transport:
        env["DNS_TRANSPORT"] = transport
    if transport in ["coap", "coaps", "oscore"]:
        env.update(
            {
                "RIOT_CONFIG_KCONFIG_USEMODULE_GCOAP": "y",
                "RIOT_CONFIG_GCOAP_PDU_BUF_SIZE": "128",
            }
        )
    if app == QUANT_APP_PATH:
        env.update(
            {
                "RIOTBASE": RIOT_PATH,
                "WERROR": "0",
                "CFLAGS": "-DPTHREAD_MUTEX_INITIALIZER=MUTEX_INIT",
            }
        )
        try:
            prepare_quant()
        except subprocess.CalledProcessError:
            logging.exception("Unable to prepare quant")
            raise
    ctrl = riotctrl.ctrl.RIOTCtrl(app, env=env)
    ctrl.MAKE_ARGS = tuple()
    try:
        ctrl.make_run(["clean", "all"], check=True)
    except subprocess.CalledProcessError:
        logging.exception("Unable to build")
        raise


def filename(app, transport=None):
    app_name = "quant" if "quant" in str(app) else app.name
    transport = f"-{transport}" if transport else ""
    return (
        pathlib.Path(pc.DATA_PATH)
        / f"doc-eval-esp32-build-sizes-{app_name}{transport}.csv"
    )


def size(app, transport=None, bindir="bin"):
    command = ["nm", "-S", "--line-numbers"]
    proc_out = subprocess.check_output(
        command + list((app / bindir / BOARD).glob("*.elf"))
    )
    comp = re.compile(
        r"(?P<addr>[0-9a-f]+)\s+(?P<size>[0-9a-f]+)\s+"
        r"(?P<type>[bdtBDT])\s(?P<sym>[0-9a-zA-Z_$.]+)\s+"
        r"(?P<filename>.*):(?P<line>\d+)$"
    )
    TYPE_MAPPING = {
        "b": "bss",
        "d": "data",
        "t": "text",
    }
    with open(filename(app, transport), "w", encoding="utf-8") as out_csv:
        writer = csv.DictWriter(
            out_csv,
            fieldnames=["text", "data", "bss", "filename", "sym"],
        )
        writer.writeheader()
        for line in proc_out.decode("ascii").splitlines():
            match = comp.match(line)
            if not match:
                continue
            res = match.groupdict()
            try:
                res["filename"] = str(
                    pathlib.Path(res["filename"]).resolve().relative_to(BASE_PATH)
                )
            except ValueError:
                pass
            row = {
                "bss": 0,
                "text": 0,
                "data": 0,
                "filename": res["filename"],
                "sym": res["sym"],
            }
            row[TYPE_MAPPING[res["type"].lower()]] += int(res["size"], base=16)
            writer.writerow(row)


def main():
    build_app(QUANT_APP_PATH)
    size(QUANT_APP_PATH)

    for transport in pc.TRANSPORTS:
        build_app(REQUESTER_PATH, transport)
        size(REQUESTER_PATH, transport)


if __name__ == "__main__":
    main()  # pragma: no cover
