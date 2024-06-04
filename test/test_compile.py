import argparse
import os.path
import pytest

from otk.command import compile


@pytest.mark.parametrize(
    "arguments, input_data, output_data, sys_exit_code, log_message",
    [
        # "GENERATE" is a placeholder to append "tmp_path" from pytest
        (
            argparse.Namespace(input="GENERATE", output="GENERATE", target=None),
            """otk.version: 1
otk.target.osbuild.qcow2: { test: 1 }
""",
            """{
  "test": 1,
  "version": "2",
  "sources": {}
}""",
            0,
            None,
        ),
    ],
)
def test_compile(
    tmp_path,
    caplog,
    capsys,
    monkeypatch,
    arguments,
    input_data,
    output_data,
    sys_exit_code,
    log_message,
):
    if arguments.input == "GENERATE":
        input_filename = "input.yaml"
        arguments.input = os.path.join(tmp_path, input_filename)
        with open(arguments.input, "w") as f:
            f.write(input_data)

    if arguments.output == "GENERATE":
        # fix path so we only write to tmp_path
        arguments.output = os.path.join(tmp_path, "output.yaml")

    ret = compile(arguments)
    assert ret == sys_exit_code

    if log_message:
        assert log_message in caplog.text

    assert os.path.exists(arguments.output)
    with open(arguments.output) as f:
        assert f.readlines() == output_data.splitlines(True)
