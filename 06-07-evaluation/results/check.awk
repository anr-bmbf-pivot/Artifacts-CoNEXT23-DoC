$3 ~ /\<q\>/ {
    sends[$2]++
}
$3 ~ /\<r\>/ {
    recvs[$2]++
}
$3 ~ /\<x\>/ {
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
    if (FILENAME ~ /-24-ieee802154-/ && nodes < 12) {
        print FILENAME, "missing-nodes"
    }
    else if (nodes < 2) {
        print FILENAME, "missing-nodes"
    }
}
