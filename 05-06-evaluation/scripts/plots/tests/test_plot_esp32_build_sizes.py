# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring,missing-class-docstring
# pylint: disable=missing-function-docstring

import os.path
import sys

from .. import plot_esp32_build_sizes

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2023 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


def test_main(mocker, monkeypatch):
    # libertine font in ACM style causes problems when running in tox/pytest
    monkeypatch.setattr(sys, "argv", ["cmd", "-s", "mlenders_simple.mplstyle"])
    monkeypatch.setattr(os.path, "exists", lambda *args, **kwargs: False)
    mocker.patch("matplotlib.pyplot.savefig", lambda *args, **kwargs: None)
    plot_esp32_build_sizes.main()
