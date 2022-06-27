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
    from . import parse_proxy_results
except ImportError:
    import plot_common as pc
    import parse_proxy_results

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021-22 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


class LogParser(parse_proxy_results.LogParser):
    # pylint: disable=too-many-instance-attributes
    LOG_EXP_STARTED_PATTERN = r"((Starting run doc-eval-max_age)|(query_bulk exec))"
    LOGNAME_PATTERN = pc.FILENAME_PATTERN_FMT.format(
        exp_type="max_age",
        link_layer=r"(?P<link_layer>ble|ieee802154)",
        max_age_config=r"(?P<max_age_config>min|subtract)",
        transport=r"(?P<transport>coaps?|dtls|udp|oscore)",
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
        if "max_age_config" in kwargs:
            self._max_age_config = kwargs.pop("max_age_config")
        self._last_transmission_reception = None
        super().__init__(*args, **kwargs)

    def _update_response_time(self, line, match, id_, node):
        res = {
            "transport": self.transport,
            "id": id_,
            "node": node,
            "response_time": float(match["time"]),
        }
        if self._last_transmission_reception is not None:
            res["response_transmission"] = self._last_transmission_reception
            self._last_transmission_reception = None
        else:
            raise AssertionError(
                f"Can not any transmission for reception {self.logname}:{line}"
            )
        try:
            if (
                id_,
                node,
                res.get("response_transmission", float("inf")),
            ) not in self._times:
                line = line.strip()
                logging.warning("%s: %s has no out from %s", self, line, node)
        except TypeError:
            print(self.logname, res.get("response_transmission"))
            raise
        return res

    def _update_times_dict(self, id_, node, res):
        resp_trans = res.pop("response_transmission", float("inf"))
        if (id_, node, resp_trans) in self._times:
            self._times[id_, node, resp_trans].update(res)
        else:
            self._times[id_, node, resp_trans] = res

    def _update_from_times2_line(self, line, match):
        msg = match["msg"]
        if msg == "t":
            id_ = int(match["id"])
            node = match["node"]
            if (
                self._last_query.get(node) is not None
                and (id_, node) not in self._transmissions
            ):
                times = self._times.pop((self._last_query[node], node, float("inf")))
                self._times[self._last_query[node], node, id_] = times
                del self._last_query[node]
            elif (id_, node) in self._transmissions:
                times = self._transmissions[id_, node]
            elif match["node"] == self._proxy:
                return None
            else:
                assert (
                    id_,
                    node,
                ) in self._transmissions, (
                    f"{self}: Could not associate transmission {id_} to any query"
                )
            if "transmission_ids" in times:
                if id_ not in times["transmission_ids"]:
                    times["transmission_ids"].append(id_)
            else:
                times["transmission_ids"] = [id_]
            if "transmissions" in times:
                times["transmissions"].append(float(match["time"]))
            else:
                times["transmissions"] = [float(match["time"])]
            self._transmissions[id_, node] = times
            if match["node"] != self._proxy:
                assert (
                    self._transmissions[id_, node]
                    is self._times[times["id"], node, id_]
                )
            return times
        elif msg == "C":
            return self._update_cache_hits(line, match)
        elif msg == "R":
            id_ = int(match["id"])
            node = match["node"]
            self._last_transmission_reception = id_
            try:
                return self._transmissions[id_, node]
            except KeyError as exc:
                raise AssertionError(f"Unable to find transmission for {line}") from exc
        return None


class ThreadableParser(parse_proxy_results.ThreadableParser):
    # pylint: disable=too-few-public-methods
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
