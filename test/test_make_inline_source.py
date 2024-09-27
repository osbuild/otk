import json
from io import StringIO
from test.test_gen_inline_files import expected_output

from otk_external_osbuild.command.make_inline_source import root

# use the output from test_gen_inline_files
test_input = expected_output


def test_make_inline_source(capsys):
    root(StringIO(json.dumps(test_input)))
    output = json.loads(capsys.readouterr().out)
    assert output == {
        "tree": {
            "org.osbuild.inline": {
                "items": {
                    "sha256:5e557cb2cceecc1845e8210350c4aa09d2925a3bfbe54c59c10e02e3d03555f6": {
                        "encoding": "base64",
                        "data": "SGVsbG8gQm9iCkhvdydzIGl0IGdvaW5nPwo=",
                    },
                    "sha256:0f26599ad3142e51c0781c93677eba62b4a28db327bc9eb443aaa764976045de": {
                        "encoding": "base64",
                        "data": "TGV0J3MgdGVzdCB0aGUgaW5saW5lIGZpbGUgZ2VuZXJhdG9yLg==",
                    },
                    "sha256:aac460f1c46997623431e7212c5e34e1f1cb2088989f5738da0d4d034844a219": {
                        "encoding": "base64",
                        "data": "VGV4dCBmcm9tIGEgZmlsZSBvbiBkaXNr",
                    },
                    "sha256:176e605efa4b7ae0ad5315f0959d3d37a8dead002bf65009029994a4d2f50c90": {
                        "encoding": "base64",
                        "data": "Qnl0ZXMgZnJvbSBhIGZpbGUgb24gZGlzaw==",
                    }
                }
            }
        }
    }
