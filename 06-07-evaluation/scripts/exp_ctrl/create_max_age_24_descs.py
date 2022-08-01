#! /usr/bin/env python3

# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring,missing-function-docstring

try:  # pragma: no cover
    from . import create_proxy_24_descs
    from . import create_max_age_descs
except ImportError:
    import create_proxy_24_descs
    import create_max_age_descs

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


def main():
    create_proxy_24_descs.set_network()
    create_max_age_descs.main(
        prefix="doc-eval-max_age-24", tmux_session="doc-eval-max_age"
    )


if __name__ == "__main__":
    main()  # pragma: no cover
