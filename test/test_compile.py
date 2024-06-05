import argparse
import os


from otk.command import compile


fake_otk_yaml = """
otk.version: 1
otk.target.osbuild.qcow2:
 test: 1
"""

expected_otk_tree = """\
{
  "test": 1,
  "version": "2",
  "sources": {}
}"""


def test_compile_integration_file(tmp_path):
    input_path = tmp_path / "input.txt"
    input_path.write_text(fake_otk_yaml)
    output_path = tmp_path / "output.txt"

    arguments = argparse.Namespace(input=input_path, output=output_path, target="osbuild")
    ret = compile(arguments)
    assert ret == 0

    assert output_path.exists()
    assert output_path.read_text() == expected_otk_tree


def test_compile_integration_stdin(capsys, monkeypatch):
    mocked_stdin = os.memfd_create("<fake-stdin>")
    os.write(mocked_stdin, fake_otk_yaml.encode("utf8"))
    os.lseek(mocked_stdin, 0, 0)
    monkeypatch.setattr("sys.stdin", os.fdopen(mocked_stdin))

    arguments = argparse.Namespace(input=None, output=None, target="osbuild")
    ret = compile(arguments)
    assert ret == 0

    assert capsys.readouterr().out == expected_otk_tree
