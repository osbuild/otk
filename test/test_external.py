import json
import os
import textwrap

import pytest

import otk.external
from otk.external import exe_from_directive


@pytest.mark.parametrize(
    "text,exe",
    [
        ("otk.external.osbuild", "otk_external_osbuild"),
        ("otk.external.osbuild_foo-bar", "otk_external_osbuild_foo-bar"),
        ("otk.external.foo", "otk_external_foo"),
    ],
)
def test_exe_from_directive(text, exe):
    assert exe_from_directive(text) == exe


def test_external_not_found():
    fake_directive = "otk.external.not_available"
    fake_tree = {}
    with pytest.raises(RuntimeError) as exc:
        otk.external.call(fake_directive, fake_tree)
    assert "could not find 'otk_external_not_available' in any search path" in str(exc.value)


def test_integration_happy(tmp_path):
    os.environ["OTK_EXTERNAL_PATH"] = os.fspath(tmp_path)
    fake_external_path = tmp_path / "otk_external_test"
    fake_external_path.write_text(
        textwrap.dedent("""\
    #!/bin/sh
    cat - > "$0".stdin
    echo '{"tree": {"some": "result"}}'
    """)
    )
    os.chmod(fake_external_path, 0o755)

    fake_directive = "otk.external.test"
    fake_tree = {
        "foo": "bar",
        "sub": {
            "baz": "foobar",
        },
    }

    res = otk.external.call(fake_directive, fake_tree)
    assert res == {"some": "result"}

    inp = fake_external_path.with_suffix(".stdin").read_text()
    assert json.loads(inp) == {"tree": {fake_directive: fake_tree}}
