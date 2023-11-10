# Scripts to conduct experiments

## Overview

The scripts in this directory serve the experiment setup and conduction:

- `create_*_descs.py` scripts are used to create experiment descriptions `descs.yaml` for different
  experiment types.
- `dispatch_*_experiments.py` scripts are used to conduct the experiments using those experiment
  descriptions for different experiment types.
- The `setup_exp.sh` script serves the environment and TMUX session setup for an experiment type. It
  expects the experiment already being described (so one of the `create_*_descs.py` script must have
  been called) and then calls the corresponding `dispatch_*_experiment.py` script in its own TMUX
  window.
- The `tests/` directory contains [pytest]-based tests for the python scripts in this directory.
- The `oscore_server_creds/` directory contains the server credentials used by the DoC server in
  these experiments.

## Requirements

The scripts were all tested on Ubuntu 22.04. While the scripts should be possible to run in other
operating systems (especially the Python scripts), we do not guarantee successful execution.
To run the commands described below, first run, e.g., `apt` on Ubuntu 22.04 to install dependencies:

```
sudo apt update
sudo apt install autoconf curl python3-pip python3-virtualenv
```

The [Arm GNU Toolchain] is needed to build the firmware. The experiments were tested and executed
with version 10.3-2021.07 of the toolchain, but any version compatible with RIOT 2022.07 should
work:

```sh
sudo mkdir -p /opt
sudo curl -sL -o /opt/gcc-arm-none-eabi.tar.bz2 \
    https://developer.arm.com/-/media/Files/downloads/gnu-rm/10.3-2021.07/gcc-arm-none-eabi-10.3-2021.07-x86_64-linux.tar.bz2
sudo echo "b56ae639d9183c340f065ae114a30202 /opt/gcc-arm-none-eabi.tar.bz2" | md5sum -c && \
    sudo tar -C /opt -jxf /opt/gcc-arm-none-eabi.tar.bz2
export PATH="${PATH}:/opt/gcc-arm-none-eabi-10.3-2021.07/bin"
```

RIOT, as well as its `riotctrl` extensions, are needed for the scripts to run. Please make sure to
initialize the [RIOT](../../RIOT) submodule:

```sh
git submodule update --init --recursive
```

All required python libraries are listed in [`requirements.txt`](./requirements.txt). They can be
installed using [pip] with the commands below.
We recommend installing them to a [Virtualenv] as shown, but it is not strictly necessary.

```sh
virtualenv env
. env/bin/activate
pip install -r requirements.txt
```

You will also require a version of the `ssh` command (e.g. [`openssh-client`][OpenSSH]) to
interact with the IoT-Lab nodes.

[`tmux`][Tmux] is required to multiplex the terminal in the background.

You must also configure your IoT-Lab credentials using `iotlab-auth` which is
provided by the `iotlabcli` python package (which is automatically installed
with `iotlab_controller` in `requirements.txt`). See

```sh
iotlab-auth -h
```

for further instructions.

## Testing

The python scripts are tested for python versions 3.7 to 3.11 using [tox]. To test and lint the
code, run the following in this directory ([`05-06-evaluation/scripts/exp_ctrl`](./)). If the python
version under test is installed, the tests for it will be executed.

```sh
tox
```

## Experiment types

Three main [experiment types] are defined for these scripts: `baseline`, `comp`, `max_age`.
Each may have subtypes that mainly determine the number of nodes in the experiments.
These subtypes are only important for the creation of the experiment description, using the
respective `create_max_age_*descs.py` scripts. The `dispatch_max_age_experiments.py` script can be
used for all `max_age` subtypes.

## Usage

### Experiment description
To create a description file (`descs.yaml`) for a number of runs of an [experiment types], just call
the appropriate `create_*_descs.py` script without any arguments. Use the `-h` argument to get
further information on the usage, e.g.:

```sh
./create_baseline_descs.py -h
```

The resulting `descs.yaml` describes the experiment in a format understandable by the
[iotlab_controller] library, which is used by the `./dispatch_*_experiments.py` scripts to control
the experiment progression. It consists of some global definitions (`globals`) and a number of
unscheduled (`unscheduled`) and scheduled (keyed by their FIT IoT-Lab experiment ID) experiment
runs.

The global definitions consist of:
- The experiment duration in the FIT IoT-Lab (`duration`),
- The environment variables needed for all experiments (`env`),
- The firmwares required for the experiment (`firmwares` and `sink_firmware`),
- The name for the experiment in the FIT IoT-Lab (`name`),
- The FIT IoT-Lab nodes used for the experiment (`nodes`),
- The Sniffer profiles for the FIT IoT-Lab nodes (`profiles`), and
- Some more variables mainly used by the controller.

Both scheduled and unscheduled runs are a list of experiment run objects (`runs`) consisting of:
- The runtime arguments for the experiment run (`args`),
- The static (i.e., compile-time) arguments for the experiment run in form of environment variables
  (`env`),
- The link-layer used for the experiment run (`link_layer`),
- The format for the name (used, e.g. for the logs and PCAP files) for the experiment run (`name`),
- Weather or not the app should be rebuilt and reflashed for this run, regardless of static
  arguments (`rebuild`), and
- The time the controller should wait for the experiment run to finish (`wait`)

Note that `unscheduled` can contain a list of `runs` lists. Each list entry then is scheduled as its
own FIT IoT-Lab experiment.

### Running the experiments
The `descs.yaml` file serves as an input to the various `dispatch_*_experiments.py` scripts, e.g.

```sh
./dispatch_baseline_experiments.py <virtualenv>
```

with `<virtualenv>` being a [Virtualenv] directory on the FIT IoT-Lab frontend server that has the
[dependencies](#requirements) for the experiments installed.

To simplify bootstrapping you can also just run

```sh
./setup_exp.sh [<exp_type>]
```

which will take most of the bootstrapping out of your hand. `<exp_type>` is the [experiment types]
(defaulting to `comp`). Note that the experiment type needs to be the same as used for the creation
of `descs.yaml`, otherwise, errors will happen!

The experiments then run in their own [Tmux] session. For each experiment run a log file with the
output and a PCAP file with the sniffed traffic is created in [results](../results) under the name
format given in the respective experiment run object in the `descs.yaml` file.

It might be necessary to sanitize and repeat some experiments, due to the flakiness of the
`serial_aggregator` tool. Use the [`check.awk`](../../results/check.awk) `awk` script (with
`-F';'`), to check the sanity of the log file of a run. If the output is empty, the log is alright.

[pytest]: https://pytest.org
[pip]: https://pip.pypa.io
[Virtualenv]: https://virtualenv.pypa.io
[Tmux]: https://github.com/tmux/tmux/wiki
[OpenSSH]: https://www.openssh.com/
[tox]: https://tox.wiki
[experiment types]: ../README.md#experiment-types
[DoC client]: ../../apps/requester
[forwarder/forward proxy]: ../../apps/proxy
[border router]: https://github.com/RIOT-OS/RIOT/tree/2022.07/examples/gnrc_border_router
[iotlab_controller]: https://github.com/miri64/iotlab_controller
