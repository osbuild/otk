import base64
import hashlib
import json
import sys
from typing import TextIO


def root(input_stream: TextIO) -> None:
    data = json.loads(input_stream.read())
    tree = data["tree"]

    files = tree["files"]
    inlines: dict = {}
    for name, item in files.items():
        contents = item["contents"].encode("utf8")

        digest = hashlib.sha256(contents).hexdigest()
        source_id = f"sha256:{digest}"

        b64contents = base64.b64encode(contents).decode("utf8")
        inlines[name] = {
            "id": source_id,
            "data": b64contents,
        }

    output = {
        "tree": {
            "const": {
                "files": inlines,
            }
        }
    }

    sys.stdout.write(json.dumps(output))


def main():
    root(sys.stdin)


if __name__ == "__main__":
    main()
