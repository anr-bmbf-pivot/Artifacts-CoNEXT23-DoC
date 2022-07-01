# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring,missing-class-docstring
# pylint: disable=missing-function-docstring

import os
import subprocess

from .. import plot_common as pc

from .. import collect_build_sizes

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


def test_cosy(mocker):
    script_path = os.path.dirname(os.path.realpath(__file__))
    make_run = mocker.patch("riotctrl.ctrl.RIOTCtrl.make_run")
    with open(os.path.join(script_path, "test_cosy_output.txt"), "rb") as f:
        make_run.return_value.stdout = f.read()
    res = collect_build_sizes.cosy("udp", with_get=True)
    assert len(res) == 10
    exp = [
        {"sym": "ts_printf", "type": "t", "size": 52, "obj": "main.o"},
        {
            "sym": "gcoap_dns_server_uri_template_set",
            "type": "t",
            "size": 200,
            "obj": "dns.o",
        },
        {"sym": "_tl_send", "type": "t", "size": 126, "obj": "gcoap.o"},
        {"sym": "_on_resp_timeout", "type": "t", "size": 136, "obj": "gcoap.o"},
        {"sym": "_event_loop", "type": "t", "size": 144, "obj": "gcoap.o"},
        {"sym": "gcoap_init", "type": "t", "size": 144, "obj": "gcoap.o"},
        {"sym": "_credential", "type": "d", "size": 28, "obj": "main.o"},
        {"sym": "_coap_state", "type": "d", "size": 13540, "obj": "gcoap.o"},
        {"sym": "netq_storage", "type": "b", "size": 8, "obj": "netq.o"},
        {"sym": "peer_storage_data", "type": "b", "size": 88, "obj": "peer.o"},
    ]
    for i, sym in enumerate(res):
        for key in ["obj", "size", "sym", "type"]:
            assert sym[key] == exp[i][key]
    make_run = mocker.patch(
        "riotctrl.ctrl.RIOTCtrl.make_run",
        side_effect=subprocess.CalledProcessError(returncode=1223, cmd="foobar"),
    )
    assert collect_build_sizes.cosy("udp", with_get=True) == []


def test_filename():
    assert collect_build_sizes.filename("udp") == os.path.join(
        pc.DATA_PATH, "doc-eval-build-sizes-udp.json"
    )
    assert collect_build_sizes.filename("coap") == os.path.join(
        pc.DATA_PATH, "doc-eval-build-sizes-coap-get0.json"
    )
    assert collect_build_sizes.filename("coap", with_get=True) == os.path.join(
        pc.DATA_PATH, "doc-eval-build-sizes-coap-get1.json"
    )


def test_write_json(mocker):
    open_mock = mocker.mock_open()
    mocker.patch("plots.collect_build_sizes.open", open_mock)
    collect_build_sizes.write_json("test.json", {"abcd": 1})
    open_mock.assert_called_once_with("test.json", "w")
    output = "".join(b[0][0] for b in open_mock().write.call_args_list)
    assert output == '{\n "abcd": 1\n}'


def test_read_json(mocker):
    open_mock = mocker.mock_open(read_data='{\n "xyz": 42\n}')
    mocker.patch("plots.collect_build_sizes.open", open_mock)
    assert collect_build_sizes.read_json("test.json") == {"xyz": 42}
    open_mock.assert_called_once_with("test.json")


def test_get_syms(mocker):
    cosy = mocker.patch("plots.collect_build_sizes.cosy")
    write_json = mocker.patch("plots.collect_build_sizes.write_json")
    mocker.patch("plots.collect_build_sizes.filename", return_value="foobar")
    assert collect_build_sizes.get_syms("get") == cosy.return_value
    cosy.assert_called_once_with("get", False)
    write_json.assert_called_once_with("foobar", cosy.return_value)


def test_main(mocker, capsys):
    get_syms = mocker.patch("plots.collect_build_sizes.get_syms")
    collect_build_sizes.main()
    out, err = capsys.readouterr()
    assert out == ("." * len(get_syms.mock_calls)) + "\n"
    assert err == ""
    exp_calls = [
        mocker.call(t, g)
        for g in [False, True]
        for t in pc.TRANSPORTS
        if t in pc.COAP_TRANSPORTS or not g
    ]
    assert len(get_syms.mock_calls) == len(exp_calls)
    get_syms.assert_has_calls(exp_calls, any_order=True)
