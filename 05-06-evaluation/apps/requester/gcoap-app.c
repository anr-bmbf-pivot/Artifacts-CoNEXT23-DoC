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
#include <stdlib.h>

#include "led.h"
#include "kernel_defines.h"
#include "net/gcoap.h"
#include "net/utils.h"
#include "fmt.h"
#include "od.h"

#define ENABLE_DEBUG 0
#include "debug.h"

#if IS_ACTIVE(GCOAP_APP)
#if IS_ACTIVE(GCOAP_APP_DTLS)
#include "net/credman.h"
#include "net/dsm.h"
#include "tinydtls_keys.h"

/* Example credential tag for credman. Tag together with the credential type needs to be unique. */
#define GCOAP_DTLS_CREDENTIAL_TAG 10

static const uint8_t psk_id_0[] = PSK_DEFAULT_IDENTITY;
static const uint8_t psk_key_0[] = PSK_DEFAULT_KEY;
static const credman_credential_t credential = {
    .type = CREDMAN_TYPE_PSK,
    .tag = GCOAP_DTLS_CREDENTIAL_TAG,
    .params = {
        .psk = {
            .key = { .s = psk_key_0, .len = sizeof(psk_key_0) - 1, },
            .id = { .s = psk_id_0, .len = sizeof(psk_id_0) - 1, },
        }
    },
};
#endif

static ssize_t _encode_link(const coap_resource_t *resource, char *buf,
                            size_t maxlen, coap_link_encoder_ctx_t *context);
static ssize_t _stats_handler(coap_pkt_t* pdu, uint8_t *buf, size_t len, coap_request_ctx_t *ctx);
static ssize_t _riot_board_handler(coap_pkt_t* pdu, uint8_t *buf, size_t len, coap_request_ctx_t *ctx);

static const char *_link_params[] = {
    ";ct=0;rt=\"count\";obs",
    NULL
};

/* CoAP resources. Must be sorted by path (ASCII order). */
static const coap_resource_t _resources[] = {
    { "/cli/stats", COAP_GET | COAP_PUT, _stats_handler, NULL },
    { "/riot/board", COAP_GET, _riot_board_handler, NULL },
};

static gcoap_listener_t _listener = {
    &_resources[0],
    ARRAY_SIZE(_resources),
    GCOAP_SOCKET_TYPE_UNDEF,
    _encode_link,
    NULL,
    NULL
};

static uint16_t req_count = 0;

/* Adds link format params to resource list */
static ssize_t _encode_link(const coap_resource_t *resource, char *buf,
                            size_t maxlen, coap_link_encoder_ctx_t *context) {
    ssize_t res = gcoap_encode_link(resource, buf, maxlen, context);
    if (res > 0) {
        if (_link_params[context->link_pos]
                && (strlen(_link_params[context->link_pos]) < (maxlen - res))) {
            if (buf) {
                memcpy(buf+res, _link_params[context->link_pos],
                       strlen(_link_params[context->link_pos]));
            }
            return res + strlen(_link_params[context->link_pos]);
        }
    }

    return res;
}

/*
 * Server callback for /cli/stats. Accepts either a GET or a PUT.
 *
 * GET: Returns the count of packets sent by the CLI.
 * PUT: Updates the count of packets. Rejects an obviously bad request, but
 *      allows any two byte value for example purposes. Semantically, the only
 *      valid action is to set the value to 0.
 */
static ssize_t _stats_handler(coap_pkt_t* pdu, uint8_t *buf, size_t len, coap_request_ctx_t *ctx)
{
    (void)ctx;

    /* read coap method type in packet */
    unsigned method_flag = coap_method2flag(coap_get_code_detail(pdu));

    switch (method_flag) {
        case COAP_GET:
            gcoap_resp_init(pdu, buf, len, COAP_CODE_CONTENT);
            coap_opt_add_format(pdu, COAP_FORMAT_TEXT);
            size_t resp_len = coap_opt_finish(pdu, COAP_OPT_FINISH_PAYLOAD);

            /* write the response buffer with the request count value */
            resp_len += fmt_u16_dec((char *)pdu->payload, req_count);
            return resp_len;

        case COAP_PUT:
            /* convert the payload to an integer and update the internal
               value */
            if (pdu->payload_len <= 5) {
                char payload[6] = { 0 };
                memcpy(payload, (char *)pdu->payload, pdu->payload_len);
                req_count = (uint16_t)strtoul(payload, NULL, 10);
                return gcoap_response(pdu, buf, len, COAP_CODE_CHANGED);
            }
            else {
                return gcoap_response(pdu, buf, len, COAP_CODE_BAD_REQUEST);
            }
    }

    return 0;
}

static ssize_t _riot_board_handler(coap_pkt_t *pdu, uint8_t *buf, size_t len, coap_request_ctx_t *ctx)
{
    (void)ctx;
    gcoap_resp_init(pdu, buf, len, COAP_CODE_CONTENT);
    coap_opt_add_format(pdu, COAP_FORMAT_TEXT);
    size_t resp_len = coap_opt_finish(pdu, COAP_OPT_FINISH_PAYLOAD);

    /* write the RIOT board name in the response buffer */
    if (pdu->payload_len >= strlen(RIOT_BOARD)) {
        memcpy(pdu->payload, RIOT_BOARD, strlen(RIOT_BOARD));
        return resp_len + strlen(RIOT_BOARD);
    }
    else {
        puts("gcoap_cli: msg buffer too small");
        return gcoap_response(pdu, buf, len, COAP_CODE_INTERNAL_SERVER_ERROR);
    }
}

static void notify_observers(void)
{
    size_t len;
    uint8_t buf[CONFIG_GCOAP_PDU_BUF_SIZE];
    coap_pkt_t pdu;

    /* send Observe notification for /cli/stats */
    switch (gcoap_obs_init(&pdu, &buf[0], CONFIG_GCOAP_PDU_BUF_SIZE,
            &_resources[0])) {
    case GCOAP_OBS_INIT_OK:
        DEBUG("gcoap_cli: creating /cli/stats notification\n");
        coap_opt_add_format(&pdu, COAP_FORMAT_TEXT);
        len = coap_opt_finish(&pdu, COAP_OPT_FINISH_PAYLOAD);
        len += fmt_u16_dec((char *)pdu.payload, req_count);
        gcoap_obs_send(&buf[0], len, &_resources[0]);
        break;
    case GCOAP_OBS_INIT_UNUSED:
        DEBUG("gcoap_cli: no observer for /cli/stats\n");
        break;
    case GCOAP_OBS_INIT_ERR:
        DEBUG("gcoap_cli: error initializing /cli/stats notification\n");
        break;
    }
}

void server_init(void)
{
#if IS_ACTIVE(GCOAP_APP_DTLS)
    int res = credman_add(&credential);
    if (res < 0 && res != CREDMAN_EXIST) {
        /* ignore duplicate credentials */
        printf("gcoap: cannot add credential to system: %d\n", res);
        return;
    }
    sock_dtls_t *gcoap_sock_dtls = gcoap_get_sock_dtls();
    res = sock_dtls_add_credential(gcoap_sock_dtls, GCOAP_DTLS_CREDENTIAL_TAG);
    if (res < 0) {
        printf("gcoap: cannot add credential to DTLS sock: %d\n", res);
    }
#endif

    gcoap_register_listener(&_listener);
}

#if IS_ACTIVE(GCOAP_APP_DTLS)
#include "net/dsm.h"
#endif

static bool _proxied = false;
static sock_udp_ep_t _proxy_remote;
static char proxy_uri[64];

/* Retain request path to re-request if response includes block. User must not
 * start a new request (with a new path) until any blockwise transfer
 * completes or times out. */
#define _LAST_REQ_PATH_MAX (64)
static char _last_req_path[_LAST_REQ_PATH_MAX];

/*
 * Response callback.
 */
static void _resp_handler(const gcoap_request_memo_t *memo, coap_pkt_t* pdu,
                          const sock_udp_ep_t *remote)
{
    (void)remote;       /* not interested in the source currently */

    if (memo->state == GCOAP_MEMO_TIMEOUT) {
        printf("gcoap: timeout for msg ID %02u\n", coap_get_id(pdu));
        return;
    }
    else if (memo->state == GCOAP_MEMO_RESP_TRUNC) {
        /* The right thing to do here would be to look into whether at least
         * the options are complete, then to mentally trim the payload to the
         * next block boundary and pretend it was sent as a Block2 of that
         * size. */
        printf("gcoap: warning, incomplete response; continuing with the truncated payload\n");
    }
    else if (memo->state != GCOAP_MEMO_RESP) {
        printf("gcoap: error in response\n");
        return;
    }

    coap_block1_t block;
    if (coap_get_block2(pdu, &block) && block.blknum == 0) {
        puts("--- blockwise start ---");
    }

    char *class_str = (coap_get_code_class(pdu) == COAP_CLASS_SUCCESS)
                            ? "Success" : "Error";
    printf("gcoap: response %s, code %1u.%02u", class_str,
                                                coap_get_code_class(pdu),
                                                coap_get_code_detail(pdu));
    if (pdu->payload_len) {
        unsigned content_type = coap_get_content_type(pdu);
        if (content_type == COAP_FORMAT_TEXT
                || content_type == COAP_FORMAT_LINK
                || coap_get_code_class(pdu) == COAP_CLASS_CLIENT_FAILURE
                || coap_get_code_class(pdu) == COAP_CLASS_SERVER_FAILURE) {
            /* Expecting diagnostic payload in failure cases */
            printf(", %u bytes\n%.*s\n", pdu->payload_len, pdu->payload_len,
                                                          (char *)pdu->payload);
        }
        else {
            printf(", %u bytes\n", pdu->payload_len);
            od_hex_dump(pdu->payload, pdu->payload_len, OD_WIDTH_DEFAULT);
        }
    }
    else {
        printf(", empty payload\n");
    }

    /* ask for next block if present */
    if (coap_get_block2(pdu, &block)) {
        if (block.more) {
            unsigned msg_type = coap_get_type(pdu);
            if (block.blknum == 0 && !strlen(_last_req_path)) {
                puts("Path too long; can't complete blockwise");
                return;
            }

            if (_proxied) {
                gcoap_req_init(pdu, (uint8_t *)pdu->hdr, CONFIG_GCOAP_PDU_BUF_SIZE,
                               COAP_METHOD_GET, NULL);
            }
            else {
                gcoap_req_init(pdu, (uint8_t *)pdu->hdr, CONFIG_GCOAP_PDU_BUF_SIZE,
                               COAP_METHOD_GET, _last_req_path);
            }

            if (msg_type == COAP_TYPE_ACK) {
                coap_hdr_set_type(pdu->hdr, COAP_TYPE_CON);
            }
            block.blknum++;
            coap_opt_add_block2_control(pdu, &block);

            if (_proxied) {
                coap_opt_add_proxy_uri(pdu, _last_req_path);
            }

            int len = coap_opt_finish(pdu, COAP_OPT_FINISH_NONE);
            gcoap_req_send((uint8_t *)pdu->hdr, len, remote,
                           _resp_handler, memo->context);
        }
        else {
            puts("--- blockwise complete ---");
        }
    }
}

static bool _parse_endpoint(sock_udp_ep_t *remote,
                            const char *addr_str, const char *port_str)
{
    netif_t *netif;

    /* parse hostname */
    if (netutils_get_ipv6((ipv6_addr_t *)&remote->addr, &netif, addr_str) < 0) {
        puts("gcoap_cli: unable to parse destination address");
        return false;
    }
    remote->netif = netif ? netif_get_id(netif) : SOCK_ADDR_ANY_NETIF;
    remote->family = AF_INET6;

    /* parse port */
    remote->port = atoi(port_str);
    if (remote->port == 0) {
        puts("gcoap_cli: unable to parse destination port");
        return false;
    }

    return true;
}

static size_t _send(uint8_t *buf, size_t len, char *addr_str, char *port_str)
{
    size_t bytes_sent;
    sock_udp_ep_t *remote;
    sock_udp_ep_t new_remote;

    if (_proxied) {
        remote = &_proxy_remote;
    }
    else {
        if (!_parse_endpoint(&new_remote, addr_str, port_str)) {
            return 0;
        }
        remote = &new_remote;
    }

    bytes_sent = gcoap_req_send(buf, len, remote, _resp_handler, NULL);
    if (bytes_sent > 0) {
        req_count++;
    }
    return bytes_sent;
}

static int _print_usage(char **argv)
{
    printf("usage: %s <get|post|put|ping|proxy|info>\n", argv[0]);
    return 1;
}

int gcoap_cli_cmd(int argc, char **argv)
{
    /* Ordered like the RFC method code numbers, but off by 1. GET is code 0. */
    char *method_codes[] = {"ping", "get", "post", "put"};
    uint8_t buf[CONFIG_GCOAP_PDU_BUF_SIZE];
    coap_pkt_t pdu;
    size_t len;

    if (argc == 1) {
        /* show help for main commands */
        return _print_usage(argv);
    }

    if (strcmp(argv[1], "info") == 0) {
        uint8_t open_reqs = gcoap_op_state();

        if (IS_USED(GCOAP_APP_DTLS)) {
            printf("CoAP server is listening on port %u\n", CONFIG_GCOAPS_PORT);
        } else {
            printf("CoAP server is listening on port %u\n", CONFIG_GCOAP_PORT);
        }
#if IS_ACTIVE(GCOAP_APP_DTLS)
        printf("Connection secured with DTLS\n");
        printf("Free DTLS session slots: %d/%d\n", dsm_get_num_available_slots(),
                dsm_get_num_maximum_slots());
#endif
        printf(" CLI requests sent: %u\n", req_count);
        printf("CoAP open requests: %u\n", open_reqs);
        printf("Configured Proxy: ");
        if (_proxied) {
            char addrstr[IPV6_ADDR_MAX_STR_LEN];
            printf("[%s]:%u\n",
                   ipv6_addr_to_str(addrstr,
                                    (ipv6_addr_t *) &_proxy_remote.addr.ipv6,
                                    sizeof(addrstr)),
                   _proxy_remote.port);
        }
        else {
            puts("None");
        }
        return 0;
    }
    else if (strcmp(argv[1], "proxy") == 0) {
        if ((argc == 5) && (strcmp(argv[2], "set") == 0)) {
            if (!_parse_endpoint(&_proxy_remote, argv[3], argv[4])) {
                puts("Could not set proxy");
                return 1;
            }
            _proxied = true;
            return 0;
        }
        if ((argc == 3) && (strcmp(argv[2], "unset") == 0)) {
            memset(&_proxy_remote, 0, sizeof(_proxy_remote));
            _proxied = false;
            return 0;
        }
        printf("usage: %s proxy set <addr>[%%iface] <port>\n", argv[0]);
        printf("       %s proxy unset\n", argv[0]);
        return 1;
    }

    /* if not 'info' and 'proxy', must be a method code or ping */
    int code_pos = -1;
    for (size_t i = 0; i < ARRAY_SIZE(method_codes); i++) {
        if (strcmp(argv[1], method_codes[i]) == 0) {
            code_pos = i;
        }
    }
    if (code_pos == -1) {
        return _print_usage(argv);
    }

    /* parse options */
    int apos = 2;       /* position of address argument */
    /* ping must be confirmable */
    unsigned msg_type = (!code_pos ? COAP_TYPE_CON : COAP_TYPE_NON);
    if (argc > apos && strcmp(argv[apos], "-c") == 0) {
        msg_type = COAP_TYPE_CON;
        apos++;
    }

    if (((argc == apos + 2) && (code_pos == 0)) ||    /* ping */
        ((argc == apos + 3) && (code_pos == 1)) ||    /* get */
        ((argc == apos + 3 ||
          argc == apos + 4) && (code_pos > 1))) {     /* post or put */

        char *uri = NULL;
        int uri_len = 0;
        if (code_pos) {
            uri = argv[apos+2];
            uri_len = strlen(argv[apos+2]);
        }

        if (_proxied) {
            uri_len = snprintf(proxy_uri, 64, "coap://[%s]:%s%s", argv[apos], argv[apos+1], uri);
            uri = proxy_uri;

            gcoap_req_init(&pdu, &buf[0], CONFIG_GCOAP_PDU_BUF_SIZE, code_pos, NULL);
        }
        else{
            gcoap_req_init(&pdu, &buf[0], CONFIG_GCOAP_PDU_BUF_SIZE, code_pos, uri);
        }
        coap_hdr_set_type(pdu.hdr, msg_type);

        memset(_last_req_path, 0, _LAST_REQ_PATH_MAX);
        if (uri_len < _LAST_REQ_PATH_MAX) {
            memcpy(_last_req_path, uri, uri_len);
        }

        size_t paylen = (argc == apos + 4) ? strlen(argv[apos+3]) : 0;
        if (paylen) {
            coap_opt_add_format(&pdu, COAP_FORMAT_TEXT);
        }

        if (_proxied) {
            coap_opt_add_proxy_uri(&pdu, uri);
        }

        if (paylen) {
            len = coap_opt_finish(&pdu, COAP_OPT_FINISH_PAYLOAD);
            if (pdu.payload_len >= paylen) {
                memcpy(pdu.payload, argv[apos+3], paylen);
                len += paylen;
            }
            else {
                puts("gcoap_cli: msg buffer too small");
                return 1;
            }
        }
        else {
            len = coap_opt_finish(&pdu, COAP_OPT_FINISH_NONE);
        }

        printf("gcoap_cli: sending msg ID %u, %u bytes\n", coap_get_id(&pdu),
               (unsigned) len);
        if (!_send(&buf[0], len, argv[apos], argv[apos+1])) {
            puts("gcoap_cli: msg send failed");
        }
        else {
            /* send Observe notification for /cli/stats */
            notify_observers();
        }
        return 0;
    }
    else {
        printf("usage: %s <get|post|put> [-c] <addr>[%%iface] <port> <path> [data]\n",
               argv[0]);
        printf("       %s ping <addr>[%%iface] <port>\n", argv[0]);
        printf("Options\n");
        printf("    -c  Send confirmably (defaults to non-confirmable)\n");
        return 1;
    }

    return _print_usage(argv);
}
#else
typedef int dont_be_pedantic;
#endif

/** @} */
