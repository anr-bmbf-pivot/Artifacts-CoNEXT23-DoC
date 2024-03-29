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

#include <errno.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include "byteorder.h"
#include "event/callback.h"
#include "event/timeout.h"
#include "event/thread.h"
#include "msg.h"
#include "mutex.h"
#include "net/af.h"
#include "net/coap.h"
#include "net/credman.h"
#include "net/dns/cache.h"
#include "net/dns/msg.h"
#include "net/gcoap/dns.h"
#include "net/ipv4/addr.h"
#include "net/ipv6/addr.h"
#include "net/sock/async/event.h"
#include "net/sock/dns.h"
#if IS_USED(MODULE_SOCK_DTLS)
#include "net/sock/dtls.h"
#include "net/sock/dodtls.h"
#endif  /* IS_USED(MODULE_SOCK_DTLS) */
#include "net/sock/util.h"
#include "random.h"
#include "shell.h"
#include "xtimer.h"
#include "ztimer.h"

#if IS_USED(MODULE_GCOAP_DNS_OSCORE)
#include "oscore_native/crypto.h"

static int _userctx(int argc, char **argv);
#endif

#define ENABLE_DEBUG 0
#include "debug.h"

#define MAIN_QUEUE_SIZE     (8)
#define DNS_TRANSPORT_UDP   0U
#define DNS_TRANSPORT_DTLS  1U
#define DNS_TRANSPORT_COAP  2U

#define PSK_ID_LEN          32U
#define PSK_LEN             32U
#define HOSTNAME_LEN        32U
#ifdef DNS_TRANSPORT_SYNC
# define REQ_MAX_NUM        1U
#else   /* DNS_TRANSPORT_SYNC */
#if IS_USED(MODULE_GNRC_SIXLOWPAN_BORDER_ROUTER_DEFAULT) || IS_USED(MODULE_NIMBLE)
# ifdef MODULE_GCOAP
#  if IS_USED(MODULE_NIMBLE)
#   define REQ_MAX_NUM      20U
#  else
#   define REQ_MAX_NUM      32U
#  endif
# else
#  if IS_USED(MODULE_NIMBLE)
#    define REQ_MAX_NUM     43U
#  else
#    define REQ_MAX_NUM     44U
#  endif
# endif
#else   /* IS_USED(MODULE_GNRC_SIXLOWPAN_BORDER_ROUTER_DEFAULT) */
# define REQ_MAX_NUM        51U
#endif  /* IS_USED(MODULE_GNRC_SIXLOWPAN_BORDER_ROUTER_DEFAULT) */
#endif  /* DNS_TRANSPORT_SYNC */

/* not defined if no DTLS is there, but for simplicity we use these values */
#ifndef CONFIG_SOCK_DODTLS_TIMEOUT_MS
#define CONFIG_SOCK_DODTLS_TIMEOUT_MS   (CONFIG_COAP_ACK_TIMEOUT_MS)
#endif
#ifndef DNS_UDP_RETRIES
#define DNS_UDP_RETRIES                 (CONFIG_COAP_MAX_RETRANSMIT)
#endif
#ifndef CONFIG_SOCK_DODTLS_RETRIES
#define CONFIG_SOCK_DODTLS_RETRIES      (DNS_UDP_RETRIES)
#endif

typedef struct {
    char hostname[HOSTNAME_LEN];
    gcoap_dns_ctx_t ctx;
    uint8_t retries;
    event_timeout_t timeout;
    event_callback_t event;
} _req_ctx_t;

#if IS_USED(GCOAP_APP)
extern void server_init(void);
extern int gcoap_cli_cmd(int argc, char **argv);
#endif

int ts_printf(const char *format, ...);

static int _init_dns(int argc, char **argv);
static int _proxy(int argc, char **argv);
static int _query(int argc, char **argv);
static int _query_bulk(int argc, char **argv);
static void _coap_cb(gcoap_dns_ctx_t *ctx);

static msg_t _main_msg_queue[MAIN_QUEUE_SIZE];
static char _line_buf[SHELL_DEFAULT_BUFSIZE];
static char _psk_id[PSK_ID_LEN];
static char _psk[PSK_LEN];
static coap_pkt_t _coap_pkts[REQ_MAX_NUM];
#if IS_USED(MODULE_GCOAP_DNS)
static uint8_t _coap_bufs[REQ_MAX_NUM][CONFIG_GCOAP_DNS_PDU_BUF_SIZE];
#endif
static uint8_t _dns_bufs[REQ_MAX_NUM][CONFIG_DNS_MSG_LEN];
static uint8_t _async_dns_buf[CONFIG_DNS_MSG_LEN];
static uint8_t _addrs_out[REQ_MAX_NUM][sizeof(ipv6_addr_t)];
static union {
    sock_udp_t *udp;
#if IS_USED(MODULE_SOCK_DTLS)
    sock_dtls_t *dtls;
#endif
} _sock;
#if IS_USED(MODULE_SOCK_DTLS)
static sock_dtls_session_t *_dtls_server_session;
#endif
static credman_credential_t _credential = {
    .type = CREDMAN_TYPE_PSK,
    .params = {
        .psk = {
            .id = { .s = _psk_id, .len = 0U, },
            .key = { .s = _psk, .len = 0U, },
        }
    },
};
static mutex_t _ts_printf_mutex = MUTEX_INIT;
static uint16_t _id, _req_time_count = 0;
static uint16_t _req_times[QUERY_COUNT];
static _req_ctx_t _req_ctxs[REQ_MAX_NUM];
static const shell_command_t _shell_commands[] = {
    { "init", "Sets up the DNS server", _init_dns},
    { "proxy", "Sets proxy URI for DNS queries", _proxy},
    { "query", "Sends DNS query for a hostname", _query},
    { "query_bulk", "Sends multiple DNS query for a group of hostnames",
      _query_bulk },
#if IS_USED(MODULE_GCOAP_DNS_OSCORE)
    { "userctx",  "Reset the user context with new key material", _userctx },
#endif
#if IS_USED(GCOAP_APP)
    { "coap", "CoAP example client", gcoap_cli_cmd },
#endif
    { NULL, NULL, NULL }
};

static inline bool _req_ctx_is_empty(const _req_ctx_t *ctx)
{
    return ctx->ctx.family == 0;
}

static inline _req_ctx_t *_req_ctx_get_by_id(uint16_t id)
{
    return &_req_ctxs[id % REQ_MAX_NUM];
}

static void _free_req_ctx(_req_ctx_t *ctx)
{
    event_timeout_clear(&ctx->timeout);
    ctx->ctx.family = 0;
}

int _print_addr(const char *hostname, int addr_len)
{
    switch (addr_len) {
        case sizeof(ipv4_addr_t):
        case sizeof(ipv6_addr_t):
            ts_printf("r;%.*s\n", 5, hostname);
            break;
        default:
            ts_printf("%s resolved to unexpected address format\n", hostname);
            return 1;
    }
    return 0;
}

static int _parse_response(uint8_t *resp, size_t resp_len)
{
    _req_ctx_t *ctx;
    uint32_t ttl;
    uint16_t id;

    if (resp_len < 2U) {
        puts("Response way too short");
    }
    id = byteorder_bebuftohs(resp);
    if (resp_len <= (sizeof(dns_hdr_t) + 7)) {
        printf("Response to query %u too short\n", id);
        return -1;
    }
    ctx = _req_ctx_get_by_id(id);
    if (_req_ctx_is_empty(ctx)) {
        ts_printf("d;%u\n", id);
        return -1;
    }
    if ((ctx->ctx.res = dns_msg_parse_reply(resp, resp_len, ctx->ctx.family,
                                            ctx->ctx.addr_out, &ttl)) < 0) {
        printf("Unable to resolve query for %s: %s", ctx->hostname, strerror(-ctx->ctx.res));
        return -1;
    }
    ts_printf("R;%u\n", id);
    _print_addr(ctx->hostname, ctx->ctx.res);
    if (ctx->ctx.res > 0) {
        dns_cache_add(ctx->hostname, ctx->ctx.addr_out, ctx->ctx.res, ttl);
    }
    _free_req_ctx(ctx);
    return 0;
}

static uint32_t _now_ms(void)
{
    if (IS_USED(MODULE_ZTIMER_MSEC)) {
        return ztimer_now(ZTIMER_MSEC);
    }
    else if (IS_USED(MODULE_ZTIMER_USEC)) {
        return ztimer_now(ZTIMER_USEC);
    }
    else if (IS_USED(MODULE_XTIMER)) {
        return xtimer_now_usec() / US_PER_MS;
    }
    else {
        puts("No timer available, add xtimer, ztimer_msec, or ztimer_usec to "
             "your application");
        assert(false);
    }
    return 0U;
}

static void _udp_cb(sock_udp_t *sock, sock_async_flags_t flags, void *arg)
{
    (void)arg;
    DEBUG("Received UDP event 0x%04x (expecting 0x%04x)\n", flags,
          SOCK_ASYNC_MSG_RECV);
    if (flags & SOCK_ASYNC_MSG_RECV) {
        int res = -1;

        while (res != 0) {
            if ((res = sock_udp_recv(sock, _async_dns_buf,
                                     sizeof(_async_dns_buf), 0, NULL)) < 0) {
                if (res != -EAGAIN) {
                    errno = -res;
                    perror("e");
                }
                return;
            }
            res = _parse_response(_async_dns_buf, res);
        }
    }
}

#if IS_USED(MODULE_SOCK_DTLS)
static void _dtls_cb(sock_dtls_t *sock, sock_async_flags_t flags, void *arg)
{
    (void)arg;
    DEBUG("Received DTLS event 0x%04x (expecting 0x%04x)\n", flags,
          SOCK_ASYNC_MSG_RECV);
    if (flags & SOCK_ASYNC_MSG_RECV) {
        int res = -1;

        assert(_dtls_server_session);
        while (res != 0) {
            if ((res = sock_dtls_recv(sock, _dtls_server_session,
                                      _async_dns_buf,
                                      sizeof(_async_dns_buf), 0)) < 0) {
                if (res != -EAGAIN) {
                    errno = -res;
                    perror("e");
                }
                return;
            }
            res = _parse_response(_async_dns_buf, res);
        }
    }
    if (flags & ~(SOCK_ASYNC_MSG_RECV | SOCK_ASYNC_MSG_SENT)) {
        printf("Unexpected sock event %04x\n",
               flags & ~(SOCK_ASYNC_MSG_RECV | SOCK_ASYNC_MSG_SENT));
    }
}
#endif

static void _coap_cb(gcoap_dns_ctx_t *coap_ctx)
{
    _req_ctx_t *ctx = container_of(coap_ctx, _req_ctx_t, ctx);
    if (ctx->ctx.res < 0) {
        printf("Unable to resolve query for %s: %s\n",
               ctx->hostname, strerror(-ctx->ctx.res));
    }
    else {
        ts_printf("R;%u\n", coap_ctx->pkt->hdr->id);
        _print_addr(ctx->hostname, ctx->ctx.res);
    }
    _free_req_ctx(ctx);
}

static void _set_timeout(_req_ctx_t *ctx, uint32_t timeout)
{
    event_timeout_ztimer_init(&ctx->timeout, ZTIMER_MSEC, EVENT_PRIO_LOWEST,
                              &ctx->event.super);
    event_timeout_set(&ctx->timeout, timeout);
}

static uint32_t _generate_timeout(_req_ctx_t *ctx)
{
    /* mimic CoAP's random backoff for fair comparison */
    unsigned i = CONFIG_SOCK_DODTLS_RETRIES - ctx->retries;
    uint32_t base = ((uint32_t)CONFIG_SOCK_DODTLS_TIMEOUT_MS) << i;

#if CONFIG_COAP_RANDOM_FACTOR_1000 > 1000
    uint32_t end = ((CONFIG_SOCK_DODTLS_TIMEOUT_MS * CONFIG_COAP_RANDOM_FACTOR_1000) / 1000) << i;

    return random_uint32_range(base, end);
#else
    return base;
#endif
}

static void _timeout_cb(void *arg)
{
    _req_ctx_t *ctx = arg;
    uint32_t timeout;
    int res;

    if (_req_ctx_is_empty(ctx)) {
        return;
    }
    if (ctx->retries == 0) {
        ts_printf("x;%u\n", byteorder_bebuftohs(ctx->ctx.dns_buf));
        _free_req_ctx(ctx);
        return;
    }
    ctx->retries--;
    timeout = _generate_timeout(ctx);
    switch (DNS_TRANSPORT) {
    case DNS_TRANSPORT_UDP:
        ts_printf("t;%u\n", byteorder_bebuftohs(ctx->ctx.dns_buf));
        res = sock_udp_send(_sock.udp, ctx->ctx.dns_buf, ctx->ctx.dns_buf_len,
                            NULL);
        if (res <= 0) {
            errno = (res == 0) ? ENOTRECOVERABLE : -res;
            perror("Unable to send request");
            _free_req_ctx(ctx);
            return;
        }
        break;
    case DNS_TRANSPORT_DTLS: {
        uint32_t send_duration, start = _now_ms();

        ts_printf("t;%u\n", byteorder_bebuftohs(ctx->ctx.dns_buf));
#if IS_USED(MODULE_SOCK_DTLS)
        res = sock_dtls_send(_sock.dtls, _dtls_server_session,
                             ctx->ctx.dns_buf, ctx->ctx.dns_buf_len,
                             timeout);
#else
        res = -ENOTSUP;
#endif
        send_duration = _now_ms() - start;
        if (send_duration > timeout) {
            res = -ETIMEDOUT;
        }
        if (res <= 0) {
            errno = (res == 0) ? ENOTRECOVERABLE : -res;
            perror("Unable to send request");
            _free_req_ctx(ctx);
            return;
        }
        timeout -= send_duration;
        break;
    }
    default:
        printf("Unexpected DNS transport %u in timeout\n", DNS_TRANSPORT);
        return;
    }
    _set_timeout(ctx, timeout);
}

static void _init_usage(const char *cmd)
{
    printf("usage: %s <server (URI)> [<cred tag> <PSK ID> <PSK>]\n", cmd);
}

static int _init_creds(int cred_tag, const char *psk_id, const char *psk,
                       credman_credential_t *creds)
{
    if ((creds->tag = cred_tag) == 0) {
        puts("Invalid credential tag");
        return -1;
    }
    if ((creds->params.psk.id.len = strlen(psk_id)) >= PSK_ID_LEN) {
        printf("PSK ID \"%s\" too long (max. %u bytes allowed)\n", psk_id,
               PSK_ID_LEN);
        return -1;
    }
    if ((creds->params.psk.key.len = strlen(psk)) >= PSK_LEN) {
        printf("PSK \"%s\" too long (max. %u bytes allowed)\n", psk,
               PSK_LEN);
        return -1;
    }
    strcpy((char *)creds->params.psk.id.s, psk_id);
    strcpy((char *)creds->params.psk.key.s, psk);
    return 0;
}

static int _init_server_ep(const char *server, uint16_t default_port,
                           sock_udp_ep_t *server_ep)
{
    if (sock_udp_str2ep(server_ep, server) < 0) {
        printf("Unable to parser server address / port pair %s\n", server);
        return 1;
    }
    if (server_ep->port == 0) {
        server_ep->port = default_port;
    }
    if (server_ep->netif == SOCK_ADDR_ANY_NETIF) {
        netif_t *netif = netif_iter(NULL);
        /* we only have one interface so take that one, otherwise
         * TinyDTLS is not able to identify the peer */
        server_ep->netif = netif_get_id(netif);
    }
    return 0;
}

static int _init_dns(int argc, char **argv)
{
    sock_udp_ep_t server_ep = SOCK_IPV6_EP_ANY;
    int res = 0;

    switch (DNS_TRANSPORT) {
    case DNS_TRANSPORT_UDP: {
        static sock_udp_t sock;
        sock_udp_ep_t local = SOCK_IPV6_EP_ANY;

        if (argc < 2) {
            _init_usage(argv[0]);
            return 1;
        }
        if (_init_server_ep(argv[1], SOCK_DNS_PORT, &server_ep)) {
            return 1;
        }
        sock_dns_server = server_ep;
        res = sock_udp_create(&sock, &local, &sock_dns_server, 0);
        if (res < 0) {
            errno = -res;
            perror("Unable to create UDP server socket");
            return 1;
        }
        sock_udp_event_init(&sock, EVENT_PRIO_LOWEST, _udp_cb, NULL);
        _sock.udp = &sock;
        printf("Successfully added DNS server %s\n", argv[1]);
        break;
    }
    case DNS_TRANSPORT_DTLS:
#if IS_USED(MODULE_SOCK_DTLS)
        if (argc < 5) {
            _init_usage(argv[0]);
            return 1;
        }
        if (_init_server_ep(argv[1], SOCK_DODTLS_PORT, &server_ep)) {
            return 1;
        }
        if (_init_creds(atoi(argv[2]), argv[3], argv[4], &_credential) < 0) {
            return 1;
        }
        if ((res = sock_dodtls_set_server(&server_ep, &_credential)) < 0) {
            errno = -res;
            perror("Unable to establish session with server");
            return errno;
        }
        _sock.dtls = sock_dodtls_get_dtls_sock();
        _dtls_server_session = sock_dodtls_get_server_session();
        assert(_sock.dtls && _dtls_server_session);
        sock_dtls_event_init(_sock.dtls, EVENT_PRIO_LOWEST, _dtls_cb, NULL);
        printf("Successfully added DoDTLS server %s (creds: %u, %s, %s)\n",
               argv[1], _credential.tag, (char *)_credential.params.psk.id.s,
               (char *)_credential.params.psk.key.s);
        break;
#else   /* IS_USED(MODULE_SOCK_DTLS) */
        return -ENOTSUP;
#endif  /* IS_USED(MODULE_SOCK_DTLS) */
    case DNS_TRANSPORT_COAP:
        if (argc < 2) {
            _init_usage(argv[0]);
            return 1;
        }
        if (IS_USED(MODULE_GCOAP_DTLS) && (argc > 4) &&
            _init_creds(atoi(argv[2]), argv[3], argv[4], &_credential) < 0) {
            return 1;
        }
        if ((res = gcoap_dns_server_uri_set(argv[1])) < 0) {
            errno = -res;
            perror("Unable to set URI");
            return errno;
        }
        if (IS_USED(MODULE_GCOAP_DTLS) && (argc > 4) && (res = gcoap_dns_cred_add(&_credential))) {
            errno = -res;
            perror("Unable to set DTLS credentials");
            return errno;
        }
        printf("Successfully added URI template %s (creds: %u, %s, %s)\n",
               argv[1], _credential.tag, (char *)_credential.params.psk.id.s,
               (char *)_credential.params.psk.key.s);
        break;
    default:
        printf("Undefined DNS transport %u\n", DNS_TRANSPORT);
        break;
    }
    return 0;
}

static int _proxy(int argc, char **argv)
{
    if (!IS_USED(MODULE_GCOAP_DNS)) {
        puts("Proxying not supported");
        return 1;
    }
    if (argc < 2) {
        static char proxy[CONFIG_GCOAP_DNS_SERVER_URI_LEN];
        int res;

        if ((res = gcoap_dns_server_proxy_get(proxy, sizeof(proxy))) < 0) {
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
        gcoap_dns_server_proxy_reset();
    }
    else {
        int res = gcoap_dns_server_proxy_set(argv[1]);

        switch (res) {
            case -ENOBUFS:
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

static void _query_usage(const char *cmd)
{
    printf("usage: %s <hostname> <family> [<method>]\n", cmd);
}

static _req_ctx_t *_alloc_req_ctx(const char *hostname, int family)
{
    assert(family != 0);
    if ((strlen(hostname) + 1) > HOSTNAME_LEN) {
        printf("%s is too long (maximum allowed length is %u)\n", hostname,
               HOSTNAME_LEN);
        return NULL;
    }

    for (unsigned i = 0; i < REQ_MAX_NUM; i++) {
        _req_ctx_t *ctx = &_req_ctxs[i];

        if (_req_ctx_is_empty(ctx)) {
            strcpy(ctx->hostname, hostname);
            ctx->ctx.sync.cb = _coap_cb;
            ctx->ctx.pkt = &_coap_pkts[i];
#if IS_USED(MODULE_GCOAP_DNS)
            ctx->ctx.pkt->payload = _coap_bufs[i];
#endif
            ctx->ctx.pkt->payload_len = CONFIG_GCOAP_DNS_PDU_BUF_SIZE;
            ctx->ctx.dns_buf = _dns_bufs[i];
            ctx->ctx.dns_buf_len = CONFIG_DNS_MSG_LEN;
            ctx->ctx.addr_out = _addrs_out[i];
            ctx->ctx.family = family;
            return ctx;
        }
    }
    printf("No free request context found for %s\n", hostname);
    return NULL;
}

static _req_ctx_t *_alloc_req_ctx_by_id(const char *hostname, int family,
                                        uint16_t id)
{
    unsigned i = id % REQ_MAX_NUM;
    _req_ctx_t *ctx = _req_ctx_get_by_id(id);

    if (!_req_ctx_is_empty(ctx)) {
        printf("Request context for ID %u is not empty\n", id);
        return NULL;
    }
    strcpy(ctx->hostname, hostname);
    ctx->ctx.sync.cb = _coap_cb;
    ctx->ctx.pkt = &_coap_pkts[i];
#if IS_USED(MODULE_GCOAP_DNS)
    ctx->ctx.pkt->payload = _coap_bufs[i];
#endif
    ctx->ctx.pkt->payload_len = CONFIG_GCOAP_DNS_PDU_BUF_SIZE;
    ctx->ctx.dns_buf = _dns_bufs[i];
    ctx->ctx.dns_buf_len = CONFIG_DNS_MSG_LEN;
    ctx->ctx.addr_out = _addrs_out[i];
    ctx->ctx.family = family;
    return ctx;
}

static uint8_t _parse_method(const char *method_name)
{
    if (strcmp("get", method_name) == 0) {
        return COAP_METHOD_GET;
    }
    else if (strcmp("post", method_name) == 0) {
        return COAP_METHOD_POST;
    }
    else if (strcmp("fetch", method_name) == 0) {
        return COAP_METHOD_FETCH;
    }
    else {
        printf("Unexpected method %s (valid values: get, fetch, and post)\n",
               method_name);
        return COAP_CLASS_REQ;
    }
}

int _parse_af(const char *family_name)
{
    if (strcmp("inet6", family_name) == 0) {
        return AF_INET6;
    }
    else if (strcmp("inet", family_name) == 0) {
        return AF_INET;
    }
    else {
        printf("Unexpected family %s\n", family_name);
        return -1;
    }
}

static int _query_udp(const char *hostname, int family)
{
    _req_ctx_t *ctx;
    int res;
    uint16_t id = _id++;

    ctx = _alloc_req_ctx_by_id(hostname, family, id);
    if (ctx == NULL) {
        return -ENOBUFS;
    }
    event_callback_init(&ctx->event, _timeout_cb, ctx);
    ctx->retries = DNS_UDP_RETRIES;
    ctx->ctx.dns_buf_len = dns_msg_compose_query(ctx->ctx.dns_buf,
                                                 ctx->hostname, id,
                                                 ctx->ctx.family);
    ts_printf("t;%u\n", id);
    res = sock_udp_send(_sock.udp, ctx->ctx.dns_buf, ctx->ctx.dns_buf_len,
                        NULL);
    if (res <= 0) {
        _free_req_ctx(ctx);
        return (res == 0) ? -ENOTRECOVERABLE : res;
    }
    _set_timeout(ctx, _generate_timeout(ctx));
    return res;
}

static int _query_dtls(const char *hostname, int family)
{
    _req_ctx_t *ctx;
    int res;
    uint32_t timeout;
    uint32_t start, send_duration;
    uint16_t id = _id++;

    ctx = _alloc_req_ctx_by_id(hostname, family, id);
    if (ctx == NULL) {
        return -ENOBUFS;
    }
    ctx->retries = CONFIG_SOCK_DODTLS_RETRIES;
    timeout = _generate_timeout(ctx);
    event_callback_init(&ctx->event, _timeout_cb, ctx);
    ctx->ctx.dns_buf_len = dns_msg_compose_query(ctx->ctx.dns_buf,
                                                 ctx->hostname, id,
                                                 ctx->ctx.family);
    start = _now_ms();
    ts_printf("t;%u\n", id);
#if IS_USED(MODULE_SOCK_DTLS)
    res = sock_dtls_send(_sock.dtls, _dtls_server_session,
                         ctx->ctx.dns_buf, ctx->ctx.dns_buf_len,
                         timeout);
#else
    res = -ENOTSUP;
#endif
    send_duration = _now_ms() - start;
    if (send_duration > timeout) {
        res = -ETIMEDOUT;
    }
    if (res <= 0) {
        _free_req_ctx(ctx);
        return (res == 0) ? -ENOTRECOVERABLE : res;
    }
    timeout -= send_duration;
    _set_timeout(ctx, timeout);
    return res;
}

static int _query_coap(const char *hostname, int family, uint8_t method)
{
    _req_ctx_t *ctx;
    int res;

    do {
        ctx = _alloc_req_ctx(hostname, family);
        if (ctx == NULL) {
            return -ENOBUFS;
        }
#if IS_USED(MODULE_GCOAP_DNS_GET) || IS_USED(MODULE_GCOAP_DNS_POST)
        ctx->ctx.flags = method;
#else
        (void)method;
#endif
        if ((res = gcoap_dns_query_async(ctx->hostname, &ctx->ctx)) < 0) {
            if (IS_USED(MODULE_GCOAP_DTLS) && (res == -ENOTCONN)) {
                printf("s;%s\n", ctx->hostname);
            }
            _free_req_ctx(ctx);
        }
        /* try to redo session establishment as long as possible */
    } while (IS_USED(MODULE_GCOAP_DTLS) && (res == -ENOTCONN));
    _id++;
    return res;
}

static int _query2(char *hostname, int family, uint8_t method)
{
    int res;

    ts_printf("q;%.*s\n", 5, hostname);
    switch (DNS_TRANSPORT) {
    case DNS_TRANSPORT_UDP:
        if ((res = _query_udp(hostname, family)) < 0) {
            errno = -res;
            perror("Unable to send request");
            return 1;
        }
        break;
    case DNS_TRANSPORT_DTLS:
        if ((res = _query_dtls(hostname, family)) < 0) {
            errno = -res;
            perror("Unable to send request");
            return 1;
        }
        break;
    case DNS_TRANSPORT_COAP: {
        if ((res = _query_coap(hostname, family, method)) < 0) {
            errno = -res;
            perror("Unable to send request");
            return 1;
        }
        break;
    }
    default:
        printf("Undefined DNS transport %u\n", DNS_TRANSPORT);
        break;
    }
    return 0;
}

static int _query(int argc, char **argv)
{
    int family;
    uint8_t method;

    if (argc < 3) {
        _query_usage(argv[0]);
        return 1;
    }
    if ((family = _parse_af(argv[2])) < 0) {
        _query_usage(argv[0]);
        return 1;
    }
    if (DNS_TRANSPORT == DNS_TRANSPORT_COAP) {
        if (argc < 4) {
            method = COAP_METHOD_FETCH;
        }
        else if ((method = _parse_method(argv[3])) == COAP_CLASS_REQ) {
            _query_usage(argv[0]);
            return 1;
        }
    }
    else {
        method = 0;
    }
    return _query2(argv[1], family, method);
}

static void _query_bulk_usage(const char *cmd)
{
    printf("usage: %s add <sleep time in ms>\n", cmd);
    printf("usage: %s reset\n", cmd);
    printf("usage: %s exec <hostname> <family> [[<method>] <mod>]\n", cmd);
}

static int _query_bulk(int argc, char **argv)
{
    if (argc < 2) {
        goto usage;
    }
    if (strcmp(argv[1], "add") == 0) {
        uint32_t sleep_time_ms;

        if (argc < 3) {
            goto usage;
        }
        sleep_time_ms = (uint32_t)atoi(argv[2]);
        if ((sleep_time_ms == 0) || (sleep_time_ms > UINT16_MAX)) {
            goto usage;
        }
        if (_req_time_count > QUERY_COUNT) {
            printf("Only able to store a schedule of %u sleep times\n",
                   (unsigned)QUERY_COUNT);
            return 1;
        }
        _req_times[_req_time_count++] = (uint16_t)sleep_time_ms;
        if (_req_time_count < 2U) {
            printf("Will wait %u ms before first query\n",
                   (unsigned)sleep_time_ms);
        }
        else {
            printf("Will wait %u ms between queries %u and %u\n",
                   (unsigned)sleep_time_ms, _req_time_count - 2,
                   _req_time_count - 1);
        }
        return 0;
    }
    else if (strcmp(argv[1], "reset") == 0) {
        _req_time_count = 0;
        return 0;
    }
    else if (strcmp(argv[1], "exec") == 0) {
        char hostname[HOSTNAME_LEN];
        uint32_t last_wakeup;
        uint16_t modulo = 0;
        uint16_t id = _id;
        int family;
        uint8_t method;

        if (argc < 4) {
            goto usage;
        }
        if ((strlen(argv[2]) + 6) >= HOSTNAME_LEN) {
            goto usage;
        }
        if ((family = _parse_af(argv[3])) < 0) {
            goto usage;
        }
        if (DNS_TRANSPORT == DNS_TRANSPORT_COAP) {
            if (argc < 5) {
                method = COAP_METHOD_FETCH;
            }
            else {
                if ((method = _parse_method(argv[4])) == COAP_CLASS_REQ) {
                    goto usage;
                }
                if (argc > 5) {
                    modulo = atoi(argv[5]);
                }
            }
        }
        else {
            method = 0;
        }
        last_wakeup = ztimer_now(ZTIMER_MSEC);
        if (modulo) {
            id = id % modulo;
        }
        sprintf(hostname, "%05u.%s", id, argv[2]);
        for (unsigned i = 0; i < _req_time_count; i++) {
            ztimer_periodic_wakeup(ZTIMER_MSEC, &last_wakeup, _req_times[i]);
            _query2(hostname, family, method);
            id = _id;
            if (modulo) {
                id = id % modulo;
            }
            sprintf(hostname, "%05u.%s", id, argv[2]);
        }
        return 0;
    }
usage:
    _query_bulk_usage(argv[0]);
    return 1;
}

#if IS_USED(MODULE_GCOAP_DNS_OSCORE)
static bool _parse_singlehex(char hex, uint8_t *target) {
    if ('0' <= hex && hex <= '9') {
        *target = hex - '0';
        return true;
    }
    if ('a' <= hex && hex <= 'f') {
        *target = hex - 'a' + 10;
        return true;
    }
    if ('A' <= hex && hex <= 'F') {
        *target = hex - 'A' + 10;
        return true;
    }
    return false;
}

static bool _parse_hex(char *hex, size_t len, uint8_t *data) {
    uint8_t acc;
    while (len) {
        if (!_parse_singlehex(*hex++, &acc)) {
            return false;
        }
        *data = acc << 4;
        if (!_parse_singlehex(*hex++, &acc)) {
            return false;
        }
        *data |= acc;
        len--;
        data++;
    }
    if (len == 0 && *hex == '-') {
        hex++;
    }
    return *hex == 0;
}

static bool _parse_i64(char *chars, int64_t *out) {
    char *end = NULL;
    *out = strtoll(chars, &end, 10);
    if (*end != ' ' && *end != '\0' && *end != '\n')
        return false;
    return true;
}

static int _userctx(int argc, char **argv)
{
    int64_t alg_num;
    uint8_t sender_key[32], recipient_key[32];
    uint8_t common_iv[20];
    uint8_t sender_id[OSCORE_KEYID_MAXLEN], recipient_id[OSCORE_KEYID_MAXLEN];
    size_t sender_id_len, recipient_id_len;

    if (argc < 7) {
        printf("usage: <userctx> <alg> <sender-id> <recipient-id> <common-iv> "
               "<sender-key> <recipient-key>");
        return 1;
    }

    if (!_parse_i64(argv[1], &alg_num)) {
        printf("Algorithm number was not a number\n");
        return 1;
    }
    sender_id_len = strlen(argv[2]) / 2;
    if (sender_id_len > OSCORE_KEYID_MAXLEN) {
        printf("Sender ID too long\n");
        return 1;
    }
    if (!_parse_hex(argv[2], sender_id_len, sender_id)) {
        printf("Invalid Sender ID\n");
        return 1;
    }
    recipient_id_len = strlen(argv[2]) / 2;
    if (recipient_id_len > OSCORE_KEYID_MAXLEN) {
        printf("Recipient ID too long\n");
        return 1;
    }
    if (!_parse_hex(argv[3], recipient_id_len, recipient_id)) {
        printf("Invalid Recipient ID\n");
        return 1;
    }
    if (!_parse_hex(argv[4], oscore_crypto_aead_get_ivlength(alg_num), common_iv)) {
        printf("Invalid Common IV\n");
        return 1;
    }
    if (!_parse_hex(argv[5], oscore_crypto_aead_get_keylength(alg_num), sender_key)) {
        printf("Invalid Sender Key'\n");
        return 1;
    }
    if (!_parse_hex(argv[6], oscore_crypto_aead_get_keylength(alg_num), recipient_key)) {
        printf("Invalid Recipient Key\n");
        return 1;
    }
    if (gcoap_dns_oscore_set_secctx(alg_num, sender_id, sender_id_len,
                                    recipient_id, recipient_id_len,
                                    common_iv, sender_key, recipient_key) < 0) {
        perror("Unable to set OSCORE user context");
        return 1;
    }
    printf("Successfully added user context\n");
    return 0;
}
#endif

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
#if IS_USED(GCOAP_APP)
    server_init();
#endif
    /* we need a message queue for the thread running the shell in order to
     * receive potentially fast incoming networking packets */
    msg_init_queue(_main_msg_queue, MAIN_QUEUE_SIZE);
    _id = random_uint32();
    shell_run(_shell_commands, _line_buf, SHELL_DEFAULT_BUFSIZE);
    return 0;
}

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

/** @} */
