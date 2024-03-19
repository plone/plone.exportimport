from datetime import datetime
from DateTime import DateTime
from plone.exportimport.utils import dates
from typing import Tuple

import pytest


@pytest.mark.parametrize(
    "value",
    [
        "2024-02-13T18:16:32+00:00",
        "2024-02-29T22:16:32+00:00",
        "2024-01-31T22:16:32+00:00",
    ],
)
def test_parse_datetime_success(value: str):
    func = dates.parse_datetime
    result = func(value)
    assert isinstance(result, datetime)


@pytest.mark.parametrize(
    "value",
    ["", "not-a-date"],
)
def test_parse_datetime_failure(value: str):
    func = dates.parse_datetime
    result = func(value)
    assert result is None


@pytest.mark.parametrize(
    "value,parts",
    [
        ["2024-02-13T18:16:32+00:00", (2024, 2, 13, 18, 16, 32, "GMT+0")],
        ["2024-02-29T22:16:32+00:00", (2024, 2, 29, 22, 16, 32, "GMT+0")],
        ["2024-01-31T22:16:32+00:00", (2024, 1, 31, 22, 16, 32, "GMT+0")],
    ],
)
def test_parse_date_success(value: str, parts: Tuple):
    func = dates.parse_date
    result = func(value)
    assert isinstance(result, DateTime)
    assert result.parts() == parts


@pytest.mark.parametrize(
    "value",
    ["", "not-a-date"],
)
def test_parse_date_failure(value: str):
    func = dates.parse_date
    result = func(value)
    assert result is None
