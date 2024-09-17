import hashlib
import json
import os
import subprocess
import sys
from typing import TextIO


def transform(packages):
    """Transform the output of `osbuild-depsolve-dnf4` to the output format
    expected of this external."""

    data = {"tree": {"const": {"internal": {}}}}

    # Expose the direct output as internal-only data, this can be used by
    # other externals.
    data["tree"]["const"]["internal"]["packages"] = packages

    # We also store all resolved packages and some meta information about
    # them, this just turns the list into a more user-friendly accessible
    # map keyed by package name.
    data["tree"]["const"]["versions"] = {}

    for package in packages:
        data["tree"]["const"]["versions"][package["name"]] = package

    return data


def mockdata(packages):
    """Mockdata as used by tests, we don't actually execute the depsolver
    but return a map that's similar enough in format that the rest of the
    compile can continue."""

    return [
        {
            "name": p,
            "checksum": "sha256:" + hashlib.sha256(p.encode()).hexdigest(),
            "remote_location": f"https://example.com/repo/packages/{p}",
            "version": "0",
            "epoch": "",
            "release": "0",
            "arch": "noarch",
        }
        for p in packages
    ]


def root(input_stream: TextIO) -> None:
    data = json.loads(input_stream.read())
    tree = data["tree"]
    if "OTK_UNDER_TEST" in os.environ:
        packages = mockdata(tree["packages"]["include"])
        sys.stdout.write(json.dumps(transform(packages)))
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
        raise RuntimeError(f"{process.stdout=}{process.stderr=}")

    results = json.loads(process.stdout)
    packages = results.get("packages", [])

    sys.stdout.write(json.dumps(transform(packages)))


def main():
    root(sys.stdin)


if __name__ == "__main__":
    main()
