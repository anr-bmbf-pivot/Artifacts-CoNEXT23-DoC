#! /usr/bin/env python3

# Copyright (C) 2022 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.


import argparse
import logging
import os


import coloredlogs

try:
    from . import dispatch_proxy_experiments as dpe
    from . import dispatch_load_experiments as dle
except ImportError:
    import dispatch_proxy_experiments as dpe
    import dispatch_load_experiments as dle

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2022 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"

QUERY_MODULO = 8
TTL = (2, 8)

logger = logging.getLogger(__name__)


class Runner(dle.Runner):
    def get_tmux_cmds(self, run):  # pylint: disable=unused-argument
        if self.resolver_running:
            record_type, method = self.get_args(run)
            yield (
                f"query_bulk exec id.exp.example.org {self.family[record_type]} "
                f"{method} {QUERY_MODULO}"
            )
        else:
            yield "ERROR: RESOLVER NOT RUNNING!"


class Dispatcher(dpe.Dispatcher):
    _EXPERIMENT_RUNNER_CLASS = Runner

    def __new__(cls, *args, **kwargs):
        cls = super().__new__(cls)
        cls._RESOLVER_CONFIG["transports"]["coap"]["use_etag"] = True
        cls._RESOLVER_CONFIG["mock_dns_upstream"]["ttl"] = TTL
        cls._RESOLVER_CONFIG["mock_dns_upstream"]["IN"]["AAAA"] = [
            cls._DNS_AAAA_RECORD,
            cls._DNS_AAAA_RECORD.replace("::7", "::8"),
            cls._DNS_AAAA_RECORD.replace("::7", "::9"),
            cls._DNS_AAAA_RECORD.replace("::7", "::10"),
        ]
        return cls

    def pre_run(self, runner, run, ctx, *args, **kwargs):
        self._RESOLVER_CONFIG["transports"]["coap"]["max_age"] = run["args"][
            "max_age_mode"
        ]
        return super().pre_run(runner, run, ctx, *args, **kwargs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "virtualenv", default=dle.VIRTUALENV, help="Virtualenv for the Python resolver"
    )
    parser.add_argument(
        "descs",
        nargs="?",
        default=os.path.join(dle.SCRIPT_PATH, "descs.yaml"),
        help="Experiment descriptions file",
    )
    parser.add_argument(
        "--limit-unscheduled",
        "-l",
        type=int,
        help=(
            "Limits the number of unscheduled experiments to "
            "be scheduled before each run"
        ),
    )
    parser.add_argument(
        "-v", "--verbosity", default="INFO", help="Verbosity as log level"
    )
    args = parser.parse_args()
    coloredlogs.install(level=getattr(logging, args.verbosity), milliseconds=True)
    logger.debug("Running %s", args.descs)
    dispatcher = Dispatcher(
        args.descs, virtualenv=args.virtualenv, verbosity=args.verbosity
    )
    dispatcher.load_experiment_descriptions(limit_unscheduled=args.limit_unscheduled)


if __name__ == "__main__":
    main()
