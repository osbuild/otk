import json
from io import StringIO

from otk_external_osbuild.command.gen_inline_files import root

test_input = {
    "tree": {
        "files": {
            "bob": {
                "contents": "Hello Bob\nHow's it going?\n"
            },
            "test": {
                "contents": "Let's test the inline file generator."
            }
        }
    }
}

expected_output = {
    "tree": {
        "const": {
            "files": {
                "bob": {
                    "id": "sha256:5e557cb2cceecc1845e8210350c4aa09d2925a3bfbe54c59c10e02e3d03555f6",
                    "data": "SGVsbG8gQm9iCkhvdydzIGl0IGdvaW5nPwo=",
                },
                "test": {
                    "id": "sha256:0f26599ad3142e51c0781c93677eba62b4a28db327bc9eb443aaa764976045de",
                    "data": "TGV0J3MgdGVzdCB0aGUgaW5saW5lIGZpbGUgZ2VuZXJhdG9yLg==",
                }
            }
        }
    }
}


def test_gen_inline_files(capsys):
    root(StringIO(json.dumps(test_input)))
    output = json.loads(capsys.readouterr().out)
    assert output == expected_output
