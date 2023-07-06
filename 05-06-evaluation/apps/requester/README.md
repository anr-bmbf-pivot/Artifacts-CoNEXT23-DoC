# Requester application

This is the application for the clients for the evaluation in Sections 5, *Comparison of
Low-Power DNS Transports*, and 6, *Evaluation of Caching for DoC*, of the Paper. On command,
it will asynchronously query for a given number of times, names from a pre-configured upstream DNS
server.

## Requirements

This application needs an embedded toolchain installed:

- For the IoT-LAB-based platform (`iotlab-m3`), the [Arm GNU Toolchain] is needed. The original
  experiments were run with version 10.3-2021.07.
- For ESP32-based platforms, the [Espressif Crosstool NG] is needed. Compiling was tested for
  version esp-2021r2-patch3. However, it is unlikely, that the apps run properly, when flashed to
  such a platform, as it uses different network devices from the ones used during the experiments.

## Compile-time configuration

The base configuration for this application in Kconfig can be found in [`app.config`](./app.config).

There are multiple compile time configurations which are switchable via environment variables to
suit the parametrization for our experiments. These environment variables can also imply the
inclusion of additional configuration files to Kconfig.

- `DNS_TRANSPORTS` (default: "`udp`"): Sets the transport used for DNS messages. Either of the
  following values are expected:
  + `udp`: Sets the macro `DNS_TRANSPORT` to `DNS_TRANSPORT_UDP`. The application will use
    **unencrypted DNS over UDP** to query for names.
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
- `ONLY_FETCH` (default: 0): When set to one `DNS_TRANSPORT` $\in$ {`coap`, `coaps`, `oscore`}, the
  application is configured to only provide support for the FETCH method being used. The added
  complexities for POST and GET in particular are stripped from the code. The compilation result
  with `ONLY_FETCH=1` was used to determine the memory usage of the valid `DNS_TRANSPORTS` without
  GET (*w/o GET*) in Section 5.2 and Figure 5. The size difference of the `gcoap_dns` module between
  the compilation result with `ONLY_FETCH=0` and `ONLY_FETCH=1` provides the result for the GET
  overhead there.
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
- `GCOAP_APP` (default: 0): Adds the application code in [gcoap-app.c](./gcoap-app.c) which based on
  the [RIOT gcoap example]. This can be used to gauge the overhead of the DNS code when having a
  CoAP application as done in Section 5.2 and Figure 5.

In addition to that the following defines are changed from the default configuration:

- `THREAD_STACKSIZE_MAIN` is set to `3 * THREAD_STACKSIZE_DEFAULT`,
- `GNRC_SIXLOWPAN_STACK_SIZE` as well `GNRC_UDP_STACK_SIZE` are set to `THREAD_STACKSIZE_SMALL`, and
- `EVENT_THREAD_STACKSIZE_DEFAULT` is set to `3 * THREAD_STACKSIZE_DEFAULT`.

## Usage

After flashing the application to a device (see [RIOT documentation]), the experiment can be
controlled using shell commands.

### Setup
To check if a global address is configured, the following command can be used.

```
ifconfig
```

The address should be listed under the global IPv6 addresses.

The `init` command can be used to initialize the stub resolver:

```
init <resolver> [<DTLS PSK tag> <DTLS PSK client ID> <DTLS PSK secret>]
```

`<resolver>` is to be expected in the format `[ipv6_address]:port`, with the `:port` being optional (the default port of the transport is used in the case of the port not being present).

To configure a proxy for the client use

```
proxy <proxy URI>
```

The `<proxy URI>` must be a valid CoAP URI.

The B1 encryption context for OSCORE is configured with the `userctx` command:

```
userctx <alg> <sender-id> <recipient-id> <common-iv> <sender-key> <recipient-key>
```

Except for `<alg>`, which is expected to be a decimal integer number, all parameters are expected to
be hexadecimal strings.
See `gcoap_dns_oscore_set_secctx()` in the `gcoap_dns` module of RIOT for more information.

### Resolving names

Use the `query` command to resolve _one_ name synchronous:

```
query <hostname> <family> [<method>]
```

`<hostname>` is the name that is to be resolved. `<family>` determines the requested resource
record: `inet` requests an `A` record, `inet6` requests an `AAAA` record. `<method>` is optional and
only sensible in usage with CoAP-based transports. It defaults to `"fetch"` and can either be
`"get"`, `"post"`, or `"fetch"`.

`query_bulk` is used to resolve multiple names asynchronously.

```
query_bulk add <delay in ms>
```

Adds a future query to a queue. Its sending will be delayed by `<delay in ms>` to the previous
query or from the calling of `query_bulk exec` when it is the first in the queue. Up to
`QUERY_COUNT` queries can be added to the queue.

```
query_bulk reset
```

Removes all queries from the queue.

The `query_bulk exec` command starts the process of sending the queries in the queue.

```
query_bulk exec <hostname> <family> [[<method>] <mod>]
```

For the most part, the parameters are the same as with the synchronous `query`
command with two exceptions:
- `<hostname>` is prepended with a running counter of queries sent
  (front-padded with up to 4 zeroes), i.e., the first query in the queue will
  be for the name `00000.<hostname>`, the second `00001.<hostname>`, and so on. This ensures that
  each queried name is unique during the experiment run.
- `<mod>` provides a modulo to that running counter. This way a name is requested multiple times
  during an experiment run.

### Output
For performance reasons, the applications prints only a code and an identifier (ID) on certain
events. The timestamp provided by the [serial_aggregator] of the FIT IoT-Lab can be used to
determine the time difference between those events. The meaning of each code can be found below:

- `b`: A CoAP request was sent block-wise. The ID printed is the CoAP MID.
- `b2`: A block-wise CoAP response was received. The ID printed is the CoAP MID.
- `c`: A "2.31 Continue" CoAP response was received to trigger the sending of another block of an
  outstanding block-wise CoAP request. The ID printed is the CoAP MID.
- `c2`: A CoAP request to continue a block-wise CoAP response was received. The ID printed is the
  CoAP MID.
- `C`: A CoAP response was taken from the CoAP cache (either due to a cache hit or because a stale
  cache entry was re-validated, `V` is used to distinguish the two events exactly). The ID printed
  is the CoAP MID.
- `d`: A DNS response was received with a transport ID for which no transport was used. The ID
  printed is the ID of the transport for the response (e.g. the MID with CoAP)
- `D`: A DNS cache hit. The ID printed is the first five characters of the
  queried hostname (e.g. the running counter prepended by the `query_bulk`
  command).
- `e`: An error occurred. The ID printed is the `errno` of the error.
- `q`: A DNS query is just about to be issued by the AP. The ID printed is the first five characters
  of the queried hostname (e.g. the running counter prepended by the `query_bulk` command).
- `r`: The DNS response was received, parsed, and contains an A or AAAA record. The ID printed is
  the first five characters of the queried hostname (e.g. the running counter prepended by the
  `query_bulk` command).
- `R`: The DNS transport response was received and parsed. The ID printed is the ID of the transport
  for the response (e.g. the MID with CoAP).
- `t`: A transport message for a query was issued (either initial transmission or retransmission).
  This includes messages that might cause a cache hit and are thus never sent via the medium, use
  `C` to distinguish these from real transmissions.
  The ID printed is the ID of the transport for the query (e.g. the MID with CoAP).
- `u`: An "4.01 Unauthorized" CoAP response was received. The ID printed is the CoAP MID.
- `V`: A stale cache entry was validated. The ID printed is the CoAP MID.
- `x`: A DNS query timed out. The ID printed is the ID of the transport for the query (e.g. the MID
  with CoAP).

[Arm GNU Toolchain]: https://developer.arm.com/downloads/-/gnu-rm
[Espressif Crosstool NG]: https://github.com/espressif/crosstool-NG/releases
[Ethos]: https://doc.riot-os.org/group__drivers__ethos.html
[libOSCORE]: https://gitlab.com/oscore/liboscore
[RIOT gcoap example]: https://github.com/RIOT-OS/RIOT/tree/2022.07/examples/gcoap
[RIOT documentation]: https://doc.riot-os.org/getting-started.html
[serial_aggregator]: https://iot-lab.github.io/docs/tools/serial-aggregator
