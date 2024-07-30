"""`otk-external-osbuild` is an [otk](https://github.com/osbuild/otk) external
to work with [osbuild](https://github.com/osbuild/osbuild) manifests.

It currently implements:

- `otk.external.osbuild_depsolve_dnf4_defines`: Depsolving through
  `osbuild-depsolve-dnf4`.

THIS FILE IS VERY, VERY PROOF OF CONCEPT AND NEEDS TO BE CLEANED UP"""

import sys
import json
import hashlib
import base64
import pathlib
import subprocess

import argparse


def source_add_curl(data, checksum, url):
    source_add("org.osbuild.curl", data)

    if checksum not in data["org.osbuild.curl"]["items"]:
        data["org.osbuild.curl"]["items"][checksum] = {"url": url}


def depsolve_dnf4_defines() -> int:
    """Dependency solve a set of included and excluded packages from a set of
       given repositories."""

    # Our data structure requires a `tree` key.
    data = json.loads(sys.stdin.read())

    if "tree" not in data:
        raise ValueError("missing `tree` key in data")

    tree = data["tree"]

    # And our relevant external-name needs to be in that tree
    if "otk.external.osbuild_depsolve_dnf4_defines" not in tree:
        raise ValueError("missing `otk.external.osbuild_depsolve_dnf4_defines` key in tree")

    tree = tree["otk.external.osbuild_depsolve_dnf4_defines"]

    # Empty dictionary to contain our sources
    srcs = {}

    # Empty dictionary to contain meta information about the performed request
    meta = {}

    if "org.osbuild.curl" not in srcs:
        srcs["org.osbuild.curl"] = {"items": {}}

    # The request as given to `osbuild-depsolve-dnf4`, most of the relevant
    # inputs come directly from the tree we've received from `otk`.
    request = {
        "command": "depsolve",
        "arch": tree["architecture"],
        "module_platform_id": f"platform:{tree['module_platform_id']}",
        "releasever": tree["releasever"],
        "cachedir": "/tmp",
        "arguments": {
            "root_dir": "/tmp",
            "repos": tree["repositories"],
            "transactions": [
                {
                    "package-specs": tree["packages"].get("include", []),
                    "exclude-specs": tree["packages"].get("exclude", []),
                },
            ],
        },
    }

    # Run the external depsolver
    process = subprocess.run(
        ["/usr/libexec/osbuild-depsolve-dnf"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        input=json.dumps(request),
        encoding="utf8",
        check=False,
    )

    if process.returncode != 0:
        raise RuntimeError(process.stderr)

    results = json.loads(process.stdout)

    for package in results.get("packages", []):
        srcs["org.osbuild.curl"]["items"][package["checksum"]] = package["remote_location"]
        meta[package["name"]] = package

    sys.stdout.write(json.dumps({
        "tree": {
            "stages": [{
                "type": "org.osbuild.rpm",
                "inputs": {
                    "packages": {
                        "type": "org.osbuild.files",
                        "origin": "org.osbuild.source",
                        "references": [
                            {
                                "id": package["checksum"],
                                "options": {"metadata": {"rpm.check_gpg": True}},
                            }
                            for package in results.get("packages", [])
                        ],
                    }
                },
                "options": {
                    "gpgkeys": tree["gpgkeys"],
                },
            }],
            "sources": {"curl": srcs["org.osbuild.curl"]},
            "meta": meta,
        }
    }))

    return 0


def root():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    (subparsers.add_parser("depsolve_dnf4")).set_defaults(func=depsolve_dnf4)
    (subparsers.add_parser("file_from_text")).set_defaults(func=file_from_text)
    (subparsers.add_parser("file_from_path")).set_defaults(func=file_from_path)

    args = parser.parse_args()
    return args.func()
