# Copyright (C) 2021-22 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import pytest

from .. import parse_load_results
from .. import parse_max_age_results

__author__ = "Martine S. Lenders"
__copyright__ = "Copyright 2021-22 Freie Universität Berlin"
__license__ = "LGPL v2.1"
__email__ = "m.lenders@fu-berlin.de"


@pytest.mark.parametrize(
    "kwargs",
    [
        pytest.param(
            {
                "logname": "The_log",
            },
            id="base",
        ),
    ],
)
def test_logparser_init(kwargs):
    parse_max_age_results.LogParser(**kwargs)


@pytest.mark.flaky(reruns=3)
@pytest.mark.parametrize(
    "read_data, exp_assert_fail",
    [
        pytest.param(
            """
Starting run doc-eval-proxy-ieee802154-coap-get-proxied0-None-None-50x5.0-AAAA-297517-1645849322
1668718705.272968;m3-202;query_bulk exec id.exp.example.org inet6 fetch
1668718705.275594;m3-205;query_bulk exec id.exp.example.org inet6 fetch
1668718705.275854;m3-205;shell: command not found: query_bulk
1668718705.464000;m3-202;q;00001
1668718705.464338;m3-202;D;00001
1668718705.464342;m3-202;R;37433
1668718705.464343;m3-202;r;00001
1668718705.465000;m3-202;q;00002
1668718705.464343;m3-202;D;00003
1668718705.465338;m3-202;t;37444
1668718705.465342;m3-202;C;37443
1668718705.483586;m3-205;> t;37444
1668718705.483592;m3-205;t;37444
1668718705.515548;m3-205;t;48537
1668718705.576846;m3-202;R;37444
1668718705.577144;m3-202;r;00002
1668718705.656947;m3-202;q;00003
1668718705.657285;m3-202;t;37700
1668718705.659536;m3-205;t;37700
1668718705.691549;m3-205;t;48793
1668718705.736776;m3-202;R;37700
1668718705.737085;m3-202;r;00003
1668718705.848991;m3-202;q;00004
1668718705.849333;m3-202;t;37956
1668718705.851434;m3-205;t;37956
1668718705.883414;m3-205;t;49049
1668718705.928741;m3-202;R;37956
1668718705.929044;m3-202;r;00004
1668718706.248858;m3-202;q;00006
1668718706.251500;m3-205;t;38468
1668718706.251740;m3-205;C;38468
1668718706.249194;m3-202;t;38468
1668718706.249195;m3-202;t;38468
1668718706.280917;m3-202;R;38468
1668718706.281224;m3-202;r;00006
1668718706.283388;m3-205;t;49561
1668718706.475533;m3-205;u;49817
1668718706.475536;m3-205;t;49817
1668718706.475767;m3-205;C;49817
1668718706.475771;m3-205;C;49817
1668718706.649019;m3-202;q;00000
1668718706.649352;m3-202;t;38980
1668718706.667516;m3-205;t;38980
1668718706.683781;m3-205;V;38980
1668718706.683784;m3-205;C;38980
1668718706.683787;m3-205;P;38980
1668718706.683788;m3-205;A;38980
1668718706.728858;m3-202;R;38980
1668718706.729152;m3-202;r;00000
1668718706.840871;m3-202;q;00001
1668718706.841205;m3-202;t;39236
1668718706.843457;m3-205;t;39236
1668718706.843690;m3-205;C;39236
1668718706.843690;m3-205;C;39236
1668718706.872740;m3-202;R;39236
1668718706.873038;m3-202;r;00001
1668718707.016771;m3-202;q;00002
1668718707.032651;m3-202;t;39492
1668718707.032952;m3-202;C;39492
1668718707.032654;m3-205;P;39493
1668718707.032656;m3-205;A;39493
1668718707.033082;m3-202;R;39492
1668718707.033196;m3-202;r;00002
1668718707.624821;m3-202;q;00005
1668718707.625165;m3-202;t;40260
1668718707.625310;m3-202;C;40260
1668718707.625312;m3-202;C;40260
1668718707.625412;m3-202;R;40260
1668718707.625503;m3-202;> r;00005
1668718822.726058;m3-202;packet buffer: first byte: 0x2000d4e4, last byte: 0x2000dce4 (size: 2048)
1668718822.726130;m3-202;  position of last byte used: 904
1668718822.726182;m3-202;~ unused: 0x2000d4e4 (next: (nil), size: 2048) ~
""",  # noqa: E501
            False,
            id="success",
        ),
        pytest.param(
            """
1668692935.851016;m3-202;query_bulk exec id.exp.example.org inet6 get 8
1668692936.026222;m3-202;q;00006
1668692936.026222;m3-202;t;13632
1668692936.026225;m3-202;R;13632
1668692936.026225;m3-202;r;00007
""",
            False,
            id="no query for reception",
        ),
        pytest.param(
            """
1668692935.851016;m3-202;query_bulk exec id.exp.example.org inet6 get 8
1668692936.026222;m3-202;q;00002
1668692936.109818;m3-202;r;00002
""",
            True,
            id="no lower-level response for reception",
        ),
        pytest.param(
            """
1668692935.851016;m3-202;query_bulk exec id.exp.example.org inet6 get 8
1668692936.026222;m3-202;q;00002
1668692936.026222;m3-202;R;1245
1668692936.109818;m3-202;r;00002
""",
            True,
            id="no transmission for reception",
        ),
        pytest.param(
            """
1668692935.851016;m3-202;query_bulk exec id.exp.example.org inet6 get 8
1668692936.026222;m3-202;t;1245
1668692936.026222;m3-202;t;1245
1668692936.026222;m3-202;R;1245
1668692936.109818;m3-202;r;00002
""",
            True,
            id="no query for reception",
        ),
    ],
)
def test_parse_max_age_results(mocker, read_data, exp_assert_fail):
    mocker.patch.object(
        parse_load_results,
        "open",
        mocker.mock_open(read_data=read_data.encode()),
    )
    mocker.patch(
        "os.listdir",
        return_value=[
            "foobar.log",
            "doc-eval-max_age-ieee802154-min-coap-fetch-dc0-ccc1-proxied0-None-None-"
            "50x5.0-AAAA-345279-1668572887.log",
            "doc-eval-max_age-ieee802154-subtract-coap-get-dc1-ccc0-proxied0-None-None-"
            "50x5.0-AAAA-345589-1668692881.log",
            "doc-eval-max_age-ieee802154-min-coap-post-proxied1-None-None-"
            "50x5.0-AAAA-345589-1668691383.log",
        ],
    )
    mocker.patch("multiprocessing.cpu_count", return_value=1)
    mocker.patch("sys.argv", ["cmd"])
    mocker.patch("os.path.exists", return_value=False)
    if exp_assert_fail:
        with pytest.raises(AssertionError):
            parse_max_age_results.main()
    else:
        parse_max_age_results.main()
