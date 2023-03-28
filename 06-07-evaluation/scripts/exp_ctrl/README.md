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
- The `tests/` directory contains `pytest`-based tests for the python scripts in this directory.
- The `oscore_server_creds/` directory contains the server credentials used by the DoC server in
  these experiments.

## Requirements

The scripts were all tested on Ubuntu 22.04. While the scripts should be possible to run in other
operating systems (especially the Python scripts), we do not guarantee successful execution.

All required python libraries are listed in [`requirements.txt`](./requirements.txt). They can be
installed using [pip] with the commands below.
We recommend installing them to a [Virtualenv] as shown, but it is not strictly necessary.

```sh
virtualenv env
. env/bin/activate
pip install -r requirements.txt
```

You will also require a version of the `ssh` command (e.g. `openssh-client`) to
interact with the IoT-LAB nodes.

`tmux` is required to multiplex the terminal in the background.

You must also configure your IoT-LAB credentials using `iotlab-auth` which is
provided by the `iotlabcli` python package (which is automatically installed
with `iotlab_controller`). See

```sh
iotlab-auth -h
```

for further instructions.

## Experiment types

## Usage

[pip]: https://pip.pypa.io
[Virtualenv]: https://virtualenv.pypa.io
