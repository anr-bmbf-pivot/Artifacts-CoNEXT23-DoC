# Copyright (C) 2021-22 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import json
import os
import subprocess
import sys

import pytest

from .. import parse_baseline_results
from .. import parse_comp_results
from .. import parse_max_age_link_util
from .. import parse_max_age_results
from .. import plot_build_sizes
from .. import plot_common as pc
from .. import plot_baseline
from .. import plot_baseline_trans
from .. import plot_comp_trans
from .. import plot_comp_cdf
from .. import plot_comp_cdf_blockwise
from .. import plot_done
from .. import plot_max_age_cdf
from .. import plot_max_age_link_util
from .. import plot_max_age_trans
from .. import plot_pkt_sizes
from .. import plot_pkt_sizes_coap
from .. import plot_pkt_sizes_slides
from .. import plot_pkt_sizes_hypo

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021-22 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


@pytest.fixture(scope="module")
def results_tree_ids():  # pragma: no cover
    json_filename = os.path.join(pc.SCRIPT_PATH, "results_tree_ids.json")
    if os.path.exists(json_filename):
        try:
            with open(json_filename, encoding="utf-8") as json_file:
                res = json.load(json_file)
        except json.JSONDecodeError:
            res = {}
    else:
        res = {}
    yield res
    with open(json_filename, "w", encoding="utf-8") as json_file:
        json.dump(res, json_file)


@pytest.fixture
def baseline_results(monkeypatch):
    monkeypatch.setenv(
        "DATA_PATH",
        os.path.join(
            pc.SCRIPT_PATH, "..", "..", "results", "2022-02-17-baseline-results"
        ),
    )
    data_path = pc.DATA_PATH
    pc.DATA_PATH = os.environ["DATA_PATH"]
    yield
    pc.DATA_PATH = data_path


def results_id(data_path=pc.DATA_PATH):
    result_dir_name = os.path.basename(data_path)
    result_dir_base = os.path.dirname(data_path)
    return (
        subprocess.check_output(
            f"git -C {result_dir_base} ls-tree HEAD "
            f"| awk '$4 ~ /{result_dir_name}/ {{print $3}}'",
            shell=True,
        )
        .decode()
        .strip()
    )


def scripts_id(script_path=pc.SCRIPT_PATH):
    script_dir_name = os.path.basename(script_path)
    script_dir_base = os.path.dirname(script_path)
    return (
        subprocess.check_output(
            f"git -C {script_dir_base} ls-tree HEAD "
            f"| awk '$4 ~ /{script_dir_name}/ {{print $3}}'",
            shell=True,
        )
        .decode()
        .strip()
    )


@pytest.fixture
def parse_baseline_fixture(results_tree_ids, baseline_results):
    results = results_id(os.environ["DATA_PATH"])
    scripts = scripts_id()
    if results_tree_ids.get("baseline") != [results, scripts]:  # pragma: no cover
        results_tree_ids["baseline"] = [results, scripts]
        # can't call main, since we need to set data_path
        parse_baseline_results.logs_to_csvs(data_path=os.environ["DATA_PATH"])
    yield


@pytest.fixture
def parse_comp_fixture(results_tree_ids, monkeypatch):
    results = results_id()
    scripts = scripts_id()
    if results_tree_ids.get("comp") != [results, scripts]:  # pragma: no cover
        results_tree_ids["comp"] = [results, scripts]
        monkeypatch.setattr(sys, "argv", ["cmd"])
        parse_comp_results.main()
    yield


@pytest.fixture
def parse_max_age_fixture(results_tree_ids, monkeypatch):
    results = results_id()
    scripts = scripts_id()
    if results_tree_ids.get("max_age") != [results, scripts]:  # pragma: no cover
        results_tree_ids["max_age"] = [results, scripts]
        monkeypatch.setattr(sys, "argv", ["cmd"])
        parse_max_age_results.main()
    yield


@pytest.fixture
def parse_max_age_link_util_fixture(results_tree_ids, monkeypatch):
    csv_name_pattern_fmt = pc.CSV_NAME_PATTERN_FMT
    csv_ext_filter = pc.CSV_EXT_FILTER
    results = results_id()
    scripts = scripts_id()
    if results_tree_ids.get("max_age_lu") != [results, scripts] or not os.path.exists(
        parse_max_age_link_util.CSV_NAME
    ):  # pragma: no cover
        results_tree_ids["max_age_lu"] = [results, scripts]
        monkeypatch.setattr(
            sys, "argv", ["cmd", "209", "209,205", "205,202", "205,290"]
        )
        parse_max_age_link_util.main()
    yield
    pc.CSV_NAME_PATTERN_FMT = csv_name_pattern_fmt
    pc.CSV_EXT_FILTER = csv_ext_filter


def test_plot_build_sizes(monkeypatch):
    # libertine font in ACM style causes problems when running in tox/pytest
    monkeypatch.setattr(sys, "argv", ["cmd", "-s", "mlenders_usenix.mplstyle"])
    plot_build_sizes.main()


def test_plot_done(monkeypatch):
    # libertine font in ACM style causes problems when running in tox/pytest
    monkeypatch.setattr(sys, "argv", ["cmd", "-s", "mlenders_usenix.mplstyle"])
    plot_done.main()


def test_plot_baseline(baseline_results, monkeypatch, parse_baseline_fixture):
    # libertine font in ACM style causes problems when running in tox/pytest
    monkeypatch.setattr(sys, "argv", ["cmd", "-s", "mlenders_usenix.mplstyle"])
    plot_baseline.main()


def test_plot_baseline_trans(baseline_results, monkeypatch, parse_baseline_fixture):
    # libertine font in ACM style causes problems when running in tox/pytest
    monkeypatch.setattr(sys, "argv", ["cmd", "-s", "mlenders_usenix.mplstyle"])
    plot_baseline_trans.main()


def test_plot_comp_cdf(monkeypatch, parse_comp_fixture):
    # libertine font in ACM style causes problems when running in tox/pytest
    monkeypatch.setattr(sys, "argv", ["cmd", "-s", "mlenders_usenix.mplstyle"])
    plot_comp_cdf.main()


def test_plot_comp_cdf_blockwise(monkeypatch, parse_comp_fixture):
    # libertine font in ACM style causes problems when running in tox/pytest
    monkeypatch.setattr(sys, "argv", ["cmd", "-s", "mlenders_usenix.mplstyle"])
    plot_comp_cdf_blockwise.main()


def test_plot_comp_trans(monkeypatch, parse_comp_fixture):
    # libertine font in ACM style causes problems when running in tox/pytest
    monkeypatch.setattr(sys, "argv", ["cmd", "-s", "mlenders_usenix.mplstyle"])
    plot_comp_trans.main()


def test_plot_max_age_cdf(monkeypatch, parse_max_age_fixture):
    # libertine font in ACM style causes problems when running in tox/pytest
    monkeypatch.setattr(sys, "argv", ["cmd", "-s", "mlenders_usenix.mplstyle"])
    plot_max_age_cdf.main()


def test_plot_max_age_link_util(monkeypatch, parse_max_age_link_util_fixture):
    # libertine font in ACM style causes problems when running in tox/pytest
    monkeypatch.setattr(sys, "argv", ["cmd", "-s", "mlenders_usenix.mplstyle"])
    plot_max_age_link_util.main()


def test_plot_max_age_trans(monkeypatch, parse_max_age_fixture):
    # libertine font in ACM style causes problems when running in tox/pytest
    monkeypatch.setattr(sys, "argv", ["cmd", "-s", "mlenders_usenix.mplstyle"])
    plot_max_age_trans.main()


def test_plot_pkt_sizes(monkeypatch):
    # libertine font in ACM style causes problems when running in tox/pytest
    monkeypatch.setattr(sys, "argv", ["cmd", "-s", "mlenders_usenix.mplstyle"])
    plot_pkt_sizes.main()


def test_plot_pkt_sizes_coap(monkeypatch):
    # libertine font in ACM style causes problems when running in tox/pytest
    monkeypatch.setattr(sys, "argv", ["cmd", "-s", "mlenders_usenix.mplstyle"])
    plot_pkt_sizes_coap.main()


def test_plot_pkt_sizes_slides(monkeypatch):
    # libertine font in ACM style causes problems when running in tox/pytest
    monkeypatch.setattr(sys, "argv", ["cmd", "-s", "mlenders_usenix.mplstyle"])
    plot_pkt_sizes_slides.main()


def test_plot_pkt_sizes_hypo(monkeypatch):
    # libertine font in ACM style causes problems when running in tox/pytest
    monkeypatch.setattr(sys, "argv", ["cmd", "-s", "mlenders_usenix.mplstyle"])
    plot_pkt_sizes_hypo.main()
