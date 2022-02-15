#! /bin/bash
#
# plot_iot_data_all.sh
# Copyright (C) 2022 Martine S. Lenders <m.lenders@fu-berlin.de>
#
# Distributed under terms of the MIT license.
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}"  )" >/dev/null 2>&1 && pwd  )"

IOT_DATA_SRCS=(
    "${SCRIPT_DIR}/../../doi-10.1109-EuroSP48549.2020.00037-iot-data.bkp.csv.gz"
    "${SCRIPT_DIR}/../../doi-10.1109-SP.2019.00013-iot-data.bkp.csv.gz"
    "${SCRIPT_DIR}/../../doi-10.1145-3355369.3355577-iot-data.tgz.bkp.csv"
)
IXP_DATA_SRCS=(
    "${SCRIPT_DIR}/../../results/dns_packets_ixp_2022_week.csv.gz"
)

plot() {
    echo "$*"
    (ulimit -v 30000000; time $*)
}

plot_all() {
    plot ${SCRIPT_DIR}/plot_iot_data_name_lens.py $*
    plot ${SCRIPT_DIR}/plot_iot_data_rr.py $*
    if ! [[ "$*" == *"${IXP_DATA_SRCS}"* ]]; then
        plot ${SCRIPT_DIR}/plot_iot_data_cname.py $*
    fi
    plot ${SCRIPT_DIR}/plot_iot_data_resp_lens.py $*
    plot ${SCRIPT_DIR}/plot_iot_data_sec_counts.py $*
}

DONE=""

for data_src in ${IOT_DATA_SRCS[@]}; do
    plot_all "${data_src}"
done

for data_src1 in ${IOT_DATA_SRCS[@]}; do
    for data_src2 in ${IOT_DATA_SRCS[@]}; do
        if [ "${data_src1}" = "${data_src2}" ]; then
            continue
        fi
        if echo -en "${DONE}" | grep -q "^${data_src2}:${data_src1}$"; then
            continue
        fi
        plot_all ${data_src1} ${data_src2}
        DONE=$"${DONE}${data_src1}:${data_src2}\n"
    done
done

plot_all ${IOT_DATA_SRCS[@]}
plot_all ${IXP_DATA_SRCS[@]}
