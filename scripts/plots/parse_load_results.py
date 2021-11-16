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
        transport=r"(?P<transport>coaps?|dtls|udp|oscore)",
        method=r"(?P<method>fetch|get|post)",
        delay_time=r"(?P<delay_time>(\d+\.\d+|None))",
        delay_queries=r"(?P<delay_queries>(\d+|None))",
        queries=r"(?P<queries>\d+)",
        record=r"(?P<record>A{1,4})",
        avg_queries_per_sec=r"(?P<avg_queries_per_sec>\d+.\d+)",
    )

    LOG_EXP_STARTED_PATTERN = r"((Starting run doc-eval-load)|(query_bulk exec h\.de))"
    LOG_DATA_PATTERN = (
        r"(?P<time>\d+.\d+);(?P<node>m3-\d+);"
        r"(> ?)?(?P<msg>(q|r));(?P<name>(?P<id>\d+)\.[0-9a-zA-Z.]+)"
    )
    _LOG_NAME_C = re.compile(f"{LOGNAME_PATTERN}.log")

    def __init__(
        self,
        logname,
        transport=None,
        method=None,
        delay_time=None,
        delay_queries=None,
        queries=None,
        avg_queries_per_sec=None,
        record=None,
        exp_id=None,
        timestamp=None,
        data_path=pc.DATA_PATH,
    ):
        # pylint: disable=too-many-arguments,unused-argument
        self.data_path = data_path
        self._logname = logname
        self.transport = transport
        if record is None:
            self.record = "AAAA"
        else:
            self.record = "A"
        self.exp_id = int(exp_id) if exp_id is not None else exp_id
        if timestamp:
            self.timestamp = datetime.datetime.fromtimestamp(int(timestamp))
        else:
            self.timestamp = None
        self._experiment_started = False
        self._times = {}
        self._c_started = re.compile(self.LOG_EXP_STARTED_PATTERN)
        self._c_data = re.compile(self.LOG_DATA_PATTERN)

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
        """
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

    @staticmethod
    def _get_csv_writer(times_csvfile):
        times_fieldnames = [
            "transport",
            "id",
            "query_time",
            "response_time",
        ]
        times_csv = csv.DictWriter(
            times_csvfile, fieldnames=times_fieldnames, delimiter=";"
        )
        times_csv.writeheader()
        return times_csv

    def _write_csvs(self):
        with open(self.times_csv, "w", encoding="utf-8") as times_csvfile:
            times_csv = self._get_csv_writer(
                times_csvfile,
            )
            for row in self._times.values():
                times_csv.writerow(row)

    def _check_experiment_started(self, line):
        match = self._c_started.search(line)
        if match:
            self._experiment_started = True
            return match.groupdict()
        return None

    def _parse_times_line(self, line):
        """
        >>> parser = LogParser('test.log', transport='udp')
        >>> parser._parse_times_line(
        ...     '1633695050.906918;m3-281;q;3911.h.fr',
        ... )
        {'transport': 'udp', 'id': 3911, 'query_time': 1633695050.906918}
        >>> parser._parse_times_line(
        ...     '1633695050.981532;m3-281;> r;3911.h.fr',
        ... )
        {'transport': 'udp', 'id': 3911, 'response_time': 1633695050.981532}
        >>> parser._parse_times_line(
        ...     '1633695064.180100;m3-281;r;3973.h.fr'
        ... )
        {'transport': 'udp', 'id': 3973, 'response_time': 1633695064.1801}
        """
        match = self._c_data.match(line)
        if match is None:
            return None
        direction = match["msg"]
        assert direction in ["q", "r"]
        if direction == "q":
            node = match["node"]
            id_ = int(match["id"])
            res = {
                "transport": self.transport,
                "id": id_,
                "query_time": float(match["time"]),
            }
        else:
            id_ = int(match["id"])
            node = match["node"]
            if id_ not in self._times:
                line = line.strip()
                logging.warning("%s: %s has no out from %s", self, line, node)
            res = {
                "transport": self.transport,
                "id": id_,
                "response_time": float(match["time"]),
            }
        if id_ in self._times:
            self._times[id_].update(res)
        else:
            self._times[id_] = res
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
