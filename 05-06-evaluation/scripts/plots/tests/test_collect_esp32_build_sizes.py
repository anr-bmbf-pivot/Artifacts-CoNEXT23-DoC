# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring,missing-class-docstring
# pylint: disable=missing-function-docstring

from .. import collect_esp32_build_sizes

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2023 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


def test_main(mocker):
    base_path = collect_esp32_build_sizes.BASE_PATH
    mocker.patch("riotctrl.ctrl.RIOTCtrl.make_run")
    mocker.patch("subprocess.run")
    mocker.patch("subprocess.check_call")
    mocker.patch(
        "subprocess.check_output",
        return_value=f"""
3ffb2468 00000330 b _addrs_out	{base_path}/apps/requester/main.c:129
3ffb2798 00000080 b _async_dns_buf	{base_path}/apps/requester/main.c:128
400d02e4 0000004c t _coap_cb	{base_path}/apps/requester/main.c:301
3ffb4198 00001188 b _coap_pkts	{base_path}/apps/requester/main.c:123
3ffb2818 00001980 b _dns_bufs	{base_path}/apps/requester/main.c:127
3ffb245e 00000002 b _id	{base_path}/apps/requester/main.c:149
400d0060 000000ba t _init_dns	{base_path}/apps/requester/main.c:442
3ffb5320 00000080 b _line_buf	{base_path}/apps/requester/main.c:120
400d0170 00000024 T main	{base_path}/apps/requester/main.c:1061
3ffb53a0 00000040 b _main_msg_queue	{base_path}/apps/requester/main.c:119
400d012c 00000032 T _parse_af	{base_path}/apps/requester/main.c:655
400d01d8 0000002a T _print_addr	{base_path}/apps/requester/main.c:183
400d0024 0000000d t _proxy	{base_path}/apps/requester/main.c:529
400d04c0 00000030 t _query	{base_path}/apps/requester/main.c:797
400d0358 00000164 t _query2$constprop$8	{base_path}/apps/requester/main.c:762
400d052c 00000158 t _query_bulk	{base_path}/apps/requester/main.c:832
3ffb0f40 000014b8 b _req_ctxs	{base_path}/apps/requester/main.c:151
3ffb245c 00000002 b _req_time_count	{base_path}/apps/requester/main.c:149
3ffb23f8 00000064 b _req_times	{base_path}/apps/requester/main.c:150
3f4003e0 0000003c d _shell_commands	{base_path}/apps/requester/main.c:152
3ffb2464 00000004 b _sock	{base_path}/apps/requester/main.c:135
3ffb0e78 000000c8 b sock$7230	{base_path}/apps/requester/main.c:449
400d0218 000000c4 t _timeout_cb	{base_path}/apps/requester/main.c:337
400d0198 00000038 T ts_printf	{base_path}/apps/requester/main.c:1077
3ffb2460 00000004 b _ts_printf_mutex	{base_path}/apps/requester/main.c:148
400d069c 000000fe t _udp_cb	/some/where/else/apps/requester/main.c:249
400d069c 000000fe t _udp_cb	{base_path}/apps/requester/main.c:249
""".encode(
            "ascii"
        ),
    )
    collect_esp32_build_sizes.main()
