#!/bin/bash
#
# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}"  )" >/dev/null 2>&1 && pwd  )"

"${SCRIPT_DIR}"/plot_comp_cdf.py
"${SCRIPT_DIR}"/plot_comp_cdf_blockwise.py
"${SCRIPT_DIR}"/plot_pkt_sizes.py
"${SCRIPT_DIR}"/plot_pkt_sizes_coap.py
"${SCRIPT_DIR}"/plot_pkt_sizes_quic.py
"${SCRIPT_DIR}"/plot_build_sizes.py
"${SCRIPT_DIR}"/plot_esp32_build_sizes.py
"${SCRIPT_DIR}"/plot_max_age_trans.py
"${SCRIPT_DIR}"/plot_max_age_link_util.py
