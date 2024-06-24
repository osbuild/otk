import pytest

from otk.document import Omnifest
from otk.error import NoTargetsError, ParseVersionError


def test_omnifest_ensure():
    Omnifest.ensure({"otk.version": 1, "otk.target.osbuild": {}})


def test_omnifest_ensure_no_keys():
    with pytest.raises(ParseVersionError):
        assert Omnifest.ensure({})


def test_omnifest_ensure_no_targets():
    with pytest.raises(NoTargetsError):
        Omnifest.ensure({"otk.version": 1})
