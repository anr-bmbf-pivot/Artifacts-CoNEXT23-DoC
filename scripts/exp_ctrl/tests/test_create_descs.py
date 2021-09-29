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

import os
import sys
import yaml

import pytest

from create_load_descs import main, GLOBALS, SCRIPT_PATH


class MockExperiment:
    def __init__(self, exp_id):
        self._exp_id = exp_id

    @property
    def name(self):
        return "mock_experiment"

    @property
    def exp_id(self):
        return self._exp_id


class MockRun:  # pylint: disable=too-few-public-methods
    def __init__(self, args, env, *a, **kwargs):
        # pylint: disable=unused-argument
        self._args = args
        self.env = env

    def __getitem__(self, key):
        if key == "args":
            return self._args
        raise KeyError(key)  # pragma: no cover


@pytest.mark.parametrize(
    "args",
    [
        [sys.argv[0]],
        [sys.argv[0], "--rebuild-first"],
        [sys.argv[0], "--exp-id", "68486999"],
        [sys.argv[0], "--rebuild-first", "--exp-id", "68486999"],
    ],
)
def test_create_load_descs(mocker, args):
    open_mock = mocker.mock_open()
    mocker.patch("create_load_descs.open", open_mock)
    mocker.patch("sys.argv", args)

    main()

    open_mock.assert_called_with(
        os.path.join(SCRIPT_PATH, "descs.yaml"), "w", encoding="utf-8"
    )
    open_mock.return_value.write.assert_called()
    write_args, _ = open_mock.return_value.write.call_args
    yaml_dict = yaml.load(write_args[0], Loader=yaml.FullLoader)
    assert yaml_dict["globals"] == GLOBALS
    if "--exp-id" in args:
        exp_id = int(args[args.index("--exp-id") + 1])
        assert exp_id in yaml_dict
        runs = yaml_dict[exp_id]["runs"]
    else:
        exp_id = 16845407703279583489
        assert len(yaml_dict["unscheduled"]) == 1
        runs = yaml_dict["unscheduled"][0]["runs"]
    if len(runs) and "--rebuild-first" in args:
        assert runs[0]["rebuild"]
    for run in runs:
        assert "args" in run
        assert "env" in run
        assert "response_delay" in run["args"]
        assert "DNS_TRANSPORT" in run["env"]
        exp = MockExperiment(exp_id=exp_id)
        run_name = yaml_dict["globals"]["run_name"].format(
            run=MockRun(**run), exp=exp, time=596608887
        )
        assert str(exp_id) in run_name
        assert exp.name in run_name
        assert "596608887" in run_name
