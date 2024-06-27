import logging
import os
import textwrap

import pytest

from otk.command import run


@pytest.mark.parametrize("cmd,with_dupe_warn", [
    ("compile", False),
    ("compile", True),
    ("validate", False),
    ("validate", True),
])
def test_warn(tmp_path, caplog, cmd, with_dupe_warn):
    caplog.set_level(logging.WARNING)

    test_otk = tmp_path / "foo.yaml"
    test_otk.write_text(textwrap.dedent("""
    otk.version: 1
    otk.target.osbuild.foo:
      x: y

    otk.define.1:
      a: 1
    otk.define.2:
      a: 2
    """))

    if with_dupe_warn:
        prefix = ["-w", "duplicate-definition"]
    else:
        prefix = []
    run(prefix + [cmd, os.fspath(test_otk)])
    if with_dupe_warn:
        expected_msg = "redefinition of 'a', previous value was 1 and new value is 2"
        assert [expected_msg] == [rec.message for rec in caplog.records]
    else:
        assert [] == [rec.message for rec in caplog.records]
