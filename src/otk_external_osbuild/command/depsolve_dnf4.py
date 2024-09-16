"""`otk-osbuild` is the [otk](https://github.com/osbuild/otk) external to work
with [osbuild](https://github.com/osbuild/osbuild) manifests.

THIS FILE IS VERY, VERY PROOF OF CONCEPT AND NEEDS TO BE CLEANED UP"""

import hashlib
import json
import os
import subprocess
import sys


def root():
    data = json.loads(sys.stdin.read())
    tree = data["tree"]
    mock = "OTK_UNDER_TEST" in os.environ

    # When we are under test we don't call the depsolver at all and instead
    # return a mocked list of things
    if mock:
        sys.stdout.write(
            json.dumps(
                {
                    "tree": {
                        "const": {
                            "internal": {
                                "packages": [
                                    {
                                        "checksum": "sha256:"
                                        + hashlib.sha256(
                                            p.encode()
                                        ).hexdigest(),
                                        "remote_location": f"https://example.com/repo/packages/{p}",
                                    }
                                    for p in tree["packages"]["include"]
                                ],
                            },
                        }
                    },
                }
            )
        )
        return

    request = {
        "command": "depsolve",
        "arch": tree["architecture"],
        "module_platform_id": "platform:" + tree["module_platform_id"],
        "releasever": tree["releasever"],
        "cachedir": "/tmp",
        "arguments": {
            "root_dir": "/tmp",
            "repos": tree["repositories"],
            "transactions": [
                {
                    "package-specs": tree["packages"]["include"],
                    "exclude-specs": tree["packages"].get("exclude", []),
                },
            ],
        },
    }

    process = subprocess.run(
        ["/usr/libexec/osbuild-depsolve-dnf"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        input=json.dumps(request),
        encoding="utf8",
        check=False,
    )

    if process.returncode != 0:
        # TODO: fix this
        raise RuntimeError(
            process.stderr
        )  # pylint: disable=broad-exception-raised

    results = json.loads(process.stdout)
    packages = results.get("packages", [])

    sys.stdout.write(
        json.dumps(
            {
                "tree": {"const": {"internal": {"packages": packages}}},
            },
        ),
    )


def main():
    root()


if __name__ == "__main__":
    main()
