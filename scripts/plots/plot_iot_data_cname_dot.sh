#! /bin/sh
#
# Copyright (C) 2022 Martine S. Lenders <m.lenders@fu-berlin.de>
#
# Distributed under terms of the MIT license.
#

if [ $# -le 1 ]; then
    echo "usage: $0 <dotfile> [<output_type>]"
fi

TYPE=${2:-svg}

dot -Grankdir="LR" -Nshape="none" -Earrowhead=none -T"${TYPE}" -o "${$1%dot}.${TYPE}" "${1}"
