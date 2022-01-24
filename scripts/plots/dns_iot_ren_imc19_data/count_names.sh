#! /bin/bash
#
# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

if [ $# -lt 1 ]; then
    echo "usage: $0 <csv file>" >&2
    exit 1
fi

echo -n "All names: "
awk -F, 'NR > 1 {print tolower($12)}' "$1" | sort -u | wc -l
echo -n "All names (w/o \".\"): "
awk -F, 'NR > 1 && $12 != "." {print tolower($12)}' "$1" | sort -u | wc -l
echo -n "All names (w/o MDNS): "
awk -F, 'NR > 1 && $3 == "Do53" {print tolower($12)}' "$1" | \
    sort -u | wc -l
echo -n "Only in QD and AN sections: "
awk -F, 'NR > 1 && ($11 != "qd" || $11 == "an") {print tolower($12)}' "$1" | \
    sort -u | wc -l
echo -n "Only in QD and AN sections (w/o MDNS): "
awk -F, 'NR > 1 && $3 == "Do53" && ($11 == "qd" && $11 != "an") {print tolower($12)}' "$1" | \
    sort -u | wc -l
echo -n "Only QD section of queries: "
awk -F, 'NR > 1 && $5 == "query" && $11 == "qd" {print tolower($12)}' "$1" | \
    sort -u | wc -l
    echo -n "Only QD section of queries (w/o MDNS): "
awk -F, 'NR > 1 && $3 == "Do53" && $5 == "query" && $11 == "qd" {print tolower($12)}' "$1" | \
    sort -u | wc -l
