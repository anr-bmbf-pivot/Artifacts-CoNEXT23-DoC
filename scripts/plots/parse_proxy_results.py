#! /usr/bin/env python3

# Copyright (C) 2021 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import argparse
import logging
import re
import os
import multiprocessing
import random

try:
    from . import plot_common as pc
    from . import parse_load_results
except ImportError:
    import plot_common as pc
    import parse_load_results

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


class LogParser(parse_load_results.LogParser):
    # pylint: disable=too-many-instance-attributes
    LOGNAME_PATTERN = pc.FILENAME_PATTERN_FMT.format(
        exp_type="proxy",
        link_layer=r"(?P<link_layer>ble|ieee802154)",
        transport=r"coap",
        method=r"(?P<method>fetch|get|post)",
        blocksize=r"(?P<blocksize>\d+|None)",
        proxied=r"(?P<proxied>[01])",
        delay_time=r"None",
        delay_queries=r"None",
        queries=r"(?P<queries>\d+)",
        record=r"(?P<record>A{1,4})",
        avg_queries_per_sec=r"(?P<avg_queries_per_sec>\d+.\d+)",
    )
    LOG_PROXY = (
        r"(?P<time>\d+.\d+);(?P<node>(m3|nrf52\d*dk)-\d+);"
        r"shell: command not found: query_bulk"
    )
    _LOG_NAME_C = re.compile(f"{LOGNAME_PATTERN}.log")

    def __init__(self, *args, **kwargs):
        if "proxied" in kwargs:
            self._proxied = int(kwargs.pop("proxied"))
        super().__init__(*args, **kwargs)
        self._proxy = None
        self._c_proxy = re.compile(self.LOG_PROXY)

    def _update_from_times2_line(self, line, match):
        assert self._proxy, "No proxy found in log"
        return []
        # super()._update_from_times2_line(line, match)

    def _parse_proxy(self, line):
        match = self._c_proxy.match(line)
        if match:
            self._proxy = match["node"]


class ThreadableParser(parse_load_results.ThreadableParser):
    @staticmethod
    def the_target(logname, data_path=pc.DATA_PATH):
        parser = LogParser.match(logname, data_path=data_path)
        if parser:
            parser.log_to_csvs()


def logs_to_csvs(data_path=pc.DATA_PATH):
    threads = []
    for logname in os.listdir(data_path):
        kwargs = {
            "logname": logname,
            "data_path": data_path,
        }
        thread = ThreadableParser(target=ThreadableParser.the_target, kwargs=kwargs)
        threads.append(thread)
        thread.start()
        if len(threads) > (multiprocessing.cpu_count() * 2):
            threads[random.randint(0, len(threads) - 1)].join()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbosity", default="INFO")
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.verbosity))
    logs_to_csvs()


if __name__ == "__main__":
    main()
