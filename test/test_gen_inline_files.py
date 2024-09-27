import json
import os
from io import StringIO

from otk_external_osbuild.command.gen_inline_files import root

test_input = {
    "tree": {
        "inline": {
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
                },
                "path-text": {
                    "id": "sha256:aac460f1c46997623431e7212c5e34e1f1cb2088989f5738da0d4d034844a219",
                    "data": "VGV4dCBmcm9tIGEgZmlsZSBvbiBkaXNr",
                },
                "path-bytes": {
                    "id": "sha256:176e605efa4b7ae0ad5315f0959d3d37a8dead002bf65009029994a4d2f50c90",
                    "data": "Qnl0ZXMgZnJvbSBhIGZpbGUgb24gZGlzaw==",
                }
            }
        }
    }
}


def test_gen_inline_files(capsys, tmp_path):
    # add temporary file paths to input struct
    input_txt = tmp_path / "embed-file.txt"
    input_txt.write_text("Text from a file on disk", encoding="utf-8")

    input_bytes = tmp_path / "embed-file.bin"
    input_bytes.write_bytes("Bytes from a file on disk".encode("utf-8"))
    test_input["tree"]["paths"] = {
        "path-text": {
            "path": os.fspath(input_txt),
            "type": "text",
        },
        "path-bytes": {
            "path": os.fspath(input_bytes),
            "type": "binary",
        }
    }

    root(StringIO(json.dumps(test_input)))
    output = json.loads(capsys.readouterr().out)
    assert output == expected_output
