import json
import sys
from typing import TextIO


def root(input_stream: TextIO) -> None:
    data = json.load(input_stream)
    tree = data["tree"]
    pkgs = tree["packageset"]["const"]["internal"]

    # allow passing on rpm stage options
    opts = tree.get("options", {}).get("rpm_stage", {})

    # perhaps gpgkeys should move *under* options?
    # it should: https://github.com/osbuild/otk/issues/218
    opts["gpgkeys"] = tree["gpgkeys"]

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
                                for package in pkgs["packages"]
                            ],
                        },
                    },
                    "options": opts,
                }
            }
        )
    )


def main():
    root(sys.stdin)


if __name__ == "__main__":
    main()
