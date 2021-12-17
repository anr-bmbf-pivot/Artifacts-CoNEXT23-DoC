/*
 * main.c
 * Copyright (C) 2021 Martine Lenders <mail@martine-lenders.eu>
 *
 * Distributed under terms of the MIT license.
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
