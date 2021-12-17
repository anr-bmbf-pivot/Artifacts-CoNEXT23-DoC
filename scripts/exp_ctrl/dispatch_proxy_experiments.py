#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright (C) 2021 Freie Universität Berlin
#
# Distributed under terms of the MIT license.

import argparse
import logging
import os
import sys
import tempfile

import coloredlogs
from iotlab_controller.experiment import ExperimentError

import riotctrl.ctrl
import riotctrl.shell

try:
    from . import dispatch_load_experiments as dle
except ImportError:
    import dispatch_load_experiments as dle

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))

sys.path.append(os.path.join(SCRIPT_PATH, "..", "..", "RIOT", "dist", "pythonlibs"))

# pylint: disable=wrong-import-position,import-error
import riotctrl_shell.netif  # noqa: E402

logger = logging.getLogger(__name__)


class Dispatcher(dle.Dispatcher):
    _RESOLVER_BIND_PORTS = {
        "udp": 5301,
        "dtls": 8531,
        "coap": 8483,
        "coaps": 8484,
        "oscore": 8483,
    }

    def __new__(cls, *args, **kwargs):
        cls = super().__new__(cls)
        cls._RESOLVER_CONFIG["transports"]["udp"]["port"] = cls._RESOLVER_BIND_PORTS[
            "udp"
        ]
        cls._RESOLVER_CONFIG["transports"]["dtls"]["port"] = cls._RESOLVER_BIND_PORTS[
            "dtls"
        ]
        cls._RESOLVER_CONFIG["transports"]["coap"]["port"] = cls._RESOLVER_BIND_PORTS[
            "coap"
        ]
        return cls

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._border_router_path = os.path.join(
            tempfile.gettempdir(), ".ssh-grenoble-CuI9vNhosI"
        )
        self._dns_resolver_path = os.path.join(
            tempfile.gettempdir(), ".ssh-grenoble-LAgWMJDWuC"
        )

    def pre_run(self, runner, run, ctx, *args, **kwargs):
        class Shell(riotctrl_shell.netif.Ifconfig):
            # pylint: disable=too-few-public-methods
            pass

        res = super().pre_run(runner, run, ctx, *args, **kwargs)
        if run["args"]["proxied"]:
            proxy = None
            for i, node in enumerate(runner.nodes):
                if not self.is_proxy(node):
                    continue
                firmware = runner.experiment.firmwares[i]
                ctrl_env = {
                    "BOARD": firmware.board,
                    "IOTLAB_NODE": node.uri,
                }
                ctrl = riotctrl.ctrl.RIOTCtrl(firmware.application_path, ctrl_env)
                ctrl.TERM_STARTED_DELAY = 0.1
                shell = Shell(ctrl)
                with ctrl.run_term(reset=False):
                    if self.verbosity:
                        ctrl.term.logfile = sys.stdout
                    # TODO determine by neighbors
                    netifs = riotctrl_shell.netif.IfconfigListParser().parse(
                        shell.ifconfig_list()
                    )
                    ifname = list(netifs)[0]
                    proxy = [
                        a["addr"]
                        for a in netifs[ifname]["ipv6_addrs"]
                        if a["scope"] == "global"
                    ][0]
            for i, node in enumerate(runner.nodes):
                if not self.is_source_node(runner, node):
                    continue
                firmware = runner.experiment.firmwares[i]
                ctrl_env = {
                    "BOARD": firmware.board,
                    "IOTLAB_NODE": node.uri,
                }
                ctrl = riotctrl.ctrl.RIOTCtrl(firmware.application_path, ctrl_env)
                ctrl.TERM_STARTED_DELAY = 0.1
                shell = Shell(ctrl)
                with ctrl.run_term(reset=False):
                    if self.verbosity:
                        ctrl.term.logfile = sys.stdout
                    ret = shell.cmd(f"proxy coap://[{proxy}]/")
                    if f"Configured proxy coap://[{proxy}]/" not in ret:
                        raise ExperimentError(f"Unable to configure proxy {proxy}")
        return res

    def is_proxy(self, node):
        return any(
            node.uri.startswith(p["name"])
            for p in self.descs["globals"]["nodes"]["network"]["proxies"]
        )

    def is_source_node(self, runner, node):
        return not self.is_proxy(node) and super().is_source_node(runner, node)

    def schedule_experiments(self, *args, **kwargs):
        wl_file = os.path.join(
            self.descs["globals"]["firmwares"][-1]["path"], "whitelist.inc"
        )

        with open(wl_file, "w", encoding="utf-8") as wl:
            print("#define L2_FILTER_WHITE_LIST { \\", file=wl)
            proxy = self.descs["globals"]["nodes"]["network"]["proxies"][-1]
            print(f"    \"{proxy['l2addr']}\", \\", file=wl)
            print("}", file=wl)
        return super().schedule_experiments(*args, **kwargs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "virtualenv", default=dle.VIRTUALENV, help="Virtualenv for the Python resolver"
    )
    parser.add_argument(
        "descs",
        nargs="?",
        default=os.path.join(dle.SCRIPT_PATH, "descs.yaml"),
        help="Experiment descriptions file",
    )
    parser.add_argument(
        "--limit-unscheduled",
        "-l",
        type=int,
        help=(
            "Limits the number of unscheduled experiments to "
            "be scheduled before each run"
        ),
    )
    parser.add_argument(
        "-v", "--verbosity", default="INFO", help="Verbosity as log level"
    )
    args = parser.parse_args()
    coloredlogs.install(level=getattr(logging, args.verbosity), milliseconds=True)
    logger.debug("Running %s", args.descs)
    dispatcher = Dispatcher(
        args.descs, virtualenv=args.virtualenv, verbosity=args.verbosity
    )
    dispatcher.load_experiment_descriptions(limit_unscheduled=args.limit_unscheduled)


if __name__ == "__main__":
    main()
