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

import os
import sys
import yaml

import pytest

import create_proxy_descs

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021-22 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


@pytest.mark.parametrize(
    "args",
    [
        [sys.argv[0]],
        [sys.argv[0], "--rebuild-first"],
        [sys.argv[0], "--exp-id", "68486999"],
        [sys.argv[0], "--rebuild-first", "--exp-id", "68486999"],
    ],
)
def test_create_proxy_descs(
    mocker, args, mock_experiment_factory, mock_run_factory, main=None
):
    open_mock = mocker.mock_open()
    mocker.patch("create_proxy_descs.open", open_mock)
    mocker.patch("sys.argv", args)

    if main is None:
        create_proxy_descs.main()
    else:
        main()

    open_mock.assert_called_with(
        os.path.join(create_proxy_descs.SCRIPT_PATH, "descs.yaml"),
        "w",
        encoding="utf-8",
    )
    open_mock.return_value.write.assert_called()
    write_args, _ = open_mock.return_value.write.call_args
    yaml_dict = yaml.load(write_args[0], Loader=yaml.FullLoader)
    assert yaml_dict["globals"] == create_proxy_descs.GLOBALS
    if "--exp-id" in args:
        exp_id = int(args[args.index("--exp-id") + 1])
        assert exp_id in yaml_dict
        runs = yaml_dict[exp_id]["runs"]
    else:
        exp_id = 15704443129291459354
        assert len(yaml_dict["unscheduled"]) == 1
        runs = yaml_dict["unscheduled"][0]["runs"]
    if len(runs) and "--rebuild-first" in args:
        assert runs[0]["rebuild"]
    for run in runs:
        assert "args" in run
        assert "env" in run
        assert "response_delay" in run["args"]
        assert "DNS_TRANSPORT" in run["env"]
        exp = mock_experiment_factory(exp_id=exp_id)
        run_name = yaml_dict["globals"]["run_name"].format(
            run=mock_run_factory(**run), exp=exp, time=2235634511
        )
        assert str(exp_id) in run_name
        assert exp.name in run_name
        assert "2235634511" in run_name
