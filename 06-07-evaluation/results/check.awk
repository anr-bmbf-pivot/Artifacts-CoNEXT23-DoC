$3 ~ /\<q\>/ {
    sends[$2]++
}
$3 ~ /\<r\>/ {
    recvs[$2]++
}
$3 ~ /\<x\>/ {
    timeouts[$2]++
}
$0 ~ /gcoap_dns: CoAP request timed out/ {
    timeouts[$2]++
}
END {
    nodes = 0
    for (key in sends) {
        if (!sends[key] || sends[key] < 50 || (sends[key] - recvs[key] - timeouts[key]) != 0 || (timeouts[key] == sends[key])) {
            print FILENAME, key, sends[key], timeouts[key], recvs[key], sends[key] - recvs[key] - timeouts[key]
        }
        nodes++
    }
    if (nodes < 2) {
        print FILENAME, "missing-nodes"
    }
}
