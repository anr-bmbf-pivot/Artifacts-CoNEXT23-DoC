APPLICATION = proxy

BOARD ?= iotlab-m3

RIOTBASE ?= $(CURDIR)/../../RIOT
DEVELHELP ?= 1
VERBOSE_ASSERT ?= 1

SHOULD_RUN_KCONFIG = 1

ifneq (,$(WHITELIST_NAME))
  USEMODULE += l2filter_whitelist
endif

USEMODULE += auto_init_gnrc_netif
USEMODULE += auto_init_gnrc_rpl
USEMODULE += ipv4_addr
USEMODULE += ipv6_addr
USEMODULE += gcoap
USEMODULE += gcoap_forward_proxy_upstream
USEMODULE += gnrc_icmpv6_echo
USEMODULE += gnrc_ipv6_router_default
USEMODULE += gnrc_pktbuf_cmd
USEMODULE += gnrc_rpl
USEMODULE += nanocoap_cache
USEMODULE += netdev_default
USEMODULE += netstats_l2
USEMODULE += od
USEMODULE += ps
USEMODULE += shell
USEMODULE += shell_commands
USEMODULE += sock_async_event
USEMODULE += ztimer_msec
USEMODULE += ztimer_usec

ON_BR ?= 0

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

CFLAGS += -D"GCOAP_STACK_SIZE"=\(2*THREAD_STACKSIZE_DEFAULT\)
ifneq (,$(WHITELIST_NAME))
  CFLAGS += -D"WHITELIST_NAME=\"$(WHITELIST_NAME)\""
endif

DOCKER_ENV_VARS += DEFAULT_CHANNEL
DOCKER_ENV_VARS += DEVELHELP
DOCKER_ENV_VARS += ETHOS_BAUDRATE
DOCKER_ENV_VARS += KCONFIG_ADD_CONFIG
DOCKER_ENV_VARS += ON_BR
DOCKER_ENV_VARS += VERBOSE_ASSERT
DOCKER_ENV_VARS += SHOULD_RUN_KCONFIG
DOCKER_ENV_VARS += SITE_PREFIX
DOCKER_ENV_VARS += STATIC_ROUTES
DOCKER_ENV_VARS += TAP
DOCKER_ENV_VARS += USEMODULE
DOCKER_ENV_VARS += WHITELIST_NAME
DOCKER_MAKE_ARGS ?= -j

include $(RIOTBASE)/Makefile.include

.PHONY: host-tools

host-tools:
	$(Q)env -u CC -u CFLAGS $(MAKE) -C $(RIOTTOOLS)

# Set a custom channel if needed
include $(RIOTMAKE)/default-radio-settings.inc.mk
