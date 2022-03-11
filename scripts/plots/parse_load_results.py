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
import csv
import datetime
import logging
import re
import os
import multiprocessing
import random
import threading

try:
    from . import plot_common as pc
except ImportError:
    import plot_common as pc

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


class LogError(Exception):
    pass


class LogParser:
    # pylint: disable=too-many-instance-attributes
    LOGNAME_PATTERN = pc.FILENAME_PATTERN_FMT.format(
        exp_type="load",
        link_layer=r"(?P<link_layer>ble|ieee802154)",
        transport=r"(?P<transport>coaps?|dtls|udp|oscore)",
        method=r"(?P<method>fetch|get|post)",
        blocksize=r"(?P<blocksize>\d+|None)",
        proxied=r"0",
        delay_time=r"(?P<delay_time>(\d+\.\d+|None))",
        delay_queries=r"(?P<delay_queries>(\d+|None))",
        queries=r"(?P<queries>\d+)",
        record=r"(?P<record>A{1,4})",
        avg_queries_per_sec=r"(?P<avg_queries_per_sec>\d+.\d+)",
    )

    LOG_EXP_STARTED_PATTERN = r"((Starting run doc-eval-load)|(query_bulk exec \d+))"
    LOG_DATA_PATTERN = (
        r"(?P<time>\d+.\d+);(?P<node>(m3|nrf52\d*dk)-\d+);"
        r"(> ?)?(?P<msg>(q|r));(?P<id>\d+)\b"
    )
    LOG_DATA2_PATTERN = (
        r"(?P<time>\d+.\d+);(?P<node>(m3|nrf52\d*dk)-\d+);"
        r"(> ?)?(?P<msg>(t|u|c2?|b2?|R));(?P<id>\d+)"
    )
    LOG_L2_RX_PATTERN = (
        r"(\d+.\d+;(?P<node>(m3|nrf52\d*dk)-\d+);)?.*"
        r"RX packets (?P<l2_received>\d+)\b"
    )
    LOG_L2_TX_PATTERN = (
        r"(\d+.\d+;(?P<node>(m3|nrf52\d*dk)-\d+);)?.*"
        r"TX packets (?P<l2_sent>\d+) \(Multicast: (?P<l2_multicast>\d+)\)"
    )
    LOG_L2_SUCCESS_PATTERN = (
        r"(\d+.\d+;(?P<node>(m3|nrf52\d*dk)-\d+);)?.*"
        r"TX succeeded (?P<l2_success>\d+) errors (?P<l2_error>\d+)\b"
    )
    _LOG_NAME_C = re.compile(f"{LOGNAME_PATTERN}.log")
    _STATS_FIELDNAMES = [
        "node",
        "l2_sent",
        "l2_received",
        "l2_success",
        "l2_multicast",
        "l2_error",
    ]
    _TIMES_FIELDNAMES = [
        "transport",
        "node",
        "id",
        "query_time",
        "response_time",
        "transmission_ids",
        "transmissions",
        "unauth_time",
    ]

    def __init__(
        self,
        logname,
        transport=None,
        link_layer=None,
        method=None,
        blocksize=None,
        delay_time=None,
        delay_queries=None,
        queries=None,
        avg_queries_per_sec=None,
        record=None,
        exp_id=None,
        timestamp=None,
        border_router=None,
        data_path=pc.DATA_PATH,
    ):
        # pylint: disable=too-many-arguments,unused-argument
        self.data_path = data_path
        self._logname = logname
        self.transport = transport
        self.link_layer = link_layer
        if record is None:
            self.record = "AAAA"
        else:
            self.record = "A"
        self.exp_id = int(exp_id) if exp_id is not None else exp_id
        if timestamp:
            self.timestamp = datetime.datetime.fromtimestamp(int(timestamp))
        else:
            self.timestamp = None
        if border_router is None:
            self.border_router = False
            self._experiment_started = False
        else:
            self.border_router = True
            self._experiment_started = True
        self._times = {}
        self._stats = {}
        self._transmissions = {}
        self._last_query = {}
        self._last_unauth = {}
        self._last_block = {}
        self._last_cont = {}
        self._c_started = re.compile(self.LOG_EXP_STARTED_PATTERN)
        self._c_data = re.compile(self.LOG_DATA_PATTERN)
        self._c_data2 = re.compile(self.LOG_DATA2_PATTERN)
        self._c_l2_rx = re.compile(self.LOG_L2_RX_PATTERN)
        self._c_l2_tx = re.compile(self.LOG_L2_TX_PATTERN)
        self._c_l2_success = re.compile(self.LOG_L2_SUCCESS_PATTERN)

    def __repr__(self):
        return f"<{type(self).__name__} '{self.logname}'>"

    def __str__(self):
        return self.logname

    @classmethod
    def match(cls, filename, data_path=None):
        """
        >>> LogParser.match('doc-eval-load-udp-None-None-100x10.0-'
        ...                 '283991-1635368397.log', data_path='./')
        <LogParser './doc-eval-load-udp-None-None-100x10.0-283991-1635368397.log'>
        >>> LogParser.match('doc-eval-load-coaps-1.0-25-100x5.0-'
        ...                 '284361-1635778024.log', data_path='./')
        <LogParser './doc-eval-load-coaps-1.0-25-100x5.0-284361-1635778024.log'>
        >>> LogParser.match('doc-eval-load-oscore-fetch-1.0-25-100x5.0-'
        ...                 '284361-1635778024.log', data_path='./')
        <LogParser './doc-eval-load-oscore-fetch-1.0-25-100x5.0-284361-1635778024.log'>
        >>> LogParser.match('doc-eval-load-coap-post-1.0-25-100x5.0-'
        ...                 '284361-1635778024.log', data_path='./')
        <LogParser './doc-eval-load-coap-post-1.0-25-100x5.0-284361-1635778024.log'>
        >>> LogParser.match('doc-eval-load-coaps-get-1.0-25-100x5.0-'
        ...                 '284361-1635778024.log', data_path='./')
        <LogParser './doc-eval-load-coaps-get-1.0-25-100x5.0-284361-1635778024.log'>
        >>> LogParser.match('doc-eval-load-coaps-get-1.0-25-100x5.0-'
        ...                 '284361-1635778024.border-router.log', data_path='./')
        <LogParser './doc-eval-load-coaps-get-1.0-25-100x5.0-284361-1635778024.border-router.log'>
        """  # noqa: E501
        match = cls._LOG_NAME_C.match(filename)
        if match is not None:
            return cls(filename, data_path=data_path, **match.groupdict())
        return None

    @property
    def logname(self):
        return os.path.join(self.data_path, self._logname)

    @property
    def times_csv(self):
        """
        >>> LogParser('test.log', data_path='./').times_csv
        './test.times.csv'
        """
        return f"{self.logname[:-4]}.times.csv"

    @property
    def stats_csv(self):
        """
        >>> LogParser('test.log', data_path='./').stats_csv
        './test.stats.csv'
        """
        return f"{self.logname[:-4]}.stats.csv"

    def _get_times_csv_writer(self, times_csvfile):
        times_csv = csv.DictWriter(
            times_csvfile, fieldnames=self._TIMES_FIELDNAMES, delimiter=";"
        )
        times_csv.writeheader()
        return times_csv

    def _get_stats_csv_writer(self, stats_csvfile):
        stats_csv = csv.DictWriter(
            stats_csvfile, fieldnames=self._STATS_FIELDNAMES, delimiter=";"
        )
        stats_csv.writeheader()
        return stats_csv

    def _write_csvs(self):
        if self._times:
            with open(self.times_csv, "w", encoding="utf-8") as times_csvfile:
                times_csv = self._get_times_csv_writer(
                    times_csvfile,
                )
                for row in self._times.values():
                    times_csv.writerow(row)
        if self._stats:
            with open(self.stats_csv, "w", encoding="utf-8") as stats_csvfile:
                stats_csv = self._get_stats_csv_writer(
                    stats_csvfile,
                )
                for row in self._stats.values():
                    stats_csv.writerow(row)

    def _check_experiment_started(self, line):
        match = self._c_started.search(line)
        if match:
            self._experiment_started = True
            return match.groupdict()
        return None

    def _add_blockwise_transmission(self, match):
        id_ = int(match["id"])
        node = match["node"]
        if (
            self._last_query.get(node) is not None
            and (id_, node) not in self._transmissions
        ):
            times = self._times[self._last_query[node], node]
            del self._last_query[node]
        elif self._last_cont.get(node) is not None and id_ not in self._transmissions:
            times = self._transmissions[self._last_cont[node], node]
            del self._last_cont[node]
        else:
            assert (
                id_,
                node,
            ) in self._transmissions, (
                f"{self}: Could not associate blockwise transfer {id_} to any query"
            )
        if "transmission_ids" in times:
            if id_ not in times["transmission_ids"]:
                times["transmission_ids"].append(id_)
        else:
            times["transmission_ids"] = [id_]
        self._last_block[node] = id_
        self._transmissions[id_, node] = times
        assert self._transmissions[id_, node] is self._times[times["id"], times["node"]]
        return times

    def _update_from_times2_line(self, line, match):
        msg = match["msg"]
        if msg == "t":
            id_ = int(match["id"])
            node = match["node"]
            if (
                self._last_block.get(node) is not None
                and (id_, node) not in self._transmissions
            ):
                times = self._transmissions[self._last_block[node], node]
                del self._last_block[node]
            elif (
                self._last_query.get(node) is not None
                and (id_, node) not in self._transmissions
            ):
                times = self._times[self._last_query[node], node]
                del self._last_query[node]
            elif (
                self._last_unauth.get(node) is not None
                and id_ not in self._transmissions
            ):
                times = self._transmissions[self._last_unauth[node], node]
                del self._last_unauth[node]
            elif (id_, node) in self._transmissions:
                times = self._transmissions[id_, node]
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
            assert self._transmissions[id_, node] is self._times[times["id"], node]
        elif msg in ["b", "b2"]:
            times = self._add_blockwise_transmission(match)
        elif msg in ["c", "c2"]:
            id_ = int(match["id"])
            node = match["node"]
            assert (
                id_,
                node,
            ) in self._transmissions, (
                f"{self}: Could not associate continue response {id_} to any query"
            )
            times = self._transmissions[id_, node]
            self._last_cont[node] = id_
        elif msg == "u":
            id_ = int(match["id"])
            node = match["node"]
            if (id_, node) in self._transmissions:
                times = self._transmissions[id_, node]
            else:
                assert (
                    id_,
                    node,
                ) in self._transmissions, f"{self}: Could not associate unauthorized "
                f"response {id_} to any query"
            assert (
                "unauth_time" not in times
            ), f"{self}: Unauthorized for {id_} already registered"
            times["unauth_time"] = float(match["time"])
            self._last_unauth[node] = id_
            self._transmissions[id_, node] = times
            assert (
                self._transmissions[id_, node]
                is self._times[times["id"], times["node"]]
            )
        return times

    def _parse_times_line(self, line):
        """
        >>> parser = LogParser('test.log', transport='udp')
        >>> parser._parse_times_line(
        ...     '1633695050.906918;m3-281;q;3911.h.fr',
        ... )
        {'transport': 'udp', 'id': 3911, 'node': 'm3-281', 'query_time': 1633695050.906918}
        >>> parser._parse_times_line(
        ...     '1633695050.981532;m3-281;> r;3911.h.fr',
        ... )
        {'transport': 'udp', 'id': 3911, 'node': 'm3-281', 'response_time': 1633695050.981532}
        >>> parser._parse_times_line(
        ...     '1633695064.180100;m3-281;r;3973.h.fr'
        ... )
        {'transport': 'udp', 'id': 3973, 'node': 'm3-281', 'response_time': 1633695064.1801}
        """  # noqa: E501
        match = self._c_data.match(line)
        if match is None:
            match = self._c_data2.match(line)
            if match is None:
                return None
        msg = match["msg"]
        assert msg in ["q", "r", "t", "u", "c", "c2", "b", "b2"]
        if msg == "q":
            node = match["node"]
            id_ = int(match["id"])
            res = {
                "transport": self.transport,
                "id": id_,
                "node": node,
                "query_time": float(match["time"]),
            }
            self._last_query[node] = id_
        elif msg == "r":
            id_ = int(match["id"])
            node = match["node"]
            if (id_, node) not in self._times:
                line = line.strip()
                logging.warning("%s: %s has no out from %s", self, line, node)
            res = {
                "transport": self.transport,
                "id": id_,
                "node": node,
                "response_time": float(match["time"]),
            }
        else:
            return self._update_from_times2_line(line, match)
        if (id_, node) in self._times:
            self._times[id_, node].update(res)
        else:
            self._times[id_, node] = res
        return res

    def _parse_stats_line(self, line):
        """
        >>> parser = LogParser('test.log', transport='udp')
        >>> parser._parse_stats_line(
        ...     '1637840810.202737;m3-281;  RX packets 266  bytes 22585',
        ... )
        {'node': 'm3-281', 'l2_received': 266}
        >>> parser._parse_stats_line(
        ...     '1637840810.204249;m3-281;  TX packets 318 (Multicast: 4)  bytes 24446',
        ... )
        {'node': 'm3-281', 'l2_sent': 318, 'l2_multicast': 4}
        >>> parser._parse_stats_line(
        ...     '1637840810.205524;m3-281;  TX succeeded 288 errors 30',
        ... )
        {'node': 'm3-281', 'l2_success': 288, 'l2_error': 30}
        >>> parser = LogParser('test.log', transport='udp', border_router='.border-router')
        >>> parser._parse_stats_line(
        ...     '            RX packets 121  bytes 12841',
        ... )
        {'node': 'br', 'l2_received': 121}
        >>> parser._parse_stats_line(
        ...     '            TX packets 265 (Multicast: 36)  bytes 20517',
        ... )
        {'node': 'br', 'l2_sent': 265, 'l2_multicast': 36}
        >>> parser._parse_stats_line(
        ...     '            TX succeeded 255 errors 10',
        ... )
        {'node': 'br', 'l2_success': 255, 'l2_error': 10}
        """  # noqa: E501
        for c in [self._c_l2_rx, self._c_l2_tx, self._c_l2_success]:
            match = c.match(line)
            if match:
                break
        if not match:
            return None
        res = match.groupdict()
        for group in [
            "l2_received",
            "l2_sent",
            "l2_multicast",
            "l2_success",
            "l2_error",
        ]:
            if group in res:
                res[group] = int(res[group])
        if self.border_router:
            assert res["node"] is None, "Line contains node on BR"
            node = "br"
            res["node"] = "br"
        else:
            assert (
                res["node"] is not None
            ), f"Line in {self._logname} does not contain node"
            node = res["node"]
        if node in self._stats:
            self._stats[node].update(res)
        else:
            self._stats[node] = res
        return res

    def log_to_csvs(self):
        logging.info("Converting %s to CSVs", self._logname)

        try:
            parsing_functions = [f for f in dir(self) if f.startswith("_parse")]
            with open(self.logname, "rb") as logfile:
                for line in logfile:
                    line = line.decode(errors="ignore")
                    if not self._experiment_started:
                        self._check_experiment_started(line)
                        continue
                    for function in parsing_functions:
                        if getattr(self, function)(line):
                            break
                assert (
                    self._experiment_started
                ), f"Experiment {self.logname} was never started"
            self._write_csvs()
        except (AssertionError, KeyboardInterrupt, LogError) as exc:
            if os.path.exists(self.times_csv):
                os.remove(self.times_csv)
            if os.path.exists(self.stats_csv):
                os.remove(self.stats_csv)
            raise exc


class ThreadableParser(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exc = None

    @staticmethod
    def the_target(logname, data_path=pc.DATA_PATH):
        parser = LogParser.match(logname, data_path=data_path)
        if parser:
            parser.log_to_csvs()

    def run(self):
        try:
            super().run()
        except BaseException as exc:  # pylint: disable=broad-except
            self.exc = exc

    def join(self, *args, **kwargs):  # pylint: disable=signature-differs
        super().join(*args, **kwargs)
        if self.exc:
            raise self.exc


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
