#! /bin/bash
#
# count_names.sh
# Copyright (C) 2023 Martine S. Lenders <m.lenders@fu-berlin.de>
#
# Distributed under terms of the MIT license.
#

PROCS=$(grep -c '^processor' /proc/cpuinfo)
EXCLUDED_DEVICES="(Gateway|AndroidTablet|iPhone|iPad|MyCloudEX2Ultra|NintendoSwitch|PlayStation4|TP-LinkWiFiPlug|UbuntuDesktop|XboxOneX)"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}"  )" >/dev/null 2>&1 && pwd  )"
DATA_DIR="$(readlink -f "${SCRIPT_DIR}/../results")"
DEVICE_MAPPING="${DATA_DIR}/doi-10.1109-SP.2019.00013-iot-data/device_mapping.csv"

export DATA_DIR

ls "${DEVICE_MAPPING}" &> /dev/null || (echo "Need device mapping CSV at ${DEVICE_MAPPING}"; exit 1) || exit 1

parse_pcap() {
    no=$(echo "$1" | cut -d';' -f1 | xargs printf "%05d")
    pcap=$(echo "$1" | cut -d';' -f2)
    dataset=$(echo "$pcap" | cut -d'/' -f1)
    tshark -Y "dns.qry.name" -r "$pcap" -Tfields \
        -e _ws.col."Source" -e _ws.col."Destination" -e dns.qry.name \
        -E aggregator='|' -E separator=';' | sed "s/^/${dataset};/" \
        > "${DATA_DIR}/names_addr_w_mdns/${no}.csv"
}

export -f parse_pcap

mkdir -p "${DATA_DIR}/names_addr_w_mdns"
find ${DATA_DIR}/{yourthings,iotfinder,moniotr} -name "*.pcap" -o -name "eth1-*" | nl -s';' | \
    parallel -j"${PROCS}" parse_pcap
cat "${DATA_DIR}/names_addr_w_mdns/"[0-9][0-9][0-9][0-9][0-9].csv > "${DATA_DIR}/names_addr_w_mdns.csv"
echo -n "All devices: "
cut -d';' -f4 "${DATA_DIR}/names_addr_w_mdns.csv" | tr '|' '\n' | tr '[:upper:]' '[:lower:]' | sort -u | wc -l

INCLUDED_ADDRS=$(
    awk -F, '$1 !~ /'"\<${EXCLUDED_DEVICES}"'\>/ {print $2}' "${DEVICE_MAPPING}" | \
    tr '\n' '|' | sed -e 's/|$//' -e 's/^.*$/(\0)/'
)
awk -F';' \
    '$1 ~ /moniotr/ || $2 ~ /^'"${INCLUDED_ADDRS}"'$/ || $3 ~ /^'"${INCLUDED_ADDRS}"'$/ {print tolower($4)}' \
    "${DATA_DIR}/names_addr_w_mdns.csv" > "${DATA_DIR}/names_w_mdns_filtered.csv"
echo -n "w/o excluded devices: "
tr '|' '\n' < "${DATA_DIR}/names_w_mdns_filtered.csv" | sort -u | wc -l
