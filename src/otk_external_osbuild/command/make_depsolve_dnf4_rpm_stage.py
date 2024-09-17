import json
import sys
from typing import TextIO


def root(input_stream: TextIO) -> None:
    data = json.load(input_stream)
    tree = data["tree"]["packageset"]["const"]["internal"]

    sys.stdout.write(
        json.dumps(
            {
                "tree": {
                    "type": "org.osbuild.rpm",
                    "inputs": {
                        "packages": {
                            "type": "org.osbuild.files",
                            "origin": "org.osbuild.source",
                            "references": [
                                {
                                    "id": package["checksum"],
                                }
                                for package in tree["packages"]
                            ],
                        },
                    },
                    "options": {
                        "gpgkeys": data["tree"]["gpgkeys"],
                    },
                }
            }
        )
    )


def main():
    root(sys.stdin)


if __name__ == "__main__":
    main()
