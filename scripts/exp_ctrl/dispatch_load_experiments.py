#! /usr/bin/env python3

# Copyright (C) 2021 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring,missing-function-docstring
# pylint: disable=missing-class-docstring

import argparse
import copy
import io
import ipaddress
import logging
import os
import pprint
import re
import subprocess
import sys
import tempfile
import time

import aiocoap.oscore
import coloredlogs
import libtmux
import numpy
import yaml

import riotctrl.ctrl
import riotctrl.shell

from iotlab_controller.constants import IOTLAB_DOMAIN
from iotlab_controller.nodes import BaseNodes
from iotlab_controller.experiment import ExperimentError
from iotlab_controller.experiment.descs import tmux_runner


__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
VIRTUALENV = "~/doc-eval-env"

sys.path.append(os.path.join(SCRIPT_PATH, "..", "..", "RIOT", "dist", "pythonlibs"))

# pylint: disable=wrong-import-position,import-error
import riotctrl_shell.gnrc  # noqa: E402
import riotctrl_shell.netif  # noqa: E402

logger = logging.getLogger(__name__)


class Runner(tmux_runner.TmuxExperimentRunner):
    # pylint: disable=too-few-public-methods
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resolver_running = False

    def get_tmux_cmds(self, run):  # pylint: disable=unused-argument
        if self.resolver_running:
            record_type = run.get("args", {}).get("record", "AAAA")
            family = {
                "A": "inet",
                "AAAA": "inet6",
            }
            yield f"query_bulk exec h.de {family[record_type]}"
        else:
            yield "ERROR: RESOLVER NOT RUNNING!"


class Dispatcher(tmux_runner.TmuxExperimentDispatcher):
    # pylint: disable=too-many-public-methods
    _EXPERIMENT_RUNNER_CLASS = Runner
    _DTLS_CREDENTIAL_ID = "Client_identity"
    _DTLS_CREDENTIAL_KEY = "secretPSK"
    _DNS_A_RECORD = "10.0.0.7"
    _DNS_AAAA_RECORD = "2001:db8::7"
    _OSCORE_KEYDIR = "oscore_server_creds/from-client1/"
    _RESOLVER_BIND_PORTS = {
        "udp": 5300,
        "dtls": 8530,
        "coap": 8383,
        "coaps": 8384,
        "oscore": 8383,
    }
    _RESOLVER_CONFIG = {
        "dtls": {
            "server_hello_done_delay": 0.04,
            "finish_delay": 0.04,
        },
        "dtls_credentials": {
            "client_identity": _DTLS_CREDENTIAL_ID,
            "psk": _DTLS_CREDENTIAL_KEY,
        },
        "mock_dns_upstream": {"IN": {"A": _DNS_A_RECORD, "AAAA": _DNS_AAAA_RECORD}},
        "transports": {
            "udp": {
                "port": _RESOLVER_BIND_PORTS["udp"],
            },
            "dtls": {
                "port": _RESOLVER_BIND_PORTS["dtls"],
            },
            "coap": {
                "port": _RESOLVER_BIND_PORTS["coap"],
            },
        },
    }
    DNS_COUNT = 100
    AVG_QUERIES_PER_SEC = 10
    QUERY_RESOLUTION = 1000

    def __init__(self, *args, virtualenv=VIRTUALENV, verbosity="INFO", **kwargs):
        super().__init__(*args, **kwargs)
        self._border_router_path = os.path.join(
            tempfile.gettempdir(), ".ssh-grenoble-EEEX1AvgB0"
        )
        self._dns_resolver_path = os.path.join(
            tempfile.gettempdir(), ".ssh-grenoble-weKwjBuCFs"
        )
        self._resolver_config_file = None
        self._resolver_bind_address = None
        self._wpan_prefix = None
        self.virtualenv = virtualenv
        self.verbosity = verbosity

    def pre_experiment(self, runner, ctx, *args, **kwargs):
        border_router, tap = self.start_border_router(runner)
        return {
            "border_router": border_router,
            "tap": tap,
            "nodes": BaseNodes(runner.nodes.non_sink_node_uris),
        }

    def post_experiment(self, runner, ctx, *args, **kwargs):
        self.stop_border_router(runner, ctx["border_router"])
        if not runner.runs:  # no more runs for the experiment
            runner.experiment.stop()

    def pre_run(self, runner, run, ctx, *args, **kwargs):
        exp = runner.experiment
        dns_resolver = self.start_dns_resolver(runner, run)
        self.set_ssh_agent_env(exp.tmux_session)
        run_log = os.path.join(
            runner.results_dir,
            f"{exp.tmux_session.session.name}." f"{exp.tmux_session.window.name}.log",
        )
        exp.cmd(
            f"ps -o comm= -p $PPID | grep -q '^script$' || " f"script -fa '{run_log}'"
        )
        sniffer, pcap_file_name = self.start_sniffer(runner, ctx)
        logname = ctx["logname"]
        if run.env["DNS_TRANSPORT"] == "oscore":
            self.set_oscore_credentials(runner)
        res = self.connect_to_resolver(runner, run, ctx)
        runner.resolver_running = res
        run.env["RESOLVER_RUNNING"] = str(int(res))
        if res:
            time.sleep(1)
            self.set_sleep_times(runner, run)
        else:
            raise ExperimentError("Resolver not running")
        pprint.pprint(run.env)
        return {
            "dns_resolver": dns_resolver,
            "sniffer": sniffer,
            "logname": logname,
            "pcap_file_name": pcap_file_name,
        }

    def post_run(self, runner, run, ctx, *args, **kwargs):
        exp = runner.experiment
        self.stop_dns_resolver(runner, ctx["dns_resolver"])
        self.stop_sniffer(runner, ctx["sniffer"])
        subprocess.run(["gzip", "-v", "-9", ctx["pcap_file_name"]], check=False)
        # set TMUX session to 0 to reinitialize it in case `run` window closes
        exp.tmux_session = None

    @property
    def resolver_bind_address(self):
        if self._resolver_bind_address is None:
            raise AssertionError("Please call get_resolver_bind_address()")
        return self._resolver_bind_address

    def resolver_endpoint(self, run):
        if self.resolver_bind_address is None:
            raise AssertionError("Please call get_resolver_bind_address()")
        assert self._RESOLVER_BIND_PORTS["coaps"] == (
            self._RESOLVER_BIND_PORTS["coap"] + 1
        )
        if run.env["DNS_TRANSPORT"] in ["coap", "coaps", "oscore"]:
            schema = (
                "coap"
                if run.env["DNS_TRANSPORT"] == "oscore"
                else run.env["DNS_TRANSPORT"]
            )
            return (
                f"{schema}://[{self.resolver_bind_address}]:"
                f"{self._RESOLVER_BIND_PORTS[run.env['DNS_TRANSPORT']]}/dns-query"
            )
        if run.env["DNS_TRANSPORT"] in ["dtls", "udp"]:
            return (
                f"[{self.resolver_bind_address}]:"
                f"{self._RESOLVER_BIND_PORTS[run.env['DNS_TRANSPORT']]}"
            )
        raise ValueError(f"Unexpected DNS_TRANSPORT {run.env['DNS_TRANSPORT']}")

    def site_ip_route(self, runner):
        return subprocess.check_output(
            f"{self.ssh_cmd(runner)} ip -6 route", shell=True
        ).decode()

    def get_resolver_bind_address(self, runner):
        if self._resolver_bind_address is None:
            ip_route_c = re.compile(r"^default\s.*\s+dev\s+([^\s]+)\s")
            ip_addr_c = re.compile(r"^\s+inet6\s+([0-9a-f:]+)/\d+\s+scope global")
            ip_route = self.site_ip_route(runner)
            for route_line in ip_route.splitlines():
                ip_route_match = ip_route_c.search(route_line)
                if ip_route_match:
                    iface = ip_route_match.group(1)
                    ip_addr = subprocess.check_output(
                        f"{self.ssh_cmd(runner)} ip -6 addr show dev {iface}",
                        shell=True,
                    ).decode()
                    for addr_line in ip_addr.splitlines():
                        ip_addr_match = ip_addr_c.search(addr_line)
                        if ip_addr_match:
                            self._resolver_bind_address = ip_addr_match.group(1)
                            return self._resolver_bind_address
        return self._resolver_bind_address

    @property
    def wpan_prefix(self):
        if self._wpan_prefix is None:
            raise AssertionError("Please call get_wpan_prefix()")
        return self._wpan_prefix

    def get_wpan_prefix(self, runner):
        if self._wpan_prefix is None:
            site_prefix = ipaddress.IPv6Network(runner.desc.env["SITE_PREFIX"])
            assert site_prefix.prefixlen < 64
            routes = [
                ipaddress.IPv6Network(route.split()[0].strip())
                for route in self.site_ip_route(runner).splitlines()
                if re.search(r"^[a-f0-9:]+/\d+", route)
            ]
            for subnet in site_prefix.subnets(64 - site_prefix.prefixlen):
                if all(route != subnet for route in routes):
                    return str(subnet)
        return self._wpan_prefix

    def get_free_tap(self, runner):
        num = 0
        links = [
            link
            for link in subprocess.check_output(
                f"{self.ssh_cmd(runner)} ip link",
                shell=True,
            )
            .decode()
            .splitlines()
            if re.search(r"^\d+:", link)
        ]
        while True:
            tap = f"tap{num}"
            if all(tap not in link for link in links):
                return tap
            num += 1
        # never reached, but there won't be endless TAPs either
        return None

    @staticmethod
    def ssh_cmd(runner=None):
        if runner is None:
            return ""
        return f"ssh lenders@{runner.nodes.site}.{IOTLAB_DOMAIN}"

    def resolver_config_file(self, runner, run):
        assert self._RESOLVER_BIND_PORTS["coaps"] == (
            self._RESOLVER_BIND_PORTS["coap"] + 1
        )
        if self._resolver_config_file is None:
            _resolver_config = copy.deepcopy(self._RESOLVER_CONFIG)
            if run.env["DNS_TRANSPORT"] == "oscore":
                _resolver_config["oscore_credentials"] = {
                    "keydir": self._OSCORE_KEYDIR,
                    "client_id": ":client1",
                }
            for transport in _resolver_config["transports"]:
                _resolver_config["transports"][transport][
                    "host"
                ] = self.get_resolver_bind_address(runner)
            if (
                "response_delay" in run["args"]
                and run["args"]["response_delay"]["queries"]
            ):
                _resolver_config["mock_dns_upstream"]["response_delay"] = run["args"][
                    "response_delay"
                ]
            config = io.StringIO()
            yaml.dump(_resolver_config, config)
            tmpfile = subprocess.check_output(
                f"{self.ssh_cmd(runner)} mktemp", shell=True
            ).decode()
            subprocess.check_call(
                f"echo '{config.getvalue()}' | {self.ssh_cmd(runner)} "
                f"tee {tmpfile}",
                shell=True,
                stdout=None if self.verbosity else subprocess.DEVNULL,
            )
            self._resolver_config_file = tmpfile
        return self._resolver_config_file

    def close_resolver_config_file(self, resolver):
        if self._resolver_config_file:
            resolver.send_keys(
                f"rm -v {self._resolver_config_file}",
                enter=True,
                suppress_history=False,
            )
            time.sleep(0.2)
            self._resolver_config_file = None

    def get_or_create_window(self, runner, name):
        runner.ensure_tmux_session()
        session = runner.experiment.tmux_session.session
        try:
            window = session.find_where({"window_name": name})
        except libtmux.exc.LibTmuxException:
            window = session.new_window(name, attach=False)
        if window is None:
            window = session.new_window(name, attach=False)
        res = window.select_pane(0)
        self.set_ssh_agent_env(res)
        time.sleep(0.2)
        for _ in range(3):
            # kill whatever ran here before
            res.send_keys("C-c", suppress_history=False)
        return res

    def _exit_dns_resolver_ssh(self, runner):
        subprocess.run(
            f"{self.ssh_cmd(runner)} -O exit -S {self._dns_resolver_path}",
            check=False,
            shell=True,
        )

    def start_dns_resolver(self, runner, run):
        self._exit_dns_resolver_ssh(runner)
        resolver = self.get_or_create_window(runner, "resolver")
        resolver_config_file = self.resolver_config_file(runner, run)
        resolver.send_keys(
            f"{self.ssh_cmd(runner)} -S {self._dns_resolver_path} -M",
            enter=True,
            suppress_history=False,
        )
        resolver.send_keys(
            f"{os.path.join(self.virtualenv, 'bin', 'aiodns-proxy')} "
            f"-v {self.verbosity} "
            f"-C {resolver_config_file}",
            enter=True,
            suppress_history=False,
        )
        time.sleep(3)
        return resolver

    def stop_dns_resolver(self, runner, resolver):
        for _ in range(3):
            resolver.send_keys("C-c", suppress_history=False)
            time.sleep(3)
        resolver.send_keys(
            "pkill -f aiodns-proxy",
            enter=True,
            suppress_history=False,
        )
        self.close_resolver_config_file(resolver)
        self._exit_dns_resolver_ssh(runner)

    def _exit_border_router_ssh(self, runner):
        subprocess.run(
            f"{self.ssh_cmd(runner)} -O exit -S {self._border_router_path}",
            check=False,
            shell=True,
        )

    def start_border_router(self, runner):
        self._exit_border_router_ssh(runner)
        border_router = self.get_or_create_window(runner, "border_router")
        wpan_prefix = self.get_wpan_prefix(runner)
        tap = self.get_free_tap(runner)
        border_router.send_keys(
            f"{self.ssh_cmd(runner)} -S {self._border_router_path} -M",
            enter=True,
            suppress_history=False,
        )
        time.sleep(1)
        ports = [str(p) for p in self._RESOLVER_BIND_PORTS.values()]
        border_router.send_keys(
            f"sudo ethos_uhcpd.py --udp-ports {','.join(ports)} "
            f"{runner.nodes.sink} {tap} {wpan_prefix}",
            enter=True,
            suppress_history=False,
        )
        time.sleep(3)
        return border_router, tap

    def stop_border_router(self, runner, border_router):
        for _ in range(3):
            border_router.send_keys("C-c", suppress_history=False)
            time.sleep(2)
        border_router.send_keys(
            "pkill -f /opt/ethos_tools",
            enter=True,
            suppress_history=False,
        )
        self._exit_border_router_ssh(runner)

    def start_sniffer(self, runner, ctx):
        sniffer = self.get_or_create_window(runner, "sniffer")
        sniffer.send_keys(f"cd {SCRIPT_PATH}", enter=True, suppress_history=False)
        pcap_file_name = ctx["logname"].replace(".log", ".pcap")
        sniffer.send_keys(
            f"{self.ssh_cmd(runner)} "
            f"sniffer_aggregator -i {runner.exp_id} -o - "
            f"> {pcap_file_name}",
            enter=True,
            suppress_history=False,
        )
        return sniffer, pcap_file_name

    def stop_sniffer(self, runner, sniffer):
        for _ in range(3):
            sniffer.send_keys("C-c", suppress_history=False)
        sniffer.send_keys(
            f"{self.ssh_cmd(runner)} " f"pkill -f sniffer_aggregator",
            enter=True,
            suppress_history=False,
        )

    @staticmethod
    def set_ssh_agent_env(tmux_pane):
        if ("SSH_AUTH_SOCK" in os.environ) and ("SSH_AGENT_PID" in os.environ):
            tmux_pane.send_keys(
                "export SSH_AUTH_SOCK='{}'".format(os.environ["SSH_AUTH_SOCK"]),
                enter=True,
                suppress_history=False,
            )
            tmux_pane.send_keys(
                "export SSH_AGENT_PID='{}'".format(os.environ["SSH_AGENT_PID"]),
                enter=True,
                suppress_history=False,
            )

    @staticmethod
    def has_global(shell):
        netifs = riotctrl_shell.netif.IfconfigListParser().parse(shell.ifconfig_list())
        ifname = list(netifs)[0]
        return any(a["scope"] == "global" for a in netifs[ifname]["ipv6_addrs"])

    def init_resolver_at_node(self, shell, run):
        res = shell.cmd(
            f"init {self.resolver_endpoint(run)} 5853 "
            f"{self._DTLS_CREDENTIAL_ID} "
            f"{self._DTLS_CREDENTIAL_KEY}",
            timeout=30 if run.env["DNS_TRANSPORT"] == "dtls" else 1,
        )
        return "Success" in res

    def set_oscore_credentials(self, runner):
        for i, node in enumerate(runner.nodes):
            if node == runner.nodes[runner.nodes.sink]:
                continue
            firmware = runner.experiment.firmwares[i]
            ctrl_env = {
                "BOARD": firmware.board,
                "IOTLAB_NODE": node.uri,
            }
            # pylint: disable=line-too-long
            # noqa: E501 ; See https://gitlab.com/oscore/liboscore/-/blob/master/tests/riot-tests/plugtest-server/oscore-key-derivation
            secctx = aiocoap.oscore.FilesystemSecurityContext(self._OSCORE_KEYDIR)
            secctx.sender_key, secctx.recipient_key = (
                secctx.recipient_key,
                secctx.sender_key,
            )
            secctx.sender_id, secctx.recipient_id = (
                secctx.recipient_id,
                secctx.sender_id,
            )
            ctrl = riotctrl.ctrl.RIOTCtrl(firmware.application_path, ctrl_env)
            ctrl.TERM_STARTED_DELAY = 0.1
            shell = riotctrl.shell.ShellInteraction(ctrl)
            with ctrl.run_term(reset=False):
                if self.verbosity:
                    ctrl.term.logfile = sys.stdout
                res = ""
                while "Successfully added user context" not in res:
                    res = shell.cmd(
                        f"userctx {secctx.algorithm.value} {secctx.sender_id.hex()} "
                        f"{secctx.recipient_id.hex()} {secctx.common_iv.hex()} "
                        f"{secctx.sender_key.hex()} {secctx.recipient_key.hex()}"
                    )
                    if "Successfully added user context" not in res:
                        time.sleep(1)
            time.sleep(1)
            return True

    def connect_to_resolver(self, runner, run, ctx):
        class Shell(riotctrl_shell.netif.Ifconfig, riotctrl_shell.gnrc.GNRCICMPv6Echo):
            # pylint: disable=too-few-public-methods
            pass

        for i, node in enumerate(runner.nodes):
            if node == runner.nodes[runner.nodes.sink]:
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
                count = 0
                while not self.has_global(shell):
                    time.sleep(10)
                    if count >= 3:
                        self.stop_border_router(runner, ctx["border_router"])
                        ctx["border_router"], ctx["tap"] = self.start_border_router(
                            runner
                        )
                        shell.cmd("reboot")
                    count += 1
                shell.cmd("6ctx")
                res = riotctrl_shell.gnrc.GNRCICMPv6EchoParser().parse(
                    shell.ping6(self.resolver_bind_address, interval=333)
                )
                if res.get("replies", 0) == 0:
                    logger.error("RESOLVER IS UNREACHABLE!")
                    return False
                if not self.init_resolver_at_node(shell, run):
                    logger.error("UNABLE TO CONNECT TO RESOLVER!")
                    return False
        return True

    @staticmethod
    def _set_sleep_times(shell, sleep_times):
        for sleep_time in sleep_times:
            retries = 3
            res = ""
            while f"Will wait {sleep_time:d} ms" not in res and retries > 0:
                res = shell.cmd(f"query_bulk add {sleep_time:d}")
                retries -= 1
            if retries == 0:
                assert f"Will wait {sleep_time:d} ms" in res

    def set_sleep_times(self, runner, run):
        dns_count = int(run.env.get("DNS_COUNT", self.DNS_COUNT))
        avg_queries_per_sec = float(
            run["args"].get("avg_queries_per_sec", self.AVG_QUERIES_PER_SEC)
        )
        rng = numpy.random.default_rng()
        for i, node in enumerate(runner.nodes):
            sleep_times = rng.poisson(
                self.QUERY_RESOLUTION / avg_queries_per_sec, size=dns_count
            )
            if node == runner.nodes[runner.nodes.sink]:
                continue
            firmware = runner.experiment.firmwares[i]
            ctrl_env = {
                "BOARD": firmware.board,
                "IOTLAB_NODE": node.uri,
            }
            ctrl = riotctrl.ctrl.RIOTCtrl(firmware.application_path, ctrl_env)
            ctrl.TERM_STARTED_DELAY = 0.1
            shell = riotctrl.shell.ShellInteraction(ctrl)
            with ctrl.run_term(reset=False):
                if self.verbosity:
                    ctrl.term.logfile = sys.stdout
                self._set_sleep_times(shell, sleep_times)
        return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "virtualenv", default=VIRTUALENV, help="Virtualenv for the Python resolver"
    )
    parser.add_argument(
        "descs",
        nargs="?",
        default=os.path.join(SCRIPT_PATH, "descs.yaml"),
        help="Experiment descriptions file",
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
    dispatcher.load_experiment_descriptions()


if __name__ == "__main__":
    main()
