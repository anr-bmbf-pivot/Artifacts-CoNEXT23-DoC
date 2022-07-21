#!/bin/bash
#
# Copyright (C) 2022 Freie Universität berlin
#
# Distributed under terms of the MIT license.

# Author: Marcin Nawrocki <marcin.nawrocki@fu-berlin.de>

# config
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}"  )" >/dev/null 2>&1 && pwd  )"
DATA_DIR=$(realpath -L "${SCRIPT_DIR}")
export DATA_DIR

LOGDIR="${LOGDIR:-/mnt/data01/tcpdumpFiles}"

tasks="${DATA_DIR}/.tasks.txt"
TS_START="${TS_START:-2022-01-10}"
TS_END="${TS_END:-2022-01-17}"
output="${DATA_DIR}/dns_packets_ixp_2022_week.csv.gz"

filterDNS(){

    # TODO WARNING: ALL ERRORS SUPPRESSED!!!
    # putting DNS query name at the end as it could contain the seperator
    sample="$1"
    sflowtool -t -r "${sample}" 2>/dev/null |\
        tcprewrite --enet-vlan=del --infile=- --outfile=- 2>/dev/null |\
        tcpdump -q -nr - -w - "udp and port 53 and not icmp" 2>/dev/null |\
        tshark -nr - -Y "dns" -T fields \
            -e _ws.col.Time -t ud \
            \
            -e ip.version \
            \
            -e udp.length \
            \
            -e dns.flags.opcode \
            -e dns.flags.response \
            -e dns.flags.authoritative \
            -e dns.flags.rcode \
            -e dns.count.queries \
            -e dns.count.answers \
            -e dns.count.auth_rr \
            -e dns.count.add_rr \
            -e dns.qry.class \
            -e dns.qry.type \
            -e dns.qry.name.len \
            -e dns.resp.class \
            -e dns.resp.type \
            -e dns.resp.len \
            \
            -E separator=\| 2>/dev/null
}
export -f filterDNS

# find all files in timerange, create sorted list of jobs for workers
find "${LOGDIR}" -newermt "${TS_START}" ! -newermt "${TS_END}" -name '*.pcap' |\
    sort > "${tasks}"

# start workerpool, gzip output since it might be large...
parallel --bar -j 12 -k filterDNS < "${tasks}" | gzip > "${output}"
