import json
import os
import textwrap

import pytest

import otk.external
from otk.context import CommonContext
from otk.external import exe_from_directive


@pytest.mark.parametrize(
    "text,exe",
    [
        ("otk.external.osbuild", "osbuild"),
        ("otk.external.osbuild_foo-bar", "osbuild_foo-bar"),
        ("otk.external.foo", "foo"),
    ],
)
def test_exe_from_directive(text, exe):
    assert exe_from_directive(text) == exe


def test_external_not_found():
    ctx = CommonContext()
    fake_directive = "otk.external.not_available"
    fake_tree = {}
    with pytest.raises(RuntimeError) as exc:
        otk.external.call(ctx, fake_directive, fake_tree)
    assert "could not find 'not_available' in any search path" in str(exc.value)


@pytest.fixture(name="test_external")
def test_external_fixture(tmp_path):
    """Create a test external with the name "test" that just prints a result"""
    fake_external_path = tmp_path / "external" / "test"
    fake_external_path.parent.mkdir(parents=True, exist_ok=True)
    fake_external_path.write_text(
        textwrap.dedent("""\
    #!/bin/sh
    cat - > "$0".stdin
    echo '{"tree": {"some": "result"}}'
    """)
    )
    os.chmod(fake_external_path, 0o755)
    return fake_external_path


def test_integration_happy_libdir(test_external):
    ctx = CommonContext(libdir=test_external.parent.parent)
    fake_directive = "otk.external.test"
    fake_tree = {"foo": "bar"}

    res = otk.external.call(ctx, fake_directive, fake_tree)
    assert res == {"some": "result"}
    inp = test_external.with_suffix(".stdin").read_text()
    assert json.loads(inp) == {"tree": fake_tree}


def test_integration_happy_env(monkeypatch, test_external):
    ctx = CommonContext()
    fake_directive = "otk.external.test"
    fake_tree = {"foo": "bar"}
    monkeypatch.setenv("OTK_EXTERNAL_PATH", os.fspath(test_external.parent))

    res = otk.external.call(ctx, fake_directive, fake_tree)
    assert res == {"some": "result"}
    inp = test_external.with_suffix(".stdin").read_text()
    assert json.loads(inp) == {"tree": fake_tree}
