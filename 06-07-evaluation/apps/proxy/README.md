# Forwarder/forward proxy application

This is the application for the forwarder and forward proxy for the evaluation in Sections 6,
*Comparison of Low-Power DNS Transports*, and 7, *Evaluation of Caching for DoC*, of the Paper. It
just needs to be en route between the client and the border router, and does not need to be
dynamically configured on its own in any way.

## Compile-time configuration

The base configuration for this application in Kconfig can be found in [`app.config`](./app.config).

There are multiple compile time configurations which are switchable via environment variables to
suit the parametrization of our experiments.

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

In addition to that the following defines are changed from the default configuration:

- `GCOAP_STACK_SIZE` is set to `2 * THREAD_STACKSIZE_DEFAULT`,

## Usage

After flashing the application to a device (see [RIOT documentation]), it is ready to use. The
deciding factor if this node acts as a forwarder or forward proxy is the usage of [the `proxy`
command at the client](../requester/README.md#setup).

### Output
For performance reasons, the applications prints only a code and an identifier (ID) on certain
events. The timestamp provided by the [serial_aggregator] of the FIT IoT-Lab can be used to
determine the time difference between those events. In addition to the codes listed in the
[`requester` app](../requester/README.md##output), there are also codes specific to the CoAP
forward proxy:

- `P`: A response for a request that was already ACK'd is about to be sent. The ID is the original
  CoAP MID of the request.
- `A`: A response for a request that was already ACK'd is about to be sent. The ID is the new CoAP
  MID that was issued by the proxy for the CON response.

[serial_aggregator]: https://iot-lab.github.io/docs/tools/serial-aggregator
