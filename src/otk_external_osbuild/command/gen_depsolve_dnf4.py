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

    return data


def mockdata(packages, architecture):
    """Mockdata as used by tests, we don't actually execute the depsolver
    but return a map that's similar enough in format that the rest of the
    compile can continue."""

    # see https://github.com/osbuild/images/pull/937
    def ver(pkg_name):
        return str(ord(pkg_name[0]) % 9)

    def release(pkg_name):
        return str(ord(pkg_name[1]) % 9)
    return [
        {
            "name": p,
            "checksum": "sha256:" + hashlib.sha256(p.encode()).hexdigest(),
            "remote_location": f"https://example.com/repo/packages/{p}",
            "version": ver(p),
            "epoch": "0",
            "release": release(p) + ".fk1",
            "arch": architecture,
        }
        for p in packages["include"] + [f"exclude:{p}" for p in packages["exclude"]]
    ]


def root(input_stream: TextIO) -> None:
    data = json.loads(input_stream.read())
    tree = data["tree"]
    if "OTK_UNDER_TEST" in os.environ:
        packages = mockdata(tree["packages"], tree["architecture"])
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
