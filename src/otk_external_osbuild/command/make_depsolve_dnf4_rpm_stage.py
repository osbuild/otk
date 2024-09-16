"""`otk-osbuild` is the [otk](https://github.com/osbuild/otk) external to work
with [osbuild](https://github.com/osbuild/osbuild) manifests.

THIS FILE IS VERY, VERY PROOF OF CONCEPT AND NEEDS TO BE CLEANED UP"""

import json
import sys


def root():
    data = json.load(sys.stdin)
    tree = data["tree"]["packages"]["const"]["internal"]

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
    root()


if __name__ == "__main__":
    main()
