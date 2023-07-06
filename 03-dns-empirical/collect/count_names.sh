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

zawk() {
    if echo "$2" | grep -q ".csv.gz$"; then
        zcat "$2" | awk -F, "$1"
    else
        awk -F, "$1" "$2"
    fi
}

echo -n "All names: "
zawk 'NR > 1 {print tolower($14)}' "$1" | sort -u | wc -l
echo -n "All names (w/o \".\"): "
zawk 'NR > 1 && $14 != "." {print tolower($14)}' "$1" | sort -u | wc -l
echo -n "All names (w/o MDNS): "
zawk 'NR > 1 && $5 == "Do53" {print tolower($14)}' "$1" | \
    sort -u | wc -l
echo -n "Only in QD and AN sections: "
zawk 'NR > 1 && ($13 != "qd" || $13 == "an") {print tolower($14)}' "$1" | \
    sort -u | wc -l
echo -n "Only in QD and AN sections (w/o MDNS): "
zawk 'NR > 1 && $5 == "Do53" && ($13 == "qd" && $13 != "an") {print tolower($14)}' "$1" | \
    sort -u | wc -l
echo -n "Only QD section of queries: "
zawk 'NR > 1 && $7 == "query" && $13 == "qd" {print tolower($14)}' "$1" | \
    sort -u | wc -l
    echo -n "Only QD section of queries (w/o MDNS): "
zawk 'NR > 1 && $5 == "Do53" && $7 == "query" && $13 == "qd" {print tolower($14)}' "$1" | \
    sort -u | wc -l
