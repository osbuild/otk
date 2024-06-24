import pytest

from otk.document import Omnifest
from otk.error import ParseVersionError


def test_omnifest_ensure():
    Omnifest.ensure({"otk.version": 1})


def test_omnifest_ensure_no_keys():
    with pytest.raises(ParseVersionError):
        assert Omnifest.ensure({})
