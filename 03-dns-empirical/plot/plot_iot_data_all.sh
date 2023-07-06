#! /bin/bash
#
# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}"  )" >/dev/null 2>&1 && pwd  )"

IOT_DATA_SRCS=(
    "${SCRIPT_DIR}/../results/doi-10.1109-EuroSP48549.2020.00037-iot-data.csv"
    "${SCRIPT_DIR}/../results/doi-10.1109-SP.2019.00013-iot-data.csv"
    "${SCRIPT_DIR}/../results/doi-10.1145-3355369.3355577-iot-data.tgz.csv"
)
IXP_DATA_SRCS=(
    "${SCRIPT_DIR}/../results/dns_packets_ixp_2022_week.csv.gz"
)

plot() {
    echo "$*"
    (ulimit -v 30000000; time "$@")
}

any_ixp() {
    for data_src in "$@"; do
        if [[ " ${IXP_DATA_SRCS[*]} " == *" ${data_src} "* ]]; then
            return 0
        fi
    done
    return 1
}

plot_all() {
    plot "${SCRIPT_DIR}"/plot_iot_data_name_lens.py "$@" || exit 1
    plot "${SCRIPT_DIR}"/plot_iot_data_rr.py "$@" || exit 1
    if ! any_ixp "$@"; then
        plot "${SCRIPT_DIR}"/plot_iot_data_cname.py "$@" || exit 1
    fi
    plot "${SCRIPT_DIR}"/plot_iot_data_resp_lens.py "$@" || exit 1
    plot "${SCRIPT_DIR}"/plot_iot_data_sec_counts.py "$@" || exit 1
}

DONE=""

for data_src in "${IOT_DATA_SRCS[@]}"; do
    plot_all "${data_src}"
done

for data_src1 in "${IOT_DATA_SRCS[@]}"; do
    for data_src2 in "${IOT_DATA_SRCS[@]}"; do
        if [ "${data_src1}" = "${data_src2}" ]; then
            continue
        fi
        if echo -en "${DONE}" | grep -q "^${data_src2}:${data_src1}$"; then
            continue
        fi
        plot_all "${data_src1}" "${data_src2}"
        DONE=$"${DONE}${data_src1}:${data_src2}\n"
    done
done

plot_all "${IOT_DATA_SRCS[@]}"
plot_all "${IXP_DATA_SRCS[@]}"
