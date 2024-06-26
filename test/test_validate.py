import argparse
import os.path
import pytest

from otk.command import validate


@pytest.mark.parametrize(
    "arguments, input_data, sys_exit_code, log_message",
    [
        # "GENERATE" is a placeholder to append "tmp_path" from pytest
        (
            argparse.Namespace(input="GENERATE", output="GENERATE", target=None),
            """otk.version: 1
otk.target.osbuild.qcow2: { test: 1 }
""",
            0,
            None,
        ),
        (
            argparse.Namespace(input="GENERATE", output=None, target=None),
            """otk.version: 1
otk.target.osbuild.qcow2: { test: 1 }
""",
            0,
            None,
        ),
        (
            argparse.Namespace(input="GENERATE", output="GENERATE", target=None),
            """otk.version: 1
otk.target.osbuild.qcow2: { test: 1 }
otk.target.osbuild.ami: { test: 2 }
""",
            1,
            "INPUT contains multiple targets, `-t` is required",
        ),
    ],
)
def test_validate(tmp_path, caplog, arguments, input_data, sys_exit_code, log_message):  # pylint: disable=too-many-arguments
    if arguments.input == "GENERATE":
        input_filename = "input.yaml"
        arguments.input = os.path.join(tmp_path, input_filename)
        with open(arguments.input, "w", encoding="utf8") as f:
            f.write(input_data)

    if arguments.output == "GENERATE":
        # fix path so we only write to tmp_path
        arguments.output = os.path.join(tmp_path, "output.yaml")

    ret = validate(arguments)
    assert ret == sys_exit_code

    if log_message:
        assert log_message in caplog.text

    if arguments.output:
        assert not os.path.exists(arguments.output)
