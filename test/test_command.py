import pytest

from otk.command import parser_create, run


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
def test_parse_commands_success(command, results):
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


TEST_ARGUMENT_T_INPUT = """otk.version: "1"

otk.target.osbuild:
  pipelines:
    - "test"
"""

TEST_ARGUMENT_T_INPUT_TWO_TARGETS = TEST_ARGUMENT_T_INPUT + """
otk.target.osbuild.name1:
  pipelines:
    - "test1"
"""

TEST_ARGUMENT_T_OUTPUT = """{
  "pipelines": [
    "test"
  ],
  "version": "2"
}"""

TEST_ARGUMENT_T_OUTPUT1 = """{
  "pipelines": [
    "test1"
  ],
  "version": "2"
}"""


@pytest.mark.parametrize(
    "data",
    [
        # Select no target - only one available
        {"command": ["compile", "-o", "OUTPUTFILE", "INPUTFILE"],
         "input_data": TEST_ARGUMENT_T_INPUT,
         "output_data": TEST_ARGUMENT_T_OUTPUT,
         "ret_expected": 0,
         "log_expected": ""
         },

        # Select the one available target
        {"command": ["compile", "-t", "osbuild", "-o", "OUTPUTFILE", "INPUTFILE"],
         "input_data": TEST_ARGUMENT_T_INPUT,
         "output_data": TEST_ARGUMENT_T_OUTPUT,
         "ret_expected": 0,
         "log_expected": ""
         },

        # Select the one of multiple targets
        {"command": ["compile", "-t", "osbuild.name1", "-o", "OUTPUTFILE", "INPUTFILE"],
         "input_data": TEST_ARGUMENT_T_INPUT_TWO_TARGETS,
         "output_data": TEST_ARGUMENT_T_OUTPUT1,
         "ret_expected": 0,
         "log_expected": ""
         },

        # Select an invalid target
        {"command": ["compile", "-t", "osbuild.nonexist", "-o", "OUTPUTFILE", "INPUTFILE"],
         "input_data": TEST_ARGUMENT_T_INPUT,
         "output_data": "",
         "ret_expected": 1,
         "log_expected": "requested target 'osbuild.nonexist' does not exist in INPUT"
         },

        # Select no target but multiples available
        {"command": ["compile", "-o", "OUTPUTFILE", "INPUTFILE"],
         "input_data": TEST_ARGUMENT_T_INPUT_TWO_TARGETS,
         "output_data": "",
         "ret_expected": 1,
         "log_expected": "INPUT contains multiple targets"
         },
    ]
)
def test_argument_t(tmp_path, caplog, data):
    output_file = tmp_path / "output.yaml"
    input_file = tmp_path / "input.yaml"
    input_file.write_text(data["input_data"])

    command = [str(output_file) if item == "OUTPUTFILE" else item for item in data["command"]]
    command = [str(input_file) if item == "INPUTFILE" else item for item in command]

    ret = run(command)

    assert output_file.read_text() == data["output_data"]
    assert ret == data["ret_expected"]
    assert data["log_expected"] in caplog.text
