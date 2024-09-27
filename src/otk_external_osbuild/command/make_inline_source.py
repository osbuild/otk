import json
import sys
from typing import TextIO


def root(input_stream: TextIO) -> None:
    data = json.load(input_stream)
    tree = data["tree"]
    files = tree["const"]["files"]

    items = {}

    for file in files.values():
        items[file["id"]] = {
            "encoding": "base64",
            "data": file["data"],
        }

    sys.stdout.write(
        json.dumps(
            {
                "tree": {"org.osbuild.inline": {"items": items}}
            }
        )
    )


def main():
    root(sys.stdin)


if __name__ == "__main__":
    main()
