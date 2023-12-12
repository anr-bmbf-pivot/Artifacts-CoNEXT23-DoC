#! /usr/bin/env python3

# Copyright (C) 2021-22 Freie Universität Berlin
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
    from . import parse_baseline_results
except ImportError:  # pragma: no cover
    import plot_common as pc
    import parse_baseline_results

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021-22 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


class LogParser(parse_baseline_results.LogParser):
    # pylint: disable=too-many-instance-attributes
    LOG_EXP_STARTED_PATTERN = r"((Starting run doc-eval-comp)|(query_bulk exec ))"
    LOGNAME_PATTERN = pc.FILENAME_PATTERN_FMT.format(
        exp_type="comp",
        node_num=r"(?P<node_num>\d+)",
        link_layer=r"(?P<link_layer>ble|ieee802154)",
        max_age_config=r"dohlike",
        transport=r"(?P<transport>coaps?|dtls|udp|oscore)",
        method=r"(?P<method>fetch|get|post)",
        dns_cache="",
        client_coap_cache="",
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
    _TIMES_FIELDNAMES = [
        "transport",
        "node",
        "id",
        "query_time",
        "response_time",
        "transmission_ids",
        "transmissions",
        "cache_hits",
        "client_cache_hits",
    ]

    def __init__(self, *args, **kwargs):
        if "proxied" in kwargs:
            self._proxied = int(kwargs.pop("proxied"))
        else:
            self._proxied = 0
        if "node_num" in kwargs:
            try:
                self._node_num = int(kwargs.pop("node_num"))
            except TypeError:
                self._node_num = None
        else:
            self._node_num = None
        self._last_query = {}
        self._last_dns_cache_hit = {}
        super().__init__(*args, **kwargs)
        self._proxies = set()
        self._proxy_transmissions = {}
        self._empty_acked = {}
        self._proxy_cache_hits = {}
        self._c_proxy = re.compile(self.LOG_PROXY)

    def _update_cache_hits(self, line, match):
        id_ = int(match["id"])
        if match["node"] in self._proxies:
            stat = "cache_hits"
        else:
            stat = "client_cache_hits"
        for key in reversed(sorted(self._times)):
            if id_ in self._times[key].get("transmission_ids", {}):
                times = self._times[key]
                if stat not in times:
                    times[stat] = []
                times[stat].append(float(match["time"]))
                return times
        for key in self._proxy_transmissions:
            if id_ != key:
                continue
            if id_ not in self._proxy_cache_hits:
                self._proxy_cache_hits[id_] = []
            self._proxy_cache_hits[id_].append(float(match["time"]))
            return None
        logging.warning(
            "Could not associate cache hit %s with any transmission",
            line.strip(),
        )
        return None

    def _add_proxy_transmission(self, match):
        id_ = int(match["id"])
        if id_ not in self._proxy_transmissions:
            self._proxy_transmissions[id_] = []
        self._proxy_transmissions[id_].append(float(match["time"]))
        return None

    def _was_empty_acked(self, match):
        id_ = int(match["id"])
        node = match["node"]
        self._empty_acked[node] = id_
        return None

    def _add_con_response(self, line, match):
        id_ = int(match["id"])
        node = match["node"]
        assert (
            node in self._empty_acked
        ), f"CON for {id_} found even though it was not empty ACK'd"
        times = None
        for key in reversed(sorted(self._times)):
            empty_acked = self._empty_acked[node]
            if empty_acked not in self._times[key].get("transmission_ids", []):
                continue
            times = self._times[key]
            times["transmission_ids"].append(id_)
            return times
        logging.warning(
            "Could not associate CON response %s with any transmission",
            line.strip(),
        )
        return None

    def _update_from_times2_line(self, line, match):
        assert self._proxies, f"No proxy found in log {self.logname}"
        msg = match["msg"]
        if msg == "C" or (msg == "c" and match["node"] in self._proxies):
            return self._update_cache_hits(line, match)
        if msg == "P":
            return self._was_empty_acked(match)
        if msg == "A":
            return self._add_con_response(line, match)
        if msg == "t" and match["node"] in self._proxies:
            return self._add_proxy_transmission(match)
        try:
            times = super()._update_from_times2_line(line, match)
            id_ = int(match["id"])
            node = match["node"]
            if (
                msg == "t"
                and id_ in self._proxy_cache_hits
                and node not in self._proxies
            ):
                if "cache_hits" not in times:
                    times["cache_hits"] = []
                times["cache_hits"].extend(self._proxy_cache_hits[id_])
                times["cache_hits"].sort()
        except AssertionError:
            if match["node"] in self._proxies:
                return None
            raise
        return times

    def _parse_proxy(self, line):
        match = self._c_proxy.match(line)
        if match:
            self._proxies.add(match["node"])


class ThreadableParser(parse_baseline_results.ThreadableParser):
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
    main()  # pragma: no cover
