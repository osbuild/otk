import argparse
import os
import pathlib

from otk.command import compile  # pylint: disable=W0622


FAKE_OTK_YAML = """
otk.version: 1
otk.target.osbuild.qcow2:
 test: 1
"""

EXPECTED_OTK_TREE = """\
{
  "test": 1,
  "version": "2",
  "sources": {}
}"""

FAKE_OTK_INCLUDE_YAML_FILENAME = "the_include.yml"

FAKE_OTK_INCLUDE_YAML = f"""
otk.version: 1
otk.target.osbuild.qcow2:
  otk.include: {FAKE_OTK_INCLUDE_YAML_FILENAME}
"""

FAKE_OTK_INCLUDE_CHILD_YAML = """\
"test": 1
"""


def test_compile_integration_file(tmp_path):
    input_path = tmp_path / "input.txt"
    input_path.write_text(FAKE_OTK_YAML)
    output_path = tmp_path / "output.txt"

    arguments = argparse.Namespace(input=input_path, output=output_path, target="osbuild.qcow2")
    ret = compile(arguments)
    assert ret == 0

    assert output_path.exists()
    assert output_path.read_text() == EXPECTED_OTK_TREE


def test_compile_integration_stdin(capsys, monkeypatch):
    mocked_stdin = os.memfd_create("<fake-stdin>")
    os.write(mocked_stdin, FAKE_OTK_YAML.encode("utf8"))
    os.lseek(mocked_stdin, 0, 0)
    monkeypatch.setattr("sys.stdin", os.fdopen(mocked_stdin))

    arguments = argparse.Namespace(input=None, output=None, target="osbuild.qcow2")
    ret = compile(arguments)
    assert ret == 0

    assert capsys.readouterr().out == EXPECTED_OTK_TREE


def test_compile_integration_stdin_with_include(capsys, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    included_file = pathlib.Path(tmp_path / FAKE_OTK_INCLUDE_YAML_FILENAME)
    included_file.write_text(FAKE_OTK_INCLUDE_CHILD_YAML, encoding="utf-8")

    mocked_stdin = os.memfd_create("<fake-stdin>")
    os.write(mocked_stdin, FAKE_OTK_INCLUDE_YAML.encode("utf8"))
    os.lseek(mocked_stdin, 0, 0)
    monkeypatch.setattr("sys.stdin", os.fdopen(mocked_stdin))

    arguments = argparse.Namespace(input=None, output=None, target="osbuild.qcow2")
    ret = compile(arguments)
    assert ret == 0

    assert capsys.readouterr().out == EXPECTED_OTK_TREE
