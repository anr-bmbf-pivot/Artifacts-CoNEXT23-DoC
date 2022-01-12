#!/bin/bash
#
# Copyright (C) 2022 Martine Lenders <mail@martine-lenders.eu>
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}"  )" >/dev/null 2>&1 && pwd  )"

${SCRIPT_DIR}/plot_load.py
${SCRIPT_DIR}/plot_load_cdf.py
${SCRIPT_DIR}/plot_load_cdf_blockwise.py
${SCRIPT_DIR}/plot_proxy_cdf.py
${SCRIPT_DIR}/plot_pkt_sizes.py
${SCRIPT_DIR}/plot_proxy_trans.py
