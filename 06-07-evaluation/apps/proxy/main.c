/*
 * Copyright (C) 2021 Freie Universität Berlin
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

int main(void)
{
    msg_init_queue(_main_msg_queue, MAIN_QUEUE_SIZE);
    shell_run(NULL, _line_buf, SHELL_DEFAULT_BUFSIZE);
    return 0;
}
