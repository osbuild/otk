import json
import os
import re
import textwrap

import pytest

import otk.external
from otk.annotation import AnnotatedDict
from otk.error import ExternalFailedError
from otk.external import exe_from_directive
from otk.traversal import State


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


def make_fake_external(tmp_path, name, script):
    fake_external_path = tmp_path / name
    fake_external_path.write_text(script)
    os.chmod(fake_external_path, 0o755)
    return fake_external_path


def run_fake_external_ok(external_path, name):
    os.makedirs(external_path, exist_ok=True)
    fake_external_path = make_fake_external(external_path, name, textwrap.dedent("""\
    #!/bin/sh
    cat - > "$0".stdin
    echo '{"tree": {"some": "result"}}'
    """))

    fake_directive = f"otk.external.{name}"
    fake_tree = {
        "name": name,
        "foo": "bar",
        "sub": {
            "baz": "foobar",
        },
    }

    res = otk.external.call(State(""), fake_directive, AnnotatedDict(fake_tree))
    assert res == {"some": "result"}

    inp = fake_external_path.with_suffix(".stdin").read_text()
    assert json.loads(inp) == {"tree": fake_tree}


def test_external_not_found():
    fake_directive = "otk.external.not_available"
    fake_tree = {}
    with pytest.raises(RuntimeError) as exc:
        otk.external.call(State(""), fake_directive, fake_tree)
    assert "could not find 'not_available' in any search path" in str(exc.value)


def test_integration_happy(tmp_path):
    os.environ["OTK_EXTERNAL_PATH"] = os.fspath(tmp_path)
    run_fake_external_ok(tmp_path, "test")


def test_external_multipath(tmp_path):
    os.environ["OTK_EXTERNAL_PATH"] = f"{tmp_path}/dir1:{tmp_path}/dir2"
    run_fake_external_ok(tmp_path / "dir1", "test-1")
    run_fake_external_ok(tmp_path / "dir2", "test-2")


def test_integration_error(tmp_path):
    os.environ["OTK_EXTERNAL_PATH"] = os.fspath(tmp_path)
    make_fake_external(tmp_path, "test", textwrap.dedent("""\
    #!/bin/sh
    cat - > "$0".stdin
    echo "some output"
    >&2 echo "stderr output"
    exit 1
    """))

    fake_directive = "otk.external.test"
    fake_tree = {
        "foo": "bar",
        "sub": {
            "baz": "foobar",
        },
    }

    with pytest.raises(ExternalFailedError) as exc:
        otk.external.call(State("foo.yaml"), fake_directive, fake_tree)
    assert re.match(
        r"foo.yaml: call /.*/test 'otk.external.test' failed: "
        r"stdout='some output\\n', stderr='stderr output\\n'", str(exc.value))
