import json
from io import StringIO

from otk_external_osbuild.command.make_depsolve_dnf4_curl_source import root


fake_input = {
    "tree": {
        "packagesets": [
            {
                "const": {
                    "internal": {
                        "packages": [
                            {
                                "remote_location": "http://example.com/pkg1",
                                "checksum": "sha256:1234",
                            },
                        ]
                    }
                }
            },
            {
                "const": {
                    "internal": {
                        "packages": [
                            {
                                "remote_location": "http://example.com/pkg2",
                                "checksum": "sha256:5678",
                            },
                        ]
                    }
                }
            },
        ]
    }
}


def test_make_depsolve_dnf4_curl_source(capsys):
    root(StringIO(json.dumps(fake_input)))
    output = json.loads(capsys.readouterr().out)
    assert output == {
        "tree": {
            "org.osbuild.curl": {
                "items": {
                    "sha256:1234": {
                        "url": "http://example.com/pkg1",
                    },
                    "sha256:5678": {
                        "url": "http://example.com/pkg2",
                    }
                }
            }
        }
    }
