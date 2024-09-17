import json
from io import StringIO

from otk_external_osbuild.command.make_depsolve_dnf4_rpm_stage import root

# Some duplication between the test and the code is expected
# pylint: disable=duplicate-code

fake_input = {
    "tree": {
        "packageset": {
            "const": {
                "internal": {
                    "packages": [
                        {
                            "remote_location": "http://example.com/pkg1",
                            "checksum": "sha256:1234",
                        },
                        {
                            "remote_location": "http://example.com/pkg2",
                            "checksum": "sha256:5678",
                        }
                    ]
                }
            }
        },
        "gpgkeys": [
            "gpg-key1"
        ]
    }
}


def test_make_depsolve_dnf4_rpm_stage(capsys):
    root(StringIO(json.dumps(fake_input)))
    output = json.loads(capsys.readouterr().out)
    assert output == {
        "tree": {
            "type": "org.osbuild.rpm",
            "inputs": {
                "packages": {
                    "type": "org.osbuild.files",
                    "origin": "org.osbuild.source",
                    "references": [
                        {
                            "id": "sha256:1234",
                        },
                        {
                            "id": "sha256:5678",
                        }
                    ]
                }
            },
            "options": {
                "gpgkeys": [
                    "gpg-key1",
                ],
            }
        }
    }
