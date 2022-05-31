# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright (C) 2021 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-class-docstring,missing-module-docstring
# pylint: disable=missing-function-docstring

import re

import pytest

from iotlab_controller.experiment.descs.file_handler import NestedDescriptionBase

import dispatch_load_experiments as dispatch


def test_runner_init(mocker, api_and_desc):
    runner = dispatch.Runner(dispatcher=mocker.MagicMock(), **api_and_desc)
    assert not runner.resolver_running


def test_runner_get_tmux_cmds(mocker, api_and_desc):
    runner = dispatch.Runner(dispatcher=mocker.MagicMock(), **api_and_desc)
    run = mocker.MagicMock()
    cmd_num = 0
    for cmd in runner.get_tmux_cmds(run):
        assert cmd == "ERROR: RESOLVER NOT RUNNING!"
        cmd_num += 1
    assert cmd_num == 1
    runner.resolver_running = True
    cmd_num = 0
    run.get = mocker.MagicMock(return_value={"record": "AAAA"})
    for cmd in runner.get_tmux_cmds(run=run):
        assert re.match(
            r"query_bulk exec id.exp.example.org inet6( (get|post|fetch))?", cmd
        )
        cmd_num += 1
    assert cmd_num == 1
    cmd_num = 0
    run = mocker.MagicMock()
    run.get = mocker.MagicMock(return_value={"record": "A"})
    for cmd in runner.get_tmux_cmds(run=run):
        assert re.match(
            r"query_bulk exec id.exp.example.org inet\b( (get|post|fetch))?", cmd
        )
        cmd_num += 1
    assert cmd_num == 1


def test_ssh_cmd(api_and_desc):
    dispatcher = dispatch.Dispatcher("test.yaml", api=api_and_desc["api"])
    runner = dispatch.Runner(dispatcher=dispatcher, **api_and_desc)
    runner.experiment.username = "foobar"
    assert dispatcher.ssh_cmd(None) == ""
    assert dispatcher.ssh_cmd(runner) == "ssh foobar@grenoble.iot-lab.info"


def test_site_ip_route(mocker, api_and_desc):
    check_output = mocker.patch("subprocess.check_output")
    dispatcher = dispatch.Dispatcher("test.yaml", api=api_and_desc["api"])
    runner = dispatch.Runner(dispatcher=dispatcher, **api_and_desc)
    runner.experiment.username = "foobar"
    res = dispatcher.site_ip_route(runner)
    check_output.assert_called_once_with(
        "ssh foobar@grenoble.iot-lab.info ip -6 route", shell=True
    )
    assert res == check_output.return_value.decode()


def test_dispatch_get_resolver_bind_address(mocker, api_and_desc):
    mocker.patch(
        "dispatch_load_experiments.Dispatcher.site_ip_route",
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
        "dispatch_load_experiments.Dispatcher.site_ip_route",
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
        "dispatch_load_experiments.Dispatcher.site_ip_route",
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
        "dispatch_load_experiments.Dispatcher.site_ip_route",
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
        "dispatch_load_experiments.Dispatcher.site_ip_route",
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
        "dispatch_load_experiments.Dispatcher.site_ip_route",
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
        "dispatch_load_experiments.Dispatcher.site_ip_route",
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
        "dispatch_load_experiments.Dispatcher.site_ip_route",
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
        "dispatch_load_experiments.Dispatcher.site_ip_route",
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


def test_dispatch_get_free_tap(api_and_desc):
    dispatcher = dispatch.Dispatcher("test.yaml", api=api_and_desc["api"])
    tap = dispatcher.get_free_tap(None)
    assert re.match(r"tap\d+", tap)


def test_dispatch_pre_experiment(mocker, api_and_desc):
    start_border_router = mocker.patch(
        "dispatch_load_experiments.Dispatcher.start_border_router",
        return_value=("the_border_router", "the_tap"),
    )
    dispatcher = dispatch.Dispatcher("test.yaml", api=api_and_desc["api"])
    runner = dispatch.Runner(dispatcher=dispatcher, **api_and_desc)
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


def test_dispatch_post_experiment(mocker, api_and_desc):
    stop_border_router = mocker.patch(
        "dispatch_load_experiments.Dispatcher.stop_border_router",
    )
    ctx = {"border_router": "the_border_router"}
    dispatcher = dispatch.Dispatcher("test.yaml", api=api_and_desc["api"])
    runner = dispatch.Runner(dispatcher=dispatcher, **api_and_desc)
    runner.experiment = mocker.MagicMock()
    dispatcher.post_experiment(runner, ctx)
    stop_border_router.assert_called_once_with(runner, "the_border_router")
    runner.experiment.stop.assert_called_once_with()
    runner.desc["runs"] = ["abcd"]
    runner.experiment.reset_mock()
    dispatcher.post_experiment(runner, ctx)
    runner.experiment.stop.assert_not_called()
