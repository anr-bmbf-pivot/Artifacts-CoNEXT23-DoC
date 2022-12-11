#! /usr/bin/env python3

# Copyright (C) 2021-22 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring,missing-function-docstring
# pylint: disable=missing-class-docstring

import logging
import os
import re
import sys
import time
import tempfile

from iotlab_controller.experiment import ExperimentError

import riotctrl.ctrl
import riotctrl.shell

try:
    from . import dispatch_baseline_experiments as dle
except ImportError:
    import dispatch_baseline_experiments as dle

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021-22 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))

sys.path.append(os.path.join(SCRIPT_PATH, "..", "..", "RIOT", "dist", "pythonlibs"))

# pylint: disable=wrong-import-position,import-error
import riotctrl_shell.netif  # noqa: E402

logger = logging.getLogger(__name__)


class Runner(dle.Runner):
    def _init_firmwares(self):
        super()._init_firmwares()
        nodes = self._exp_params["nodes"]
        for node, firmware in zip(nodes, self._firmwares):
            if node.uri.startswith(nodes.sink):
                continue  # sink has no whitelist
            node_name = node.uri.split(".")[0]
            firmware.env["QUIETER"] = "1"
            firmware.env["WHITELIST_NAME"] = f"whitelist-{node_name}.inc"
            firmware.env["BINDIRBASE"] = os.path.join(
                firmware.application_path, f"{node_name}-bin"
            )
            firmware.flashfile = firmware.path.replace(
                os.path.sep + "bin" + os.path.sep,
                os.path.sep + f"{node_name}-bin" + os.path.sep,
            )
            neighbors = list(nodes.neighbors(node_name))
            assert neighbors, f"{node_name} has no neighbors"
            wl_file = os.path.join(
                firmware.application_path, firmware.env["WHITELIST_NAME"]
            )
            found_neighbors = set()
            with open(wl_file, "w", encoding="utf-8") as whitelist:
                print("#define L2_FILTER_WHITE_LIST { \\", file=whitelist)
                for neighbor in neighbors:
                    for name, l2addr in self.desc["nodes"]["l2addrs"].items():
                        if neighbor.startswith(name):
                            print(f'    "{l2addr}", \\', file=whitelist)
                            found_neighbors.add(neighbor)
                print("}", file=whitelist)
            assert all(
                neighbor in found_neighbors for neighbor in neighbors
            ), f"{neighbors} != {found_neighbors}"


class Dispatcher(dle.Dispatcher):
    _EXPERIMENT_RUNNER_CLASS = Runner
    _RESOLVER_BIND_PORTS = {
        "udp": 5301,
        "dtls": 8531,
        "coap": 8483,
        "coaps": 8484,
        "oscore": 8483,
    }

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        # pylint: disable=self-cls-assignment,no-value-for-parameter
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

    def __init__(self, filename, *args, **kwargs):
        super().__init__(filename, *args, **kwargs)
        descs = os.path.basename(filename).split(".")[0]
        self._border_router_path = os.path.join(
            tempfile.gettempdir(), f".ssh-grenoble-CuI9vNhosI-{descs}"
        )
        self._dns_resolver_path = os.path.join(
            tempfile.gettempdir(), f".ssh-grenoble-LAgWMJDWuC-{descs}"
        )

    @staticmethod
    def establish_session(shell):
        # send one query to enforce session / repeat window to be
        # initialized for encrypted communication
        ret = shell.cmd("query example.org inet6 fetch", timeout=60)
        # just look for transmission, response would be printed
        # asynchronously
        if re.search(r"\bt;\d+\s", ret) is None:
            raise ExperimentError("Unable to establish session")

    @staticmethod
    def configure_proxy(shell, proxy_addr):
        retries = 3
        while retries > 0:
            ret = shell.cmd(f"proxy coap://[{proxy_addr}]/")
            if f"Configured proxy coap://[{proxy_addr}]/" in ret:
                break
            retries -= 1
            time.sleep(0.5)
        if retries == 0:
            raise ExperimentError(f"Unable to configure proxy {proxy_addr}")

    def configure_proxies(self, runner, run):  # noqa: C901
        # pylint: disable=too-many-locals

        # configure proxies in a depth-first manner
        firmwares = {
            node.uri.split(".")[0]: runner.experiment.firmwares[i]
            for i, node in enumerate(runner.nodes)
        }
        shells = {}

        class Shell(riotctrl_shell.netif.Ifconfig):
            # pylint: disable=too-few-public-methods
            @classmethod
            def create(cls, node, node_name, verbosity=None):
                if node_name not in shells:  # pragma: no branch
                    firmware = firmwares[node_name]
                    ctrl_env = {
                        "BOARD": firmware.board,
                        "IOTLAB_NODE": node.uri,
                    }
                    ctrl = riotctrl.ctrl.RIOTCtrl(firmware.application_path, ctrl_env)
                    ctrl.TERM_STARTED_DELAY = 0.1
                    ctrl.start_term()
                    if verbosity:
                        ctrl.term.logfile = sys.stdout
                    shells[node_name] = cls(ctrl)
                return shells[node_name]

        stack = []
        stack.append(runner.nodes.sink)
        visited = set()
        proxied = run["args"].get("proxied", False)
        try:  # pylint: disable=too-many-nested-blocks
            while stack:
                node_name = stack.pop()
                proxy_addr = None
                if node_name not in visited:
                    node = runner.nodes[node_name]
                    if proxied and self.is_proxy(node):
                        shell = Shell.create(node, node_name, self.verbosity)
                        netifs = riotctrl_shell.netif.IfconfigListParser().parse(
                            shell.ifconfig_list()
                        )
                        ifname = list(netifs)[0]
                        proxy_addr = [
                            a["addr"]
                            for a in netifs[ifname]["ipv6_addrs"]
                            if a["scope"] == "global"
                        ][0]
                        shell.riotctrl.stop_term()
                        del shells[node_name]
                    for neighbor in runner.nodes.neighbors(node_name):
                        if neighbor not in visited and node_name != runner.nodes.sink:
                            neigh_node = runner.nodes[neighbor]
                            shell = Shell.create(neigh_node, neighbor, self.verbosity)
                            # do nodes stuff
                            if proxied:
                                assert proxy_addr
                                self.configure_proxy(shell, proxy_addr)
                            if self.is_source_node(  # pragma: no branch
                                runner, neigh_node
                            ):
                                self.establish_session(shell)
                        stack.append(neighbor)
                    visited.add(node_name)
        finally:
            for shell in shells.values():
                shell.riotctrl.stop_term()

    def pre_run(self, runner, run, ctx, *args, **kwargs):
        res = super().pre_run(runner, run, ctx, *args, **kwargs)
        self.configure_proxies(runner, run)
        return res

    def is_proxy(self, node):
        return any(
            node.uri.startswith(p["name"])
            for p in self.descs["globals"]["nodes"]["network"]["proxies"]
        )

    def is_source_node(self, runner, node):
        return not self.is_proxy(node) and super().is_source_node(runner, node)


if __name__ == "__main__":  # pragma: no cover
    dle.main(Dispatcher)
