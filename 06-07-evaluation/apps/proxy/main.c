/*
 * Copyright (C) 2021-22 Freie Universität Berlin
 *
 * This file is subject to the terms and conditions of the GNU Lesser
 * General Public License v2.1. See the file LICENSE in the top level
 * directory for more details.
 */

/**
 * @{
 *
 * @file
 * @author  Martine S. Lenders <m.lenders@fu-berlin.de>
 */

#include <stdarg.h>
#include <stdio.h>

#include "msg.h"
#include "mutex.h"
#include "net/netif.h"
#include "shell.h"

#define MAIN_QUEUE_SIZE     (8)

static msg_t _main_msg_queue[MAIN_QUEUE_SIZE];
static char _line_buf[SHELL_DEFAULT_BUFSIZE];
static mutex_t _ts_printf_mutex = MUTEX_INIT;

int ts_printf(const char *format, ...)
{
    int res;
    va_list args;
    va_start(args, format);

    mutex_lock(&_ts_printf_mutex);
    res = vprintf(format, args);
    mutex_unlock(&_ts_printf_mutex);
    va_end(args);
    return res;
}

#if IS_USED(MODULE_L2FILTER_WHITELIST)
#include WHITELIST_NAME

extern int _gnrc_netif_config(int argc, char **argv);
#endif

int _update_l2filter(void)
{
#if IS_USED(MODULE_L2FILTER_WHITELIST)
    static const char *whitelist[] = L2_FILTER_WHITE_LIST;

    for (unsigned i = 0; i < ARRAY_SIZE(whitelist); i++) {
        netif_t *netif = netif_iter(NULL);
        char netif_name[CONFIG_NETIF_NAMELENMAX];

        if (netif_get_name(netif, netif_name) == 0) {
            return 1;
        }
        const char *args[] = {
            "ifconfig",
            netif_name,
            "l2filter",
            "add",
            whitelist[i],
        };

        if (_gnrc_netif_config(ARRAY_SIZE(args), (char **)args)) {
            return 1;
        }
        puts(whitelist[i]);
    }
#endif
    return 0;
}

int main(void)
{
    if (_update_l2filter()) {
        puts("Error updating l2white list");
    }
    msg_init_queue(_main_msg_queue, MAIN_QUEUE_SIZE);
    shell_run(NULL, _line_buf, SHELL_DEFAULT_BUFSIZE);
    return 0;
}
