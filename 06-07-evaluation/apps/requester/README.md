# Requester application

This is the application for the clients for the evaluation in Sections 6, *Comparison of
Low-Power DNS Transports*, and 7, *Evaluation of Caching for DoC*, of the Paper. On command,
it will asynchronously query for a given number of times, names from a pre-configured upstream DNS
server.

## Compile-time configuration

The base configuration for this application in Kconfig can be found in [`app.config`](./app.config).

There are multiple compile time configurations which are switchable via environment variables to
suit the parametrization for our experiments. These environment variables can also imply the
inclusion of additional configuration files to Kconfig.

- `DNS_TRANSPORTS` (default: "`udp`"): Sets the transport used for DNS messages. Either of the
  following values are expected:
  + `udp`: Sets the macro `DNS_TRANSPORT` to `DNS_TRANSPORT_UDP`. The application will use
    **unencrypted DNS** over UDP to query for names.
  + `dtls`: Sets the macro `DNS_TRANSPORT` to `DNS_TRANSPORT_DTLS`. The application will use **DNS
    over DTLSv1.2** to query for names. This also includes [`tinydtls.config`](./tinydtls.config)
    and [`sock_dtls.config`](./sock_dtls.config) into the configuration of the application.
  + `coap`: Sets the macro `DNS_TRANSPORT` to `DNS_TRANSPORT_COAP`. The application will use 
    **unencrypted DNS over CoAP** to query for names. This also includes
    [`coap.config`](./coap.config) into the configuration of the application.
  + `coaps`: Sets the macro `DNS_TRANSPORT` to `DNS_TRANSPORT_COAP`. The application will use **DNS
    over CoAPSv1.2** (DNS over CoAP over DTLSv1.2) to query for names. This also includes
    [`coap.config`](./coap.config), [`coaps.config`](./coaps.config), and
    [`tinydtls.config`](./tinydtls.config) into the configuration of the application.
  + `oscore`: Sets the macro `DNS_TRANSPORT` to `DNS_TRANSPORT_COAP`. The application will use
    **DNS over OSCORE** to query for names. This also includes [`coap.config`](./coap.config) into
    the configuration of the application and sets the `OSCORE_NANOCOAP_MEMMOVE_MODE` macro for
    [libOSCORE].
- `ASYNC` (default: 1): With `ASYNC=0` the application is configured to query the names
  synchronously (i.e. one at a time until a response was received, or the query timed out). Defines
  the `DNS_TRANSPORT_SYNC` macro of the application.
- `DOH_LIKE` (default: 0): `DNS_TRANSPORT` $\in$ {`coap`, `coaps`, `oscore`} and `DOH_LIKE=1` the
  client is configured to assume that the Max-Age option carries the value of the minimum
  Time-to-live (TTL) within the DNS response and that the TTLs of the DNS response were not touched
  by the DNS server.
- `ON_BR` (default: 0): Sets the client to run on a 6LoWPAN border router, i.e. the query will go
  out directly over [Ethos] (**Eth**ernet **o**ver **S**erial) and the node will also forward
  messages from downstream nodes in the IoT domain. With that environment variable additional
  environment variables are taken into account:
  + `ETHOS_BAUDTRATE` (default: 115200): The baudrate of the UART interface used for [Ethos]. Sets
    the `ETHOS_BAUDRATE` macro to the given value.
  + `SITE_PREFIX` (default: `2001:db8::/64`): The IPv6 subnet prefix for the downstream interface of
    the border router.
  + `STATIC_ROUTES` (default: 1): If a static route should be configured between the hosting system
    and the border router.
  + `TAP` (default: `tap0`): The TAP interface to use for [Ethos] on the side of the hosting system.
- `ONLY_FETCH` (default: 0): When `DNS_TRANSPORT` $\in$ {`coap`, `coaps`, `oscore`}, the application
  is configured to only provide support for the FETCH method being used. The added complexities for
  POST and GET in particular are stripped from the code. The compilation result with `ONLY_FETCH=1`
  was used to determine the memory usage of the valid `DNS_TRANSPORTS` without GET (*w/o GET*) in
  Section 6.2 and Figure 8. The of the size difference of the `gcoap_dns` module between the
  compilation result with `ONLY_FETCH=0` and `ONLY_FETCH=1` provides the result for the GET overhead
  there.
- `PROXIED` (default: 0): When `DNS_TRANSPORT` $\in$ {`coap`, `coaps`, `oscore`} and `PROXIED=1` the
  logic to add the `Proxy-Uri` option to the CoAP header of the queries is compiled in.
- `QUERY_COUNT` (default: 50): Sets the number of queries the application issues at maximum during
  an experiment run. The `QUERY_COUNT` macro of the application is set to the value of the
  environment variable.
- `WHITELIST_NAME` (unset by default): When set to the name of a C header file, it configures the
  application to use the declaration of a string array of link layer addresses
  `L2_FILTER_WHITE_LIST` in that header file to configure an allowlist for the radio on start-up.
  This is used to ensure the topology of the experiment setup. The header file can look as simple as
  ```C
  #define L2_FILTER_WHITE_LIST { \
    "ba:fc:f8:a1:20:8d:9e:01", \
  }
  ```
  The `WHITELIST_NAME` macro of the application is set to the value of the environment variable.
- `WITH_COAP_CACHE` (default: 0): With `DNS_TRANSPORT` $\in$ {`coap`, `coaps`, `oscore`} and
  `WITH_COAP_CACHE=1` a CoAP cache is provided for the client and includes the
  [`coap_cache.config`](./coap_cache.config) into the configuration of the application.
- `WITH_DNS_CACHE` (default: 0): With `WITH_DNS_CACHE=1` a DNS cache is provided for the client.

In addition to that the following defines are changed from the default configuration:

- `THREAD_STACKSIZE_MAIN` is set to `3 * THREAD_STACKSIZE_DEFAULT`,
- `GNRC_SIXLOWPAN_STACK_SIZE` as well `GNRC_UDP_STACK_SIZE` are set to `THREAD_STACKSIZE_SMALL`, and
- `EVENT_THREAD_STACKSIZE_DEFAULT` is set to `3 * THREAD_STACKSIZE_DEFAULT`.

## Usage
TBD

[Ethos]: https://doc.riot-os.org/group__drivers__ethos.html
[libOSCORE]: https://gitlab.com/oscore/liboscore
