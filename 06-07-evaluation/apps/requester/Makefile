APPLICATION = requester

BOARD ?= iotlab-m3

RIOTBASE ?= $(CURDIR)/../../RIOT
DEVELHELP ?= 1
VERBOSE_ASSERT ?= 1

SHOULD_RUN_KCONFIG = 1

USEMODULE += embunit

USEMODULE += auto_init_gnrc_netif
USEMODULE += auto_init_gnrc_rpl
USEMODULE += ipv4_addr
USEMODULE += ipv6_addr
USEMODULE += gnrc_icmpv6_echo
USEMODULE += gnrc_ipv6_default
USEMODULE += gnrc_pktbuf_cmd
USEMODULE += gnrc_rpl
USEMODULE += netdev_default
USEMODULE += netstats_l2
USEMODULE += prng_sha256prng
USEMODULE += ps
USEMODULE += od
USEMODULE += shell
USEMODULE += shell_commands
USEMODULE += sock_async_event
USEMODULE += ztimer_msec
USEMODULE += ztimer_usec

DNS_TRANSPORT ?= udp
QUERY_COUNT ?= 50
ON_BR ?= 0
ONLY_FETCH ?= 0
PROXIED ?= 0
WITH_COAP_CACHE ?= 0
WITH_DNS_CACHE ?= 0
DOH_LIKE ?= 0
ASYNC ?= 1

ifeq (1,$(PROXIED))
  ifneq (,$(WHITELIST_NAME))
    USEMODULE += l2filter_whitelist
  endif
endif

ifeq (1,$(WITH_DNS_CACHE))
  USEMODULE += dns_cache
endif

ifeq (1,$(ON_BR))
  USEMODULE += gnrc_sixlowpan_border_router_default
  USEMODULE += gnrc_uhcpc
  USEMODULE += stdio_ethos

  ETHOS_BAUDRATE ?= 115200
  CFLAGS += -DETHOS_BAUDRATE=$(ETHOS_BAUDRATE)
  SITE_PREFIX ?= "2001:db8::/64"
  STATIC_ROUTES ?= 1
  TAP ?= tap0
  TERMDEPS += host-tools
  TERMPROG ?= sudo sh $(RIOTTOOLS)/ethos/start_network.sh
  TERMFLAGS ?= $(FLAGS_EXTRAS) $(PORT) $(TAP) $(SITE_PREFIX) $(ETHOS_BAUDRATE)
else
  USEMODULE += gnrc_netif_single        # Only one interface used and it makes
                                        # shell commands easier
endif

ifneq (,$(filter coap coaps oscore,$(DNS_TRANSPORT)))
  KCONFIG_ADD_CONFIG += $(CURDIR)/coap.config
  ifneq (,$(COAP_BLOCKSIZE))
    KCONFIG_ADD_CONFIG += $(CURDIR)/blockwise$(COAP_BLOCKSIZE).config
  endif
  USEMODULE += gcoap_dns
  USEMODULE += gcoap_dns_async
  ifneq (1,$(ONLY_FETCH))
    USEMODULE += gcoap_dns_get
    USEMODULE += gcoap_dns_post
  endif
  ifeq (1,$(PROXIED))
    USEMODULE += gcoap_dns_proxied
  endif
  CFLAGS += -D"DNS_TRANSPORT=DNS_TRANSPORT_COAP"
  ifeq (coaps,$(DNS_TRANSPORT))
    USEMODULE += gcoap_dtls
    USEMODULE += prng_sha256prng
    USEPKG += tinydtls
    KCONFIG_ADD_CONFIG += $(CURDIR)/tinydtls.config
    KCONFIG_ADD_CONFIG += $(CURDIR)/coaps.config
    CFLAGS += -D"DTLS_PEER_MAX=2"
  endif
  ifeq (oscore,$(DNS_TRANSPORT))
    USEMODULE += gcoap_dns_oscore
    CFLAGS += -DOSCORE_NANOCOAP_MEMMOVE_MODE
    OSCOREBASE = $(RIOTBASE)/../liboscore
  endif
  ifeq (1,$(WITH_COAP_CACHE))
    USEMODULE += nanocoap_cache
    KCONFIG_ADD_CONFIG += $(CURDIR)/coap_cache.config
  endif
  ifeq (1,$(DOH_LIKE))
    USEMODULE += gcoap_dns_doh_like
  endif
else
  ifeq (dtls,$(DNS_TRANSPORT))
    USEPKG += tinydtls
    KCONFIG_ADD_CONFIG += $(CURDIR)/tinydtls.config
    KCONFIG_ADD_CONFIG += $(CURDIR)/sock_dodtls.config
    USEMODULE += event_callback
    USEMODULE += event_timeout_ztimer
    USEMODULE += event_thread
    USEMODULE += sock_dodtls
    CFLAGS += -D"DNS_TRANSPORT=DNS_TRANSPORT_DTLS"
  else
    ifeq (udp,$(DNS_TRANSPORT))
      USEMODULE += event_callback
      USEMODULE += event_timeout_ztimer
      USEMODULE += event_thread
      USEMODULE += sock_dns
      CFLAGS += -D"DNS_TRANSPORT=DNS_TRANSPORT_UDP"
    else
      $(error "Unknown DNS_TRANSPORT = $(DNS_TRANSPORT)")
    endif
  endif
endif

CFLAGS += -D"QUERY_COUNT"=$(QUERY_COUNT)
CFLAGS += -D"THREAD_STACKSIZE_MAIN"=\(3*THREAD_STACKSIZE_DEFAULT\)
CFLAGS += -D"GNRC_SIXLOWPAN_STACK_SIZE"=THREAD_STACKSIZE_SMALL
CFLAGS += -D"GNRC_UDP_STACK_SIZE"=THREAD_STACKSIZE_SMALL
CFLAGS += -D"EVENT_THREAD_STACKSIZE_DEFAULT"=\(3*THREAD_STACKSIZE_DEFAULT\)
ifeq (0, $(ASYNC))
  CFLAGS += -D"DNS_TRANSPORT_SYNC"
endif
ifneq (,$(WHITELIST_NAME))
  CFLAGS += -D"WHITELIST_NAME=\"$(WHITELIST_NAME)\""
endif

DOCKER_ENV_VARS += ASYNC
DOCKER_ENV_VARS += DEFAULT_CHANNEL
DOCKER_ENV_VARS += DEVELHELP
DOCKER_ENV_VARS += DNS_TRANSPORT
DOCKER_ENV_VARS += ETHOS_BAUDRATE
DOCKER_ENV_VARS += KCONFIG_ADD_CONFIG
DOCKER_ENV_VARS += ON_BR
DOCKER_ENV_VARS += ONLY_FETCH
DOCKER_ENV_VARS += OSCOREBASE
DOCKER_ENV_VARS += QUERY_COUNT
DOCKER_ENV_VARS += PROXIED
DOCKER_ENV_VARS += VERBOSE_ASSERT
DOCKER_ENV_VARS += SHOULD_RUN_KCONFIG
DOCKER_ENV_VARS += SITE_PREFIX
DOCKER_ENV_VARS += STATIC_ROUTES
DOCKER_ENV_VARS += TAP
DOCKER_ENV_VARS += USEMODULE
DOCKER_ENV_VARS += WHITELIST_NAME
DOCKER_ENV_VARS += WITH_COAP_CACHE
DOCKER_ENV_VARS += WITH_DNS_CACHE
DOCKER_MAKE_ARGS ?= -j

include $(RIOTBASE)/Makefile.include

CFLAGS += -I$(GENERATED_DIR)

.PHONY: host-tools

host-tools:
	$(Q)env -u CC -u CFLAGS $(MAKE) -C $(RIOTTOOLS)

# make the build size analysis tool run without webserver if desired
ifneq (,$(COSY_NO_WEBSERVER))
  COSY_TOOL += -d
endif

# Set a custom channel if needed
include $(RIOTMAKE)/default-radio-settings.inc.mk
