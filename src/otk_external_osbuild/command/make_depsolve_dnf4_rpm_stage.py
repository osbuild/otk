import json
import sys


def root():
    data = json.load(sys.stdin)
    tree = data["tree"]

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
                        "gpgkeys": tree["gpgkeys"],
                    },
                }
            }
        )
    )


def main():
    root()


if __name__ == "__main__":
    main()
