import json
from io import StringIO

from otk_external_osbuild.command.get_dnf4_package_info import root


fake_input = {
    "tree": {
        "packagename": "foo",
        "packageset": {
            "const": {
                "internal": {
                    "packages": [
                        {
                            "name": "foo",
                            "version": "1",
                            "release": "fc30",
                            "arch": "c64",
                        },
                        {
                            "name": "bar",
                            "version": "2",
                            "release": "fc40",
                            "arch": "c128",
                        },
                    ]
                }
            }
        }
    }
}


def test_make_depsolve_dnf4_curl_source(capsys):
    root(StringIO(json.dumps(fake_input)))
    output = json.loads(capsys.readouterr().out)
    assert output == {
        "tree": {
            "version": "1",
            "release": "fc30",
            "arch": "c64",
        }
    }
