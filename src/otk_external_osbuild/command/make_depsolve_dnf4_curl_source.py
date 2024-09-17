import itertools
import json
import sys
from typing import TextIO


def root(input_stream: TextIO) -> None:
    data = json.load(input_stream)
    tree = data["tree"]

    sources: dict = {"org.osbuild.curl": {"items": {}}}

    for package in itertools.chain.from_iterable(
        s["const"]["internal"]["packages"] for s in tree["packagesets"]
    ):
        sources["org.osbuild.curl"]["items"][package["checksum"]] = {
            "url": package["remote_location"],
        }

    sys.stdout.write(
        json.dumps(
            {
                "tree": sources,
            }
        )
    )


def main():
    root(sys.stdin)


if __name__ == "__main__":
    main()
