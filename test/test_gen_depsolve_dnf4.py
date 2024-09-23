import json
import subprocess
from io import StringIO
from unittest.mock import call, Mock, patch

from otk_external_osbuild.command.gen_depsolve_dnf4 import root


fake_input = {
    "tree": {
        "architecture": "x86_64",
        "module_platform_id": "f40",
        "releasever": "40",
        "repositories": [
            {
                "id": "BaseOS",
                "baseurl": "https://rpmrepo.osbuild.org/v2/mirror/public/el9/cs9-x86_64-baseos-20240901",
            }
        ],
        "packages": {
            "include": ["pkg1"],
            "exclude": ["not-pkg2"],
        }
    }
}


def test_gen_depsolve_dnf4_under_test_mock_data(monkeypatch, capsys):
    monkeypatch.setenv("OTK_UNDER_TEST", "1")
    root(StringIO(json.dumps(fake_input)))
    output = json.loads(capsys.readouterr().out)
    assert output == {
        "tree": {
            "const": {
                "internal": {
                    "packages": [
                        {
                            "checksum": "sha256:3d7b91c2dd3273400f26d21a492fcdfdc3dde228cd5627247dfef745ce717755",
                            "name": "pkg1",
                            "remote_location": "https://example.com/repo/packages/pkg1",
                            "version": "0",
                            "release": "0",
                            "arch": "noarch",
                            "epoch": "",
                        },
                    ],
                },
                "versions": {
                    "pkg1": {
                        "arch": "noarch",
                        "checksum": "sha256:3d7b91c2dd3273400f26d21a492fcdfdc3dde228cd5627247dfef745ce717755",
                        "epoch": "",
                        "name": "pkg1",
                        "release": "0",
                        "remote_location": "https://example.com/repo/packages/pkg1",
                        "version": "0",
                    },
                },
            },
        },
    }


def make_dnfjson_mock_run_result():
    mock_output = json.dumps({
        "packages": [
            {
                "name": "pkg1",
                "checksum": "sha256:3d7b91c2dd3273400f26d21a492fcdfdc3dde228cd5627247dfef745ce717755",
                "remote_location": "https://example.com/repo/packages/pkg1",
                "version": "0",
                "epoch": "",
                "release": "0",
                "arch": "noarch"
            },
            {
                "name": "pkg1-dep",
                "checksum": "sha256:3d7b91c2dd3273400f26d21a492fcdfdc3dde228cd5627247dfef745ce717755",
                "remote_location": "https://example.com/repo/packages/pkg1-dep",
                "version": "0",
                "epoch": "",
                "release": "0",
                "arch": "noarch"
            },
        ],
    })
    run_result = Mock()
    run_result.stdout = mock_output
    run_result.returncode = 0
    return run_result


@patch("subprocess.run")
def test_gen_depsolve_dnf4_call_out(mocked_run):
    mocked_run.return_value = make_dnfjson_mock_run_result()

    expected_dnfjson_input = json.dumps({
        "command": "depsolve",
        "arch": "x86_64",
        "module_platform_id": "platform:f40",
        "releasever": "40",
        "cachedir": "/tmp",
        "arguments": {
            "root_dir": "/tmp",
            "repos": fake_input["tree"]["repositories"],
            "transactions": [
                {
                    "package-specs": ["pkg1"],
                    "exclude-specs": ["not-pkg2"],
                },
            ],
        },
    })
    root(StringIO(json.dumps(fake_input)))
    assert len(mocked_run.call_args_list) == 1
    assert mocked_run.call_args_list[0] == call(
        ["/usr/libexec/osbuild-depsolve-dnf"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        input=expected_dnfjson_input,
        encoding="utf8",
        check=False,
    )
