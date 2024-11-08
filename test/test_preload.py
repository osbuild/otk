import os
import textwrap

from otk.command import run


def test_otk_preload_works(tmp_path):
    expected_json = textwrap.dedent("""\
    {
      "lang": "nl_NL.UTF-8",
      "version": "2"
    }""")
    preload_otk = tmp_path / "preload.yaml"
    preload_otk.write_text(textwrap.dedent("""
    otk.define:
      user:
        modifications:
          language: nl_NL.UTF-8
    """))

    test_otk = tmp_path / "foo.yaml"
    test_otk.write_text(textwrap.dedent("""
    otk.version: 1
    otk.define:
      default:
        modifications:
          language: en_US.UTF-8
      modifications:
        otk.op.join:
          values:
            - ${default.modifications}
            - ${user.modifications}
    otk.target.osbuild:
      lang: ${modifications.language}
    """))
    result_otk = tmp_path / "output.yaml"
    run(["compile", "-e", os.fspath(preload_otk), os.fspath(test_otk), "-o", result_otk.as_posix()])
    assert expected_json == result_otk.read_text()
