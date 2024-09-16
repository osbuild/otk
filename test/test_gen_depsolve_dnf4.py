import json
from io import StringIO

from otk_external_osbuild.command.gen_depsolve_dnf4 import root


def test_otk_under_test_mock_data(monkeypatch, capsys):
    monkeypatch.setenv("OTK_UNDER_TEST", "1")
    fake_input = StringIO(json.dumps({
        "tree": {
            "packages": {
                "include": ["pkg1"],
            }
        },
    }))
    root(fake_input)
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
                            "version": "4",
                            "release": "r8",
                            "arch": "noarch",
                        },
                    ],
                },
            },
        },
    }


def test_otk_under_test_mock_data_kernel(monkeypatch, capsys):
    monkeypatch.setenv("OTK_UNDER_TEST", "1")
    fake_input = StringIO(json.dumps({
        "tree": {
            "kernel_pkgname": "my-kernel",
            "packages": {
                "include": ["my-kernel", "pkg1"],
            }
        },
    }))
    root(fake_input)
    output = json.loads(capsys.readouterr().out)
    assert output == {
        "tree": {
            "const": {
                "kernel": {
                    "name": "my-kernel",
                    "version": "1",
                    "release": "r4",
                    "arch": "noarch",
                },
                "internal": {
                    "packages": [
                        {
                            "checksum": "sha256:c892f5086e0951a7b31364bfd1373c375b10567a26e6e37ff96de2993428bc12",
                            "name": "my-kernel",
                            "remote_location": "https://example.com/repo/packages/my-kernel",
                            "version": "1",
                            "release": "r4",
                            "arch": "noarch",
                        },
                        {
                            "checksum": "sha256:3d7b91c2dd3273400f26d21a492fcdfdc3dde228cd5627247dfef745ce717755",
                            "name": "pkg1",
                            "remote_location": "https://example.com/repo/packages/pkg1",
                            "version": "4",
                            "release": "r8",
                            "arch": "noarch",
                        },
                    ],
                },
            },
        },
    }
