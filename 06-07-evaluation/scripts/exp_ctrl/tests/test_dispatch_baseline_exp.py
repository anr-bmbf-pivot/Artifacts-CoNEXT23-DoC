# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright (C) 2021-22 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-class-docstring,missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=too-many-lines

import os
import re
import sys

import libtmux
import libtmux.exc
import pytest

from iotlab_controller.experiment.descs.file_handler import NestedDescriptionBase
from iotlab_controller.constants import IOTLAB_DOMAIN

import dispatch_baseline_experiments as dispatch

from . import conftest

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021-22 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


@pytest.fixture(scope="module")
def test_run_desc():
    yield conftest.TEST_RUN_DESC


@pytest.fixture(scope="module")
def default_network():
    yield {
        "sink": "m3-10",
        "edgelist": [
            ["m3-10", "m3-232"],
        ],
        "site": "grenoble",
    }


@pytest.fixture(scope="module")
def dispatcher_class():
    yield dispatch.Dispatcher


@pytest.fixture(scope="module")
def runner_class():
    yield dispatch.Runner


def test_runner_init(mocker, api_and_desc):
    runner = dispatch.Runner(dispatcher=mocker.MagicMock(), **api_and_desc)
    assert not runner.resolver_running


def test_runner_get_tmux_cmds(mocker, api_and_desc):
    runner = dispatch.Runner(dispatcher=mocker.MagicMock(), **api_and_desc)
    run = NestedDescriptionBase()
    cmd_num = 0
    for cmd in runner.get_tmux_cmds(run):
        assert cmd == "ERROR: RESOLVER NOT RUNNING!"
        cmd_num += 1
    assert cmd_num == 1
    runner.resolver_running = True
    cmd_num = 0
    run = NestedDescriptionBase(args={"record": "AAAA"})
    for cmd in runner.get_tmux_cmds(run=run):
        assert re.match(
            r"query_bulk exec id.exp.example.org inet6( (get|post|fetch))?", cmd
        )
        cmd_num += 1
    assert cmd_num == 1
    cmd_num = 0
    run = NestedDescriptionBase(args={"record": "A"})
    for cmd in runner.get_tmux_cmds(run=run):
        assert re.match(
            r"query_bulk exec id.exp.example.org inet\b( (get|post|fetch))?", cmd
        )
        cmd_num += 1
    assert cmd_num == 1


def test_site_ip_route(mocker, mocked_dispatcher):
    check_output = mocker.patch("subprocess.check_output")
    dispatcher = mocked_dispatcher["dispatcher"]
    runner = mocked_dispatcher["runner"]
    res = dispatcher.site_ip_route(runner)
    check_output.assert_called_once_with(
        f"ssh {runner.experiment.username}@{runner.experiment.nodes.site}."
        f"{IOTLAB_DOMAIN} ip -6 route",
        shell=True,
    )
    assert res == check_output.return_value.decode()


def test_dispatch_get_resolver_bind_address(mocker, api_and_desc):
    mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.site_ip_route",
        return_value=(
            "::1 dev lo proto kernel metric 256 pref medium\n"
            "fe80::/64 dev ens3 proto kernel metric 256 pref medium\n"
        ),
    )
    mocker.patch(
        "subprocess.check_output",
        return_value=(b"  inet6 fe80::1/64 scope link\n"),
    )
    dispatcher = dispatch.Dispatcher("test.yaml", api=api_and_desc["api"])
    bind_address = dispatcher.get_resolver_bind_address(None)
    assert bind_address is None
    mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.site_ip_route",
        return_value=(
            "::1 dev lo proto kernel metric 256 pref medium\n"
            "default via 2001:db8::1 dev ens3 metric 1024 onlink pref medium"
            "fe80::/64 dev ens3 proto kernel metric 256 pref medium\n"
        ),
    )
    mocker.patch(
        "subprocess.check_output",
        return_value=(b"  inet6 fe80::1/64 scope link"),
    )
    bind_address = dispatcher.get_resolver_bind_address(None)
    assert bind_address is None
    mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.site_ip_route",
        return_value="default via 2001:db8::1 dev ens3 metric 1024 onlink pref medium",
    )
    mocker.patch(
        "subprocess.check_output",
        return_value=(
            b"  inet6 fe80::1/64 scope link\n" b"  inet6 2001:db8::2/64 scope global"
        ),
    )
    bind_address = dispatcher.get_resolver_bind_address(None)
    assert bind_address == "2001:db8::2"
    bind_address = dispatcher.get_resolver_bind_address(None)
    assert bind_address == "2001:db8::2"


def test_dispatch_resolver_bind_address(mocker, api_and_desc):
    dispatcher = dispatch.Dispatcher("test.yaml", api=api_and_desc["api"])
    with pytest.raises(AssertionError):
        dispatcher.resolver_bind_address  # pylint: disable=pointless-statement
    mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.site_ip_route",
        return_value=(
            "::1 dev lo proto kernel metric 256 pref medium\n"
            "default via 2001:db8::1 dev ens3 metric 1024 onlink pref medium\n"
            "fe80::/64 dev ens3 proto kernel metric 256 pref medium\n"
        ),
    )
    mocker.patch(
        "subprocess.check_output",
        return_value=(
            b"  inet6 fe80::1/64 scope link\n  inet6 2001:db8::2/64 scope global"
        ),
    )
    bind_address = dispatcher.get_resolver_bind_address(None)
    assert dispatcher.resolver_bind_address == bind_address


def test_dispatch_resolver_bind_ports(api_and_desc):
    dispatcher = dispatch.Dispatcher("test.yaml", api=api_and_desc["api"])
    assert dispatcher.resolver_bind_ports == [5300, 8383, 8383, 8384, 8530]


@pytest.mark.parametrize(
    "dns_transport, args, exp_bind_addr",
    [
        ("udp", None, "[2001:db8::2]:5300"),
        ("dtls", None, "[2001:db8::2]:8530"),
        ("coap", None, "coap://[2001:db8::2]:8383/dns"),
        ("coap", {"method": "get"}, "coap://[2001:db8::2]:8383/dns{?dns}"),
        ("coaps", None, "coaps://[2001:db8::2]:8384/dns"),
        ("coaps", {"method": "get"}, "coaps://[2001:db8::2]:8384/dns{?dns}"),
        ("oscore", None, "coap://[2001:db8::2]:8383/dns"),
        ("oscore", {"method": "get"}, "coap://[2001:db8::2]:8383/dns{?dns}"),
        ("foobar", None, ValueError),
        ("foobar", {"method": "get"}, ValueError),
    ],
)
def test_dispatch_resolver_endpoint(
    mocker, api_and_desc, dns_transport, args, exp_bind_addr
):
    run = NestedDescriptionBase({"env": {"DNS_TRANSPORT": dns_transport}})
    if args is not None:
        run["args"] = args
    dispatcher = dispatch.Dispatcher("test.yaml", api=api_and_desc["api"])
    mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.site_ip_route",
        return_value="default via 2001:db8::1 dev ens3 metric 1024 onlink pref medium",
    )
    mocker.patch(
        "subprocess.check_output",
        return_value=(
            b"  inet6 fe80::1/64 scope link\n" b"  inet6 2001:db8::2/64 scope global"
        ),
    )
    with pytest.raises(AssertionError):
        dispatcher.resolver_endpoint(run)
    dispatcher.get_resolver_bind_address(None)
    if isinstance(exp_bind_addr, str):
        assert dispatcher.resolver_endpoint(run) == exp_bind_addr
    else:
        with pytest.raises(exp_bind_addr):
            dispatcher.resolver_endpoint(run)


def test_dispatch_get_wpan_prefix(mocker, api_and_desc):
    assert api_and_desc["desc"]["env"]["SITE_PREFIX"] == "2001:db8::/62"
    dispatcher = dispatch.Dispatcher("test.yaml", api=api_and_desc["api"])
    runner = dispatch.Runner(dispatcher=dispatcher, **api_and_desc)
    mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.site_ip_route",
        return_value=(
            "::1 dev lo proto kernel metric 256 pref medium\n"
            "default via 2001:db8::1 dev ens3 metric 1024 onlink pref medium\n"
            "fe80::/64 dev ens3 proto kernel metric 256 pref medium\n"
        ),
    )
    assert dispatcher.get_wpan_prefix(runner) == "2001:db8::/64"
    dispatcher = dispatch.Dispatcher("test.yaml", api=api_and_desc["api"])
    runner = dispatch.Runner(dispatcher=dispatcher, **api_and_desc)
    mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.site_ip_route",
        return_value=(
            "::1 dev lo proto kernel metric 256 pref medium\n"
            "default via 2001:db8::1 dev ens3 metric 1024 onlink pref medium\n"
            "2001:db8::/64 via fe80::1 dev tap0 metric 1024 onlink pref medium\n"
            "fe80::/64 dev ens3 proto kernel metric 256 pref medium\n"
        ),
    )
    assert dispatcher.get_wpan_prefix(runner) == "2001:db8:0:1::/64"
    assert dispatcher.get_wpan_prefix(runner) == "2001:db8:0:1::/64"
    dispatcher = dispatch.Dispatcher("test.yaml", api=api_and_desc["api"])
    runner = dispatch.Runner(dispatcher=dispatcher, **api_and_desc)
    mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.site_ip_route",
        return_value=(
            "::1 dev lo proto kernel metric 256 pref medium\n"
            "default via 2001:db8::1 dev ens3 metric 1024 onlink pref medium\n"
            "2001:db8:0:0::/64 via fe80::1 dev tap0 metric 1024 onlink pref medium\n"
            "2001:db8:0:1::/64 via fe80::1 dev tap0 metric 1024 onlink pref medium\n"
            "2001:db8:0:2::/64 via fe80::1 dev tap0 metric 1024 onlink pref medium\n"
            "2001:db8:0:3::/64 via fe80::1 dev tap0 metric 1024 onlink pref medium\n"
            "fe80::/64 dev ens3 proto kernel metric 256 pref medium\n"
        ),
    )
    assert dispatcher.get_wpan_prefix(runner) is None


def test_dispatch_wpan_prefix(mocker, api_and_desc):
    assert api_and_desc["desc"]["env"]["SITE_PREFIX"] == "2001:db8::/62"
    dispatcher = dispatch.Dispatcher("test.yaml", api=api_and_desc["api"])
    runner = dispatch.Runner(dispatcher=dispatcher, **api_and_desc)
    mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.site_ip_route",
        return_value=(
            "::1 dev lo proto kernel metric 256 pref medium\n"
            "default via 2001:db8::1 dev ens3 metric 1024 onlink pref medium\n"
            "fe80::/64 dev ens3 proto kernel metric 256 pref medium\n"
        ),
    )
    with pytest.raises(AssertionError):
        dispatcher.wpan_prefix  # pylint: disable=pointless-statement
    wpan_prefix = dispatcher.get_wpan_prefix(runner)
    assert dispatcher.wpan_prefix == wpan_prefix


def test_dispatch_get_free_tap(mocker, api_and_desc):
    dispatcher = dispatch.Dispatcher("test.yaml", api=api_and_desc["api"])
    mocker.patch(
        "subprocess.check_output",
        return_value=b"",
    )
    tap = dispatcher.get_free_tap(None)
    assert re.match(r"tap\d+", tap)
    mocker.patch(
        "subprocess.check_output",
        return_value=b"208: tap0: <NO-CARRIER,BROADCAST,MULTICAST,UP>\n",
    )
    tap = dispatcher.get_free_tap(None)
    assert re.match(r"tap\d+", tap)


def test_ssh_cmd(mocked_dispatcher):
    dispatcher = mocked_dispatcher["dispatcher"]
    runner = mocked_dispatcher["runner"]
    assert dispatcher.ssh_cmd(None) == ""
    assert (
        dispatcher.ssh_cmd(runner)
        == f"ssh {runner.experiment.username}@{runner.experiment.nodes.site}."
        f"{IOTLAB_DOMAIN}"
    )


@pytest.mark.parametrize("unscheduled", [[]], indirect=["unscheduled"])
def test_dispatch_reschedule_experiment(mocker, mocked_dispatcher):
    mocker.patch("time.sleep")
    dispatcher = mocked_dispatcher["dispatcher"]
    runner = mocked_dispatcher["runner"]
    assert runner.experiment.exp_id not in dispatcher.descs
    assert "unscheduled" not in dispatcher.descs
    dispatcher.reschedule_experiment(runner)
    assert runner.experiment.exp_id not in dispatcher.descs
    assert runner.desc in dispatcher.descs["unscheduled"]
    dispatcher.descs["unscheduled"].pop()
    assert runner.experiment.exp_id not in dispatcher.descs
    dispatcher.descs[runner.experiment.exp_id] = runner.desc
    dispatcher.reschedule_experiment(runner)
    assert runner.experiment.exp_id not in dispatcher.descs
    assert runner.desc in dispatcher.descs["unscheduled"]


@pytest.mark.parametrize(
    "run",
    [
        NestedDescriptionBase(env={"DNS_TRANSPORT": "udp"}),
        NestedDescriptionBase(
            env={"DNS_TRANSPORT": "udp"}, args={"response_delay": {}}
        ),
        NestedDescriptionBase(
            env={"DNS_TRANSPORT": "udp"}, args={"response_delay": {"queries": None}}
        ),
        NestedDescriptionBase(
            env={"DNS_TRANSPORT": "udp"},
            args={"response_delay": {"queries": 1337, "time": 3.14}},
        ),
        NestedDescriptionBase(env={"DNS_TRANSPORT": "oscore"}),
    ],
)
def test_dispatch_resolver_config_file(mocker, mocked_dispatcher, run):
    tmpfile_name = "/tmp/foobar"
    mocker.patch("subprocess.check_output", return_value=tmpfile_name.encode())
    mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.get_resolver_bind_address",
        return_value="2001:db8::dead:c0ff:ee",
    )
    check_call = mocker.patch("subprocess.check_call")
    dispatcher = mocked_dispatcher["dispatcher"]
    runner = mocked_dispatcher["runner"]
    assert dispatcher.resolver_config_file(runner, run) == tmpfile_name
    check_call.assert_called_once()
    called_cmd = "".join(str(b[0][0]) for b in check_call.call_args_list)
    assert "host: 2001:db8::dead:c0ff:ee\n" in called_cmd
    assert f"tee {tmpfile_name}" in called_cmd
    if run.env["DNS_TRANSPORT"] == "oscore":
        assert "oscore_credentials" in called_cmd
    else:
        assert "oscore_credentials" not in called_cmd
    if run.get("args", {}).get("response_delay", {}).get("queries"):
        assert "response_delay:\n" in called_cmd
        assert f"  queries: {run['args']['response_delay']['queries']}\n" in called_cmd
        assert f"  time: {run['args']['response_delay']['time']}\n" in called_cmd
    else:
        assert "response_delay:\n" not in called_cmd
    assert dispatcher.resolver_config_file(runner, run) == tmpfile_name
    check_call.assert_called_once()
    return tmpfile_name


def test_dispatch_close_resolver_config_file(mocker, mocked_dispatcher):
    resolver = mocker.MagicMock()
    mocker.patch("time.sleep")
    dispatcher = mocked_dispatcher["dispatcher"]
    dispatcher.close_resolver_config_file(resolver)
    resolver.send_keys.assert_not_called()
    tmpfile_name = test_dispatch_resolver_config_file(
        mocker, mocked_dispatcher, NestedDescriptionBase(env={"DNS_TRANSPORT": "udp"})
    )
    dispatcher.close_resolver_config_file(resolver)
    resolver.send_keys.assert_called_once_with(
        f"rm -v {tmpfile_name}", enter=True, suppress_history=False
    )


def test_dispatch_get_or_create_window(mocker, mocked_dispatcher):
    mocker.patch("time.sleep")
    dispatcher = mocked_dispatcher["dispatcher"]
    runner = mocked_dispatcher["runner"]
    runner.experiment.tmux_session.session = mocker.Mock(spec=libtmux.Session)
    assert (
        dispatcher.get_or_create_window(runner, "test_window")
        == runner.experiment.tmux_session.session.find_where.return_value.select_pane()
    )
    runner.experiment.tmux_session.session.find_where.assert_called_once_with(
        {"window_name": "test_window"}
    )
    runner.experiment.tmux_session.session.find_where = mocker.MagicMock(
        side_effect=libtmux.exc.LibTmuxException
    )
    assert (
        dispatcher.get_or_create_window(runner, "test_window")
        == runner.experiment.tmux_session.session.new_window.return_value.select_pane()
    )
    runner.experiment.tmux_session.session.new_window.assert_called_once_with(
        "test_window", attach=False
    )
    runner.experiment.tmux_session.session.find_where = mocker.MagicMock(
        side_effect=[None, mocker.MagicMock()]
    )
    runner.experiment.tmux_session.session.new_window.reset_mock()
    assert (
        dispatcher.get_or_create_window(runner, "test_window")
        == runner.experiment.tmux_session.session.new_window.return_value.select_pane()
    )
    runner.experiment.tmux_session.session.new_window.assert_has_calls(
        [
            mocker.call("test_window", attach=False),
        ]
    )


def test_dispatch_start_dns_resolver(mocker, mocked_dispatcher):
    subprocess_run = mocker.patch("subprocess.run")
    resolver = mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.get_or_create_window"
    ).return_value
    mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.resolver_config_file",
        return_value="/tmp/foobar9000",
    )
    mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.ssh_cmd",
        return_value="test_ssh",
    )
    mocker.patch("time.sleep")
    dispatcher = mocked_dispatcher["dispatcher"]
    runner = mocked_dispatcher["runner"]
    dispatcher.start_dns_resolver(runner, {})
    subprocess_run.assert_called_once_with(
        # pylint: disable=protected-access
        f"test_ssh -O exit -S {dispatcher._dns_resolver_path}",
        check=False,
        shell=True,
    )
    resolver.send_keys.assert_has_calls(
        [
            # pylint: disable=protected-access
            mocker.call(
                f"test_ssh -S {dispatcher._dns_resolver_path} -M",
                enter=True,
                suppress_history=False,
            ),
            mocker.call(
                f"{os.path.join(dispatcher.virtualenv, 'bin', 'aiodns-proxy')}"
                f" -v {dispatcher.verbosity} -f -C /tmp/foobar9000",
                enter=True,
                suppress_history=False,
            ),
        ]
    )


def test_dispatch_stop_dns_resolver(mocker, mocked_dispatcher):
    mocker.patch("subprocess.run")
    mocker.patch("dispatch_baseline_experiments.Dispatcher.close_resolver_config_file")
    mocker.patch("time.sleep")
    dispatcher = mocked_dispatcher["dispatcher"]
    runner = mocked_dispatcher["runner"]
    dispatcher.stop_dns_resolver(runner, mocker.MagicMock())


@pytest.mark.parametrize(
    "network",  # passed to api_and_desc via mocked_dispatcher
    [
        None,  # use default network
        {
            "sink": "nrf52dk-9",
            "edgelist": [
                ["nrf52dk-9", "nrf52dk-10"],
            ],
            "site": "saclay",
        },
    ],
    indirect=["network"],
)
def test_dispatch_start_border_router(mocker, mocked_dispatcher):
    subprocess_run = mocker.patch("subprocess.run")
    timestamp_mock = 1072334710.324977
    border_router = mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.get_or_create_window"
    ).return_value
    border_router.cmd.return_value.stdout = [
        "foobar",
        str(timestamp_mock),
        "inet6 addr: 2001:db8:1337::1234 scope: global VAL",
    ]
    mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.get_wpan_prefix",
        return_value="2001:db8:1337::/64",
    )
    mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.get_free_tap",
        return_value="tap42",
    )
    mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.ssh_cmd",
        return_value="test_ssh",
    )
    mocker.patch("time.sleep")
    mocker.patch("time.time", return_value=timestamp_mock)
    dispatcher = mocked_dispatcher["dispatcher"]
    runner = mocked_dispatcher["runner"]
    the_border_router, tap = dispatcher.start_border_router(runner)
    subprocess_run.assert_called_once_with(
        # pylint: disable=protected-access
        f"test_ssh -O exit -S {dispatcher._border_router_path}",
        check=False,
        shell=True,
    )
    assert the_border_router == border_router
    assert tap == "tap42"
    ports = ",".join(str(p) for p in dispatcher.resolver_bind_ports)
    border_router.send_keys.assert_any_call(
        f"sudo ethos_uhcpd.py --udp-ports {ports} {runner.nodes.sink} "
        f"{tap} 2001:db8:1337::/64",
        enter=True,
        suppress_history=False,
    )
    border_router.cmd.return_value.stdout = [
        str(timestamp_mock),
        "[Errno 3] No such process: ethos",
    ]
    with pytest.raises(AssertionError):
        dispatcher.start_border_router(runner)
    border_router.cmd.return_value.stdout = [
        str(timestamp_mock),
        "ethos lost serial connection.",
    ]
    with pytest.raises(AssertionError):
        dispatcher.start_border_router(runner)


def test_dispatch_stop_border_router(mocker, mocked_dispatcher):
    mocker.patch("subprocess.run")
    mocker.patch("time.sleep")
    dispatcher = mocked_dispatcher["dispatcher"]
    runner = mocked_dispatcher["runner"]
    dispatcher.stop_border_router(runner, mocker.MagicMock(), "tap123")


@pytest.mark.parametrize(
    "network",  # passed to api_and_desc via mocked_dispatcher
    [
        None,  # use default network
        {
            "sink": "nrf52dk-9",
            "edgelist": [
                ["nrf52dk-9", "nrf52dk-10"],
            ],
            "site": "saclay",
        },
    ],
    indirect=["network"],
)
def test_dispatch_start_sniffer(mocker, mocked_dispatcher):
    sniffer = mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.get_or_create_window"
    ).return_value
    mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.ssh_cmd",
        return_value="test_ssh",
    )
    dispatcher = mocked_dispatcher["dispatcher"]
    runner = mocked_dispatcher["runner"]
    the_sniffer, pcap_file_name = dispatcher.start_sniffer(
        runner, {"logname": "test.log"}
    )
    if any(n.uri.startswith("nrf52") for n in runner.nodes):
        # sniffer is not used with BLE
        assert the_sniffer is None
        assert pcap_file_name is None
        sniffer.send_keys.assert_not_called()
    else:
        assert the_sniffer == sniffer
        assert pcap_file_name == "test.pcap"
        sniffer.send_keys.assert_any_call(
            f"test_ssh sniffer_aggregator -i {runner.exp_id} -o - > test.pcap",
            enter=True,
            suppress_history=False,
        )


def test_dispatch_stop_sniffer(mocker, mocked_dispatcher):
    dispatcher = mocked_dispatcher["dispatcher"]
    runner = mocked_dispatcher["runner"]
    dispatcher.stop_sniffer(runner, mocker.MagicMock())


def test_dispatch_set_ssh_agent_env(monkeypatch, mocker):
    monkeypatch.setattr(os, "environ", {"SSH_AUTH_SOCK": "foobar"})
    tmux_pane = mocker.MagicMock()
    dispatch.Dispatcher.set_ssh_agent_env(tmux_pane)
    tmux_pane.send_keys.assert_not_called()
    monkeypatch.setattr(os, "environ", {"SSH_AGENT_PID": 12345})
    dispatch.Dispatcher.set_ssh_agent_env(tmux_pane)
    tmux_pane.send_keys.assert_not_called()
    monkeypatch.setattr(
        os, "environ", {"SSH_AUTH_SOCK": "foobar", "SSH_AGENT_PID": 12345}
    )
    dispatch.Dispatcher.set_ssh_agent_env(tmux_pane)
    tmux_pane.send_keys.assert_called()


def test_dispatch_has_global(mocker):
    shell = mocker.MagicMock()
    assert not dispatch.Dispatcher.has_global(shell)
    shell.ifconfig_list = mocker.MagicMock(side_effect=ValueError)
    assert not dispatch.Dispatcher.has_global(shell)
    shell.ifconfig_list = mocker.MagicMock(
        return_value="""
Iface  7  HWaddr: E2:BC:7D:CB:F5:50
          L2-PDU:1500  MTU:1500  HL:64  Source address length: 6
          Link type: wired
          inet6 addr: fe80::e0bc:7dff:fecb:f550  scope: link  VAL
          inet6 group: ff02::1
          inet6 group: ff02::1:ffcb:f550
        """
    )
    assert not dispatch.Dispatcher.has_global(shell)
    shell.ifconfig_list = mocker.MagicMock(
        return_value="""
Iface  7  HWaddr: E2:BC:7D:CB:F5:50
          L2-PDU:1500  MTU:1500  HL:64  Source address length: 6
          Link type: wired
          inet6 addr: fe80::e0bc:7dff:fecb:f550  scope: link  VAL
          inet6 addr: 2001:db8::affe:abe:1  scope: global  VAL
          inet6 group: ff02::1
          inet6 group: ff02::1:ffcb:f550
        """
    )
    assert dispatch.Dispatcher.has_global(shell)


@pytest.mark.parametrize(
    "cmd_res, dns_transport",
    [
        ("Error", "udp"),
        ("Success", "udp"),
        ("Error", "dtls"),
        ("Success", "dtls"),
    ],
)
def test_dispatch_init_resolver_at_node(
    mocker, mocked_dispatcher, cmd_res, dns_transport
):
    mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.resolver_endpoint",
        return_value="foobar",
    )
    shell = mocker.MagicMock()
    dispatcher = mocked_dispatcher["dispatcher"]
    shell.cmd = mocker.MagicMock(return_value=cmd_res)
    run = NestedDescriptionBase(env={"DNS_TRANSPORT": dns_transport})
    assert dispatcher.init_resolver_at_node(shell, run) == ("Success" in cmd_res)
    if dns_transport == "dtls":
        shell.cmd.assert_called_with(
            "init foobar 5853 Client_identity secretPSK", timeout=30
        )
    else:
        shell.cmd.assert_called_with(
            "init foobar 5853 Client_identity secretPSK", timeout=1
        )


@pytest.mark.parametrize(
    "network",  # passed to api_and_desc via mocked_dispatcher
    [
        {
            "sink": "m3-232",
            "edgelist": [
                ["m3-232", "m3-10"],
            ],
            "site": "grenoble",
        },
    ],
    indirect=["network"],
)
def test_dispatch_is_source_node(mocked_dispatcher, network):
    dispatcher = mocked_dispatcher["dispatcher"]
    runner = mocked_dispatcher["runner"]
    assert not dispatcher.is_source_node(runner, runner.nodes[network["sink"]])
    assert dispatcher.is_source_node(runner, runner.nodes["m3-10"])


def test_dispatch_set_oscore_credential(mocker, mocked_dispatcher):
    mocker.patch(
        "riotctrl.shell.ShellInteraction.cmd",
        side_effect=["Some output", "Successfully added user context", "foobar"],
    )
    mocker.patch("riotctrl.ctrl.RIOTCtrl")
    mocker.patch("time.sleep")
    dispatcher = mocked_dispatcher["dispatcher"]
    runner = mocked_dispatcher["runner"]
    assert dispatcher.set_oscore_credentials(runner)
    mocker.patch(
        "riotctrl.shell.ShellInteraction.cmd",
        side_effect=["Some output", "Successfully added user context", "foobar"],
    )
    dispatcher.verbosity = 0
    assert dispatcher.set_oscore_credentials(runner)


def test_dispatch_wait_for_rpl(mocker, mocked_dispatcher):
    mocker.patch("time.sleep")
    shell = mocker.MagicMock()
    shell.cmd = mocker.MagicMock(
        side_effect=[
            """rpl
instance table:	[ ]
parent table:	[ ]	[ ]	[ ]	""",
            """rpl
instance table:	[X]
parent table:	[X]	[ ]	[ ]

instance [0 | Iface: 6 | mop: 2 | ocp: 0 | mhri: 256 | mri 0]
    dodag [2001:db8::1 | R: 512 | OP: Router | PIO: on | TR(I=[8,20], k=10, c=0)]
        parent [addr: fe80::204:2519:1801:ae82 | rank: 256]""",
            """nib route
2001:db8::/64 dev #6
default* via fe80::204:2519:1801:ae82 dev #6""",
        ]
    )
    dispatcher = mocked_dispatcher["dispatcher"]
    dispatcher.wait_for_rpl(shell, 123)
    shell.cmd = mocker.MagicMock(
        side_effect=[
            """rpl
instance table:	[ ]
parent table:	[ ]	[ ]	[ ]	""",
            """rpl
instance table:	[X]
parent table:	[X]	[ ]	[ ]

instance [0 | Iface: 6 | mop: 2 | ocp: 0 | mhri: 256 | mri 0]
    dodag [2001:db8::1 | R: 512 | OP: Router | PIO: on | TR(I=[8,20], k=10, c=0)]
        parent [addr: fe80::204:2519:1801:ae82 | rank: 256]""",
            """nib route
2001:db8::/64 dev #6""",
        ]
    )
    with pytest.raises(dispatch.ExperimentError):
        dispatcher.wait_for_rpl(shell, 123)


def test_dispatch_set_sleep_times(mocker, mocked_dispatcher):
    dispatcher = mocked_dispatcher["dispatcher"]
    runner = mocked_dispatcher["runner"]
    run = NestedDescriptionBase(env={"DNS_COUNT": 47}, args={"avg_queries_per_sec": 56})
    mocker.patch("riotctrl.ctrl.RIOTCtrl")
    mocker.patch("time.sleep")
    rng = mocker.patch("numpy.random.default_rng")
    rng.return_value.poisson = mocker.MagicMock(return_value=[53] * 47)
    mocker.patch(
        "riotctrl.shell.ShellInteraction.cmd",
        side_effect=(len(runner.nodes) - 1)
        * [f"{i}: Will wait 53 ms" for i in range(47)],
    )
    assert dispatcher.set_sleep_times(runner, run)
    mocker.patch(
        "riotctrl.shell.ShellInteraction.cmd",
        side_effect=(len(runner.nodes) - 1)
        * (
            ["Only able to store a schedule of 43 sleep times"]
            + [f"{i}: Will wait 53 ms" for i in range(47)]
        ),
    )
    dispatcher.verbosity = 0
    assert dispatcher.set_sleep_times(runner, run)
    mocker.patch(
        "riotctrl.shell.ShellInteraction.cmd",
        side_effect=(len(runner.nodes) - 1)
        * (4 * ["Nope"] + [f"{i}: Will wait 53 ms" for i in range(47)]),
    )
    assert dispatcher.set_sleep_times(runner, run)


@pytest.mark.parametrize("link_layer", ["ieee802154", "ble"])
def test_dispatch_connect_to_resolver(mocker, mocked_dispatcher, link_layer):
    mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.start_border_router",
        return_value=(mocker.MagicMock(), "tap42"),
    )
    mocker.patch("dispatch_baseline_experiments.Dispatcher.stop_border_router")
    has_global = mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.has_global",
        side_effect=[False, False, False, False, False, True],
    )
    mocker.patch("dispatch_baseline_experiments.Dispatcher.wait_for_rpl")
    mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.resolver_bind_address",
        return_value="2001:db8::1",
    )
    init_resolver_at_node = mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.init_resolver_at_node",
        return_value=False,
    )
    mocker.patch("riotctrl.ctrl.RIOTCtrl")
    mocker.patch("riotctrl.shell.ShellInteraction.cmd")
    mocker.patch("time.sleep")
    dispatcher = mocked_dispatcher["dispatcher"]
    runner = mocked_dispatcher["runner"]
    run = NestedDescriptionBase(link_layer=link_layer)
    ctx = {"border_router": mocker.MagicMock(), "tap": "tap322"}
    assert not dispatcher.connect_to_resolver(runner, run, ctx)
    mocker.patch(
        "riotctrl_shell.gnrc.GNRCICMPv6EchoParser.parse", return_value={"replies": 1}
    )
    has_global.reset_mock(side_effect=[True])
    dispatcher.verbosity = 0
    assert not dispatcher.connect_to_resolver(runner, run, ctx)
    has_global.reset_mock(side_effect=[True])
    init_resolver_at_node.reset_mock(return_value=True)
    assert dispatcher.connect_to_resolver(runner, run, ctx)


def test_dispatch_pre_experiment(mocker, mocked_dispatcher, api_and_desc):
    start_border_router = mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.start_border_router",
        return_value=("the_border_router", "the_tap"),
    )
    dispatcher = mocked_dispatcher["dispatcher"]
    runner = mocked_dispatcher["runner"]
    res = dispatcher.pre_experiment(runner, ctx={})
    start_border_router.assert_called_once_with(runner)
    assert res["border_router"] == "the_border_router"
    assert res["tap"] == "the_tap"
    for node in res["nodes"]:
        assert not node.uri.startswith(api_and_desc["desc"]["nodes"]["network"]["sink"])
        assert any(  # pragma: no cover
            node.uri.startswith(edge[0]) or node.uri.startswith(edge[1])
            for edge in api_and_desc["desc"]["nodes"]["network"]["edgelist"]
        )


def test_dispatch_post_experiment(mocker, mocked_dispatcher, api_and_desc):
    stop_border_router = mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.stop_border_router",
    )
    ctx = {"border_router": "the_border_router", "tap": "tap413"}
    dispatcher = mocked_dispatcher["dispatcher"]
    runner = mocked_dispatcher["runner"]
    dispatcher.post_experiment(runner, ctx)
    stop_border_router.assert_called_once_with(runner, "the_border_router", "tap413")
    runner.desc["runs"] = ["abcd"]
    api_and_desc["api"].stop_experiment.assert_called_once()
    dispatcher.post_experiment(runner, ctx)
    api_and_desc["api"].stop_experiment.assert_called_once()


@pytest.mark.parametrize(
    "run, connect_to_resolver_res",
    [
        (NestedDescriptionBase(env={"DNS_TRANSPORT": "udp"}), True),
        (NestedDescriptionBase(env={"DNS_TRANSPORT": "udp"}, link_layer="ble"), False),
        (NestedDescriptionBase(env={"DNS_TRANSPORT": "udp"}, link_layer="ble"), True),
        (NestedDescriptionBase(env={"DNS_TRANSPORT": "oscore"}), True),
    ],
)
def test_dispatch_pre_run(mocker, mocked_dispatcher, run, connect_to_resolver_res):
    start_dns_resolver = mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.start_dns_resolver",
    )
    mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.start_sniffer",
        return_value=("the_sniffer", "test.pcap"),
    )
    reschedule_experiment = mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.reschedule_experiment",
        return_value=True,
    )
    mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.connect_to_resolver",
        return_value=connect_to_resolver_res,
    )
    mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.set_ssh_agent_env",
    )
    mocker.patch(
        "time.sleep",
    )
    set_oscore_credentials = mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.set_oscore_credentials",
    )
    set_sleep_times = mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.set_sleep_times",
    )
    dispatcher = mocked_dispatcher["dispatcher"]
    runner = mocked_dispatcher["runner"]
    if connect_to_resolver_res:
        res = dispatcher.pre_run(runner, run, ctx={"logname": "test.log"})
        assert len(res) == 4
        assert res["dns_resolver"] == start_dns_resolver()
        assert res["sniffer"] == "the_sniffer"
        assert res["logname"] == "test.log"
        assert res["pcap_file_name"] == "test.pcap"
    else:
        with pytest.raises(dispatch.ExperimentError):
            dispatcher.pre_run(runner, run, ctx={"logname": "test.log"})
    if run.get("link_layer") == "ble" and not connect_to_resolver_res:
        reschedule_experiment.assert_called()
    else:
        reschedule_experiment.assert_not_called()
    if run.env.get("DNS_TRANSPORT") == "oscore":
        set_oscore_credentials.assert_called()
    else:
        set_oscore_credentials.assert_not_called()
    if connect_to_resolver_res:
        set_sleep_times.assert_called()
    else:
        set_sleep_times.assert_not_called()


@pytest.mark.parametrize(
    "ctx",
    [
        {},
        {"sniffer": None},
        {"pcap_file_name": "test.pcap"},
    ],
)
def test_dispatch_post_run(mocker, mocked_dispatcher, ctx):
    br_log = mocker.mock_open()
    stop_dns_resolver = mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.stop_dns_resolver",
    )
    mocker.patch(
        "time.sleep",
    )
    subprocess_run = mocker.patch("subprocess.run")
    mocker.patch("dispatch_baseline_experiments.open", br_log)
    dispatcher = mocked_dispatcher["dispatcher"]
    runner = mocked_dispatcher["runner"]
    run = NestedDescriptionBase()
    tmux_session = runner.experiment.tmux_session
    tmux_session.capture_pane = mocker.MagicMock(
        return_value=[
            r"Aggregator started",
        ]
    )
    ctx["dns_resolver"] = mocker.MagicMock()
    ctx["logname"] = "test.log"
    if "sniffer" in ctx:
        ctx["sniffer"] = mocker.MagicMock()
    ctx["border_router"] = mocker.MagicMock()
    ctx["border_router"].cmd.return_value = mocker.MagicMock(
        stdout=[
            r"test foobar",
            r"shell: command not found: test.log",
            r"Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy",
            r"eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam",
            r"voluptua.",
            r"reboot",
            r"At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd",
            r"gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet.",
        ]
    )
    dispatcher.post_run(runner, run, ctx)
    stop_dns_resolver.assert_called_once()
    tmux_session.send_keys.assert_has_calls(
        [
            mocker.call(
                f"ssh {runner.experiment.username}@{runner.experiment.nodes.site}"
                f".{IOTLAB_DOMAIN} serial_aggregator -i {runner.experiment.exp_id}| "
                f"tee -a {ctx['logname']}",
                enter=True,
                suppress_history=False,
            ),
            mocker.call("ifconfig", enter=True, suppress_history=False),
            mocker.call("pktbuf", enter=True, suppress_history=False),
            mocker.call("ps", enter=True, suppress_history=False),
        ]
    )
    if "pcap_file_name" in ctx:
        subprocess_run.assert_called_with(
            ["gzip", "-v", "-9", ctx["pcap_file_name"]], check=False
        )
    ctx["border_router"].send_keys.assert_has_calls(
        [
            mocker.call("ifconfig", enter=True, suppress_history=False),
            mocker.call("pktbuf", enter=True, suppress_history=False),
            mocker.call("ps", enter=True, suppress_history=False),
            mocker.call("6lo_frag", enter=True, suppress_history=False),
            mocker.call("reboot", enter=True, suppress_history=False),
        ]
    )
    br_log_content = "".join(str(b[0][0]) for b in br_log().write.call_args_list)
    assert (
        br_log_content
        == """Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy
eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam
voluptua.
"""
    )
    assert runner.experiment.tmux_session is None
    runner.experiment.tmux_session = mocker.MagicMock()
    runner.experiment.tmux_session.capture_pane = mocker.MagicMock(
        return_value=[
            r"Aggregator started",
        ]
    )
    ctx["border_router"].cmd.return_value = mocker.MagicMock(
        stdout=[
            r"test foobar",
            r"shell: command not found: test.log",
        ]
    )
    dispatcher.post_run(runner, run, ctx)
    assert runner.experiment.tmux_session is None


@pytest.mark.parametrize(
    "args",
    [
        [sys.argv[0], "test.yaml"],
        [sys.argv[0], "test.yaml", "-l", "10"],
        [sys.argv[0], "test.yaml", "-l", "10", "-v", "ERROR"],
        [sys.argv[0], "test.yaml", "-c", "12345"],
    ],
)
def test_main(monkeypatch, mocker, api_and_desc, args):
    monkeypatch.setattr(sys, "argv", args)
    mocker.patch(
        "iotlab_controller.common.get_default_api", return_value=api_and_desc["api"]
    )
    load_experiment_descriptions = mocker.patch(
        "dispatch_baseline_experiments.Dispatcher.load_experiment_descriptions"
    )
    dispatch.main(dispatch.Dispatcher)
    load_experiment_descriptions.assert_called_once()
    load_experiment_descriptions.reset_mock()
