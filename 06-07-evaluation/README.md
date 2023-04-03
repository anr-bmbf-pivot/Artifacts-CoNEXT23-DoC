# Comparison of Low-power DNS Transports & Evaluation of Caching for DoC
This directory contains the device applications, scripts, plots, and data aggregates used for
Section 6 _Comparison of Low-power DNS Transports_ and Section 7 _Evaluation of Caching for DoC_ of
the paper.



## Overview

### Experiment types

There are three main experiment types that can be conducted and evaluated with the artifacts in this
directory.


##### `baseline`

![The `baseline` setup.](figs/setup-baseline.svg)

A simple set-up with a single [DoC client] separated by a single hop to the border router. We used
this experiment types primarily to validate our implementation.

##### `comp`

![The `comp` setup.](figs/setup-comp.svg)

The experiment type we used for our evaluation in Section 6 _Comparison of Low-power Transports_,
i.e., at least 2 [DoC client] that query 50 records from a DoC server via a [forwarder/forward
proxy] and [border router] without any caching. There are 4 subtypes of this experiment type:

- `comp`: The base setup from our paper with 2 DoC clients. This is the subtype presented in the
  paper and depicted in the figure above.
- `comp_8`: A setup with 6 DoC clients (to a total of 8 nodes with forwarder/proxy and border
  router).
- `comp_24`: A setup with 22 DoC clients (to a total of 24 nodes with forwarder/proxy and border
  router).

##### `max_age`

![The `max_age` setup.](figs/setup-max_age.svg)

The experiment type we used for our evaluation in Section 7 _Evaluation of Caching for DoC_, i.e.,
at least 2 [DoC client] that query 50 records for 8 distinct names from a DoC server via a
[forwarder/forward proxy] and [border router] with different caching scenarios. There are 4 subtypes
of this experiment type:

- `max_age`: The base setup from our paper with 2 DoC clients. This is the subtype presented in the
  paper and depicted in the figure above.
- `max_age_8`: A setup with 6 DoC clients (to a total of 8 nodes with forwarder/proxy and border
   router).
- `max_age_24`: A setup with 22 DoC clients (to a total of 24 nodes with forwarder/proxy and
   border router).

### [`./RIOT`](./RIOT)
A [Git submodule] import of [RIOT 2022.07] with the necessary Pull Requests and patches applied on
top. Namely, this includes the patches in [`./riot-patches`](./riot-patches) and the following Pull
Requests:

- [#16861](https://github.com/RIOT-OS/RIOT/pull/16861)
- [#18329](https://github.com/RIOT-OS/RIOT/pull/18329)
- [#18381](https://github.com/RIOT-OS/RIOT/pull/18381)
- [#18386](https://github.com/RIOT-OS/RIOT/pull/18386)
- [#18441](https://github.com/RIOT-OS/RIOT/pull/18441)
- [#18443](https://github.com/RIOT-OS/RIOT/pull/18443)
- [#18471](https://github.com/RIOT-OS/RIOT/pull/18471)

### [`./riot-patches`](./riot-patches)
[Git patches] to RIOT required for the experiments that did not result in an upstream Pull Request.

### [`cherry-pick-prs.sh`](./cherry-pick-prs.sh)
A script that can be used to reproduce the state of [`./RIOT`](./RIOT). It fetches [RIOT 2022.07]
from the main RIOT GitHub repo, resets the submodule to that release and then [cherry-picks][git
cherry-pick] the Pull Request first and then [applies][git am] the patches from
[`./riot-patches`](./riot-patches) to it.

### [`./liboscore`](./liboscore)
A [Git submodule] import of [libOSCORE].

### [`./apps`](./apps)
Contains the dedicated RIOT applications used for our experiments:

- [`./apps/requester`](./apps/requester) is the DNS client application used for all our experiments.
- [`./apps/proxy`](./apps/proxy) is the opaque forwarder and forward proxy application used for the
  [`comp` and `max_age` experiments][experiment types]

We also used the [border router example][border router] from the [`./RIOT`](./RIOT) submodule as the
border router.

### [`./scripts`](./scripts)
Contains the scripts to conduct and evaluate the experiments:

- [`./scripts/exp_ctrl`](./scripts/exp_ctrl) contains scripts for conducting the experiments.
- [`./scripts/plots`](./scripts/plots) contains scripts to parse the output of the `exp_ctrl`
  scripts and generate plots from them.

### [`./results`](./results)
Contains the outputs of the scripts in [`./scripts`](./scripts). Results not taken into account for
our paper are listed in subdirectories `<discard ISO date>-<reason for discard>`.

In addition to the results there is an [AWK] script [`./results/check.awk`] that can check the
output logs generated by the RIOT applications for correctness. Due to syncing issues between the
`stdio` of RIOT and FIT IoT-LAB characters might get lost in rare cases, skewing the evaluation.
This script used to spot these errors, but also unusual timeouts due to crashed or resource-drained
nodes.

### [`./figs`](./figs)
Contains the figures used in this README.

[DoC client]: ./apps/requester
[forwarder/forward proxy]: ./apps/proxy
[border router]: https://github.com/RIOT-OS/RIOT/tree/2022.07/examples/gnrc_border_router
[Git submodule]: https://git-scm.com/book/en/v2/Git-Tools-Submodules
[RIOT 2022.07]: https://github.com/RIOT-OS/RIOT/releases/tag/2022.07
[Git patches]: https://git-scm.com/docs/git-format-patch
[git cherry-pick]: https://git-scm.com/docs/git-cherry-pick
[git am]: https://git-scm.com/docs/git-am
[libOSCORE]: https://oscore.gitlab.io/liboscore/
[AWK]: https://pubs.opengroup.org/onlinepubs/9699919799/utilities/awk.html