#! /bin/sh
#
# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.
#

if [ $# -le 1 ]; then
    echo "usage: $0 <dotfile> [<output_type>]"
fi

TYPE=${2:-svg}

dot -Grankdir="LR" -Nshape="none" -Earrowhead=none -T"${TYPE}" -o "${1%dot}.${TYPE}" "${1}"
