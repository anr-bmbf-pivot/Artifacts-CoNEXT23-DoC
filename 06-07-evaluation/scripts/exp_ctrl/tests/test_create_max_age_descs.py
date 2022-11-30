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
# pylint: disable=redefined-outer-name,unused-argument

import copy
import sys

import pytest

import create_proxy_descs

import create_max_age_descs

from tests.test_create_proxy_descs import test_create_proxy_descs

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021-22 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


@pytest.fixture
def protect_globals():

    name = copy.deepcopy(create_proxy_descs.NAME)
    dns_transports = copy.deepcopy(create_proxy_descs.DNS_TRANSPORTS)
    coap_blocksizes = copy.deepcopy(create_proxy_descs.COAP_BLOCKSIZES)
    record_types = copy.deepcopy(create_proxy_descs.RECORD_TYPES)
    proxy_firmware = copy.deepcopy(create_proxy_descs.PROXY_FIRMWARE)
    max_age_modes = copy.deepcopy(create_proxy_descs.MAX_AGE_MODES)
    client_coap_cache = copy.deepcopy(create_proxy_descs.CLIENT_COAP_CACHE)
    dns_cache = copy.deepcopy(create_proxy_descs.DNS_CACHE)
    proxied = copy.deepcopy(create_proxy_descs.PROXIED)
    globs = copy.deepcopy(create_proxy_descs.GLOBALS)
    coap_run_name = copy.deepcopy(create_proxy_descs.COAP_RUN_NAME)

    yield

    create_proxy_descs.NAME = name
    create_proxy_descs.DNS_TRANSPORTS = dns_transports
    create_proxy_descs.COAP_BLOCKSIZES = coap_blocksizes
    create_proxy_descs.RECORD_TYPES = record_types
    create_proxy_descs.PROXY_FIRMWARE = proxy_firmware
    create_proxy_descs.MAX_AGE_MODES = max_age_modes
    create_proxy_descs.CLIENT_COAP_CACHE = client_coap_cache
    create_proxy_descs.DNS_CACHE = dns_cache
    create_proxy_descs.PROXIED = proxied
    create_proxy_descs.GLOBALS = globs
    create_proxy_descs.COAP_RUN_NAME = coap_run_name


@pytest.mark.parametrize(
    "args",
    [
        [sys.argv[0]],
        [sys.argv[0], "--rebuild-first"],
        [sys.argv[0], "--exp-id", "1842375287"],
        [sys.argv[0], "--rebuild-first", "--exp-id", "1842375287"],
    ],
)
def test_create_max_age_descs(
    mocker, args, protect_globals, mock_experiment_factory, mock_run_factory
):
    test_create_proxy_descs(
        mocker,
        args,
        mock_experiment_factory,
        mock_run_factory,
        main=create_max_age_descs.main,
    )
