import logging
import os
import textwrap

import pytest

from otk.command import run


@pytest.mark.parametrize("cmd,warn_arg,expect_warning", [
    ("compile", "", False),
    ("compile", "duplicate-definition", True),
    ("compile", "all", True),
    ("validate", "", False),
    ("validate", "duplicate-definition", True),
    ("validate", "all", True),
])
def test_warn(tmp_path, caplog, cmd, warn_arg, expect_warning):
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

    if warn_arg:
        prefix = ["-w", warn_arg]
    else:
        prefix = []
    run(prefix + [cmd, os.fspath(test_otk)])
    if expect_warning:
        expected_msg = "redefinition of 'a', previous value was 1 and new value is 2"
        assert [expected_msg] == [rec.message for rec in caplog.records]
    else:
        assert [] == [rec.message for rec in caplog.records]
