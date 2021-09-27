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
USEMODULE += gnrc_rpl
USEMODULE += netdev_default
USEMODULE += prng_sha256prng
USEMODULE += ps
USEMODULE += shell
USEMODULE += shell_commands
USEMODULE += sock_async_event
USEMODULE += ztimer_msec
USEMODULE += ztimer_usec

DNS_TRANSPORT ?= udp
QUERY_COUNT ?= 100
ON_BR ?= 0
ONLY_FETCH ?= 0

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

ifeq (coap,$(DNS_TRANSPORT))
  KCONFIG_ADD_CONFIG += $(CURDIR)/coap.config
  KCONFIG_ADD_CONFIG += $(CURDIR)/coap_unencrypted.config
  USEMODULE += gcoap_dns
  USEMODULE += gcoap_dns_async
  ifneq (1,$(ONLY_FETCH))
    USEMODULE += gcoap_dns_get
    USEMODULE += gcoap_dns_post
  endif
  CFLAGS += -D"DNS_TRANSPORT=DNS_TRANSPORT_COAP"
else
  ifeq (coaps,$(DNS_TRANSPORT))
    USEPKG += tinydtls
    KCONFIG_ADD_CONFIG += $(CURDIR)/tinydtls.config
    KCONFIG_ADD_CONFIG += $(CURDIR)/coap.config
    USEMODULE += gcoap_dns
    USEMODULE += gcoap_dns_async
    CFLAGS += -D"DNS_TRANSPORT=DNS_TRANSPORT_COAP"
    CFLAGS += -D"DTLS_PEER_MAX=2"
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
endif

CFLAGS += -D"QUERY_COUNT"=$(QUERY_COUNT)
CFLAGS += -D"THREAD_STACKSIZE_MAIN"=\(3*THREAD_STACKSIZE_DEFAULT\)
CFLAGS += -D"EVENT_THREAD_STACKSIZE_DEFAULT"=\(3*THREAD_STACKSIZE_DEFAULT\)

include $(RIOTBASE)/Makefile.include

.PHONY: host-tools

host-tools:
	$(Q)env -u CC -u CFLAGS $(MAKE) -C $(RIOTTOOLS)

# Set a custom channel if needed
include $(RIOTMAKE)/default-radio-settings.inc.mk
