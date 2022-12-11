# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-class-docstring,missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=redefined-outer-name,unused-argument

import importlib
import sys

import pytest

# pylint: disable=unused-import; used as fixtures for test case
from tests.test_create_max_age_descs import protect_globals  # noqa: F401
from tests.test_create_comp_n_descs import protect_n_globals  # noqa: F401


__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


@pytest.mark.parametrize(
    "number, args",
    [
        (6, [sys.argv[0]]),
        (6, [sys.argv[0], "--rebuild-first"]),
        (6, [sys.argv[0], "--exp-id", "1842375287"]),
        (6, [sys.argv[0], "--rebuild-first", "--exp-id", "1842375287"]),
        (8, [sys.argv[0]]),
        (8, [sys.argv[0], "--rebuild-first"]),
        (8, [sys.argv[0], "--exp-id", "1842375287"]),
        (8, [sys.argv[0], "--rebuild-first", "--exp-id", "1842375287"]),
        (24, [sys.argv[0]]),
        (24, [sys.argv[0], "--rebuild-first"]),
        (24, [sys.argv[0], "--exp-id", "1842375287"]),
        (24, [sys.argv[0], "--rebuild-first", "--exp-id", "1842375287"]),
    ],
)
def test_create_max_age_n_descs(  # pylint: disable=too-many-arguments
    monkeypatch,
    number,
    args,
    protect_globals,  # noqa: F811
    protect_n_globals,  # noqa: F811
    mock_experiment_factory,
    mock_run_factory,
):
    monkeypatch.setattr(sys, "argv", args)
    create_max_age_n_descs = importlib.import_module(f"create_max_age_{number}_descs")
    create_max_age_n_descs.main()
