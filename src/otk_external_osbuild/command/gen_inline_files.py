import base64
import hashlib
import json
import pathlib
import sys
from typing import TextIO


def process_contents(contents):
    digest = hashlib.sha256(contents).hexdigest()
    source_id = f"sha256:{digest}"
    b64contents = base64.b64encode(contents).decode("utf8")
    return {
        "id": source_id,
        "data": b64contents,
    }


def root(input_stream: TextIO) -> None:
    data = json.loads(input_stream.read())
    tree = data["tree"]

    inline_files = tree.get("inline", {})
    inlines: dict = {}
    for name, item in inline_files.items():
        contents = item["contents"].encode("utf8")
        inlines[name] = process_contents(contents)

    inline_paths = tree.get("paths", {})
    for name, item in inline_paths.items():
        path = item["path"]
        read_type = item["type"]
        if read_type == "text":
            contents = pathlib.Path(path).read_text(encoding="utf-8").encode("utf-8")
        elif read_type == "binary":
            contents = pathlib.Path(path).read_bytes()
        else:
            raise ValueError(f"invalid type for inline path {path}: {read_type}")

        inlines[name] = process_contents(contents)

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
