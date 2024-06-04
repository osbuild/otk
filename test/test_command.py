import pytest

from otk.command import parser_create


def test_parse_no_command(capsys):
    p = parser_create()
    with pytest.raises(SystemExit) as sys_exit:
        p.parse_args([])
    assert sys_exit.type == SystemExit
    assert sys_exit.value.code == 2

    captured_stderr = capsys.readouterr().err
    assert "the following arguments are required: command" in captured_stderr


@pytest.mark.parametrize(
    "command,results",
    [
        (["compile"], {"command": "compile", "output": None, "input": None}),
        (["compile", "foo"], {"command": "compile", "output": None, "input": "foo"}),
        (
            ["compile", "-o", "output_manifest.yaml"],
            {"command": "compile", "output": "output_manifest.yaml", "input": None},
        ),
        (
            ["compile", "-o", "output_manifest.yaml", "input_omifest.yaml"],
            {
                "command": "compile",
                "output": "output_manifest.yaml",
                "input": "input_omifest.yaml",
            },
        ),
        (["validate", "foo.yaml"], {"command": "validate", "input": "foo.yaml"}),
    ],
)
def test_parse_commands_success(capsys, command, results):
    p = parser_create()
    r = p.parse_args(command)
    for k in results.keys():
        assert getattr(r, k) == results[k]


@pytest.mark.parametrize(
    "command,sys_exit_code,sys_exit_message",
    [
        (
            ["compile", "--no_such_option"],
            2,
            "unrecognized arguments: --no_such_option",
        ),
        (
            ["validate", "-o", "output_manifest.yaml", "input_omifest.yaml"],
            2,
            # deliberately we expect '-o input_omifest.yaml' as argparse acts like this if -o is not defined
            "error: unrecognized arguments: -o input_omifest.yaml",
        ),
    ],
)
def test_parse_commands_failure(capsys, command, sys_exit_code, sys_exit_message):
    p = parser_create()
    with pytest.raises(SystemExit) as sys_exit:
        p.parse_args(command)
    assert sys_exit.type == SystemExit
    assert sys_exit.value.code == sys_exit_code

    captured_stderr = capsys.readouterr().err
    assert sys_exit_message in captured_stderr
