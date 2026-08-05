import datetime

import pytest

from utilities.http import add_qs_params_to_url, parse_last_modified_header


@pytest.mark.parametrize(
    "input,expected",
    [
        ("Fri, 06 Sep 2024 13:08:28 GMT", datetime.datetime(2024, 9, 6, 13, 8, 28, 0, datetime.timezone.utc)),
        ("Wed, 21 Oct 2015 07:28:00 GMT", datetime.datetime(2015, 10, 21, 7, 28, 0, 0, datetime.timezone.utc)),
        ("Wed, 21 Oct 2015 07:28:00", None),
        ("Wed, 21 October 2015 07:28:00 +00:00", None),
    ],
)
def test_parse_http_last_modified_header(input, expected):
    assert parse_last_modified_header(input) == expected


@pytest.mark.parametrize(
    "input,params,expected",
    [
        ("http://www.a.com", {}, "http://www.a.com"),
        ("http://www.a.com", {"one": 1}, "http://www.a.com?one=1"),
        ("http://www.a.com", {"one": 1, "two": 2}, "http://www.a.com?one=1&two=2"),
        ("http://www.a.com?one=1", {"one": "updated"}, "http://www.a.com?one=updated"),
    ],
)
def test_add_qs_params_to_url(input, params, expected):
    assert add_qs_params_to_url(input, params) == expected
