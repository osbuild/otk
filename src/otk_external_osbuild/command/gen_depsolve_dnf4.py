import hashlib
import json
import os
import subprocess
import sys
from typing import List, Optional, TextIO


def find_pkg_by_name(packages: List[dict], pkg_name: str) -> Optional[dict]:
    for pkg in packages:
        if pkg["name"] == pkg_name:
            return pkg
    return None


def transform(tree: dict, packages: List[dict]) -> dict:
    """Transform the output of `osbuild-depsolve-dnf4` to the output format
    expected of this external."""

    data: dict = {"tree": {"const": {"internal": {}}}}

    # Expose the direct output as internal-only data, this can be used by
    # other externals.
    data["tree"]["const"]["internal"]["packages"] = packages

    if kernel_pkg_name := tree.get("kernel_pkgname"):
        # We also store all resolved kernel
        data["tree"]["const"]["kernel"] = {}

        kernel_pkg = find_pkg_by_name(packages, kernel_pkg_name)
        if kernel_pkg:
            data["tree"]["const"]["kernel"] = {
                "name": kernel_pkg["name"],
                "version": kernel_pkg["version"],
            }

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
            "version": "",
        }
        for p in packages
    ]


def root(input_stream: TextIO) -> None:
    data = json.loads(input_stream.read())
    tree = data["tree"]

    packages = mockdata(tree["packages"]["include"])
    if kernel_pkg_name := tree.get("kernel", {}).get("name"):
        packages.append(kernel_pkg_name)

    mock = "OTK_UNDER_TEST" in os.environ

    # When we are under test we don't call the depsolver at all and instead
    # return a mocked list of things
    if mock:
        sys.stdout.write(json.dumps(transform(tree, packages)))
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

    sys.stdout.write(json.dumps(transform(tree, packages)))


def main():
    root(sys.stdin)


if __name__ == "__main__":
    main()
