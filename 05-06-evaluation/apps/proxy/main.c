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
#include "net/gcoap/forward_proxy.h"
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

static int _proxy(int argc, char **argv)
{
    if (argc < 2) {
        static char proxy[CONFIG_GCOAP_FORWARD_PROXY_UPSTREAM_URI_MAX];
        int res;

        if ((res = gcoap_forward_proxy_upstream_get(proxy, sizeof(proxy))) < 0) {
            errno = -res;
            perror("Unable to get URI");
            return 1;
        }
        else {
            if (res > 0) {
                puts(proxy);
                return 0;
            }
            else {
                 printf("usage: %s [<proxy URI>|-]\n", argv[0]);
                return 1;
            }
            return 0;
        }
    }
    else if (strcmp(argv[1], "clear") == 0) {
        gcoap_forward_proxy_upstream_set(NULL);
    }
    else {
        int res = gcoap_forward_proxy_upstream_set(argv[1]);

        switch (res) {
            case -EINVAL:
                puts("Unable to store proxy URI.");
                break;
            case -ENOTSUP:
                puts("Proxying not supported");
                break;
            default:
                printf("Configured proxy %.*s\n", res, argv[1]);
                break;
        }
    }
    return 0;
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

static const shell_command_t _shell_commands[] = {
    { "proxy", "Sets upstream proxy URI for proxy", _proxy},
    { NULL, NULL, NULL }
};

int main(void)
{
    if (_update_l2filter()) {
        puts("Error updating l2white list");
    }
    msg_init_queue(_main_msg_queue, MAIN_QUEUE_SIZE);
    shell_run(_shell_commands, _line_buf, SHELL_DEFAULT_BUFSIZE);
    return 0;
}
