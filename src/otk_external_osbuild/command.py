"""`otk-osbuild` is the [otk](https://github.com/osbuild/otk) external to work
with [osbuild](https://github.com/osbuild/osbuild) manifests.

THIS FILE IS VERY, VERY PROOF OF CONCEPT AND NEEDS TO BE CLEANED UP"""

import sys
import json
import hashlib
import base64
import pathlib
import subprocess

import argparse


def source_add(kind, data):
    """Add an osbuild source to the tree."""

    # Initialize empty sources
    if data.get(kind) is None:
        data[kind] = {"items": {}}


def source_add_inline(data, text):
    source_add("org.osbuild.inline", data)

    text = text.encode("utf8")
    hashsum = hashlib.sha256(text).hexdigest()
    addr = f"sha256:{hashsum}"

    if addr not in data["org.osbuild.inline"]["items"]:
        data["org.osbuild.inline"]["items"][addr] = {
            "encoding": "base64",
            "data": base64.b64encode(text).decode("utf8"),
        }

    return hashsum, f"sha256:{hashsum}"


def source_add_curl(data, checksum, url):
    source_add("org.osbuild.curl", data)

    if checksum not in data["org.osbuild.curl"]["items"]:
        data["org.osbuild.curl"]["items"][checksum] = {"url": url}


def depsolve_dnf4_defines():
    data = json.loads(sys.stdin.read())
    tree = data["tree"]["otk.external.osbuild_depsolve_dnf4_defines"]
    srcs = {}

    source_add("org.osbuild.rpm", srcs)

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
        raise Exception(process.stderr)  # pylint: disable=broad-exception-raised

    results = json.loads(process.stdout)

    for package in results.get("packages", []):
        source_add_curl(srcs, package["checksum"], package["remote_location"])

    out = {
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
            "sources": {"rpms": srcs["org.osbuild.rpm"]},
        }
    }

    sys.stdout.write(
        json.dumps(out)
    )


def file_from_text():
    data = json.loads(sys.stdin.read())

    dest = data["tree"]["destination"]
    hashsum, addr = source_add_inline(data, data["tree"]["text"])

    sys.stdout.write(
        json.dumps(
            {
                "context": data["context"],
                "tree": {
                    "type": "org.osbuild.copy",
                    "inputs": {
                        f"file-{hashsum}": {
                            "type": "org.osbuild.files",
                            "origin": "org.osbuild.source",
                            "references": [
                                {"id": addr},
                            ],
                        }
                    },
                    "options": {
                        "paths": [
                            {
                                "from": f"input://file-{hashsum}/{addr}",
                                "to": f"tree://{dest}",
                                "remove_destination": True,
                            }
                        ]
                    },
                },
            }
        )
    )


def file_from_path():
    data = json.loads(sys.stdin.read())

    dest = data["tree"]["destination"]
    text = (pathlib.Path(data["context"]["path"]) / data["tree"]["source"]).read_text()
    hashsum, addr = source_add_inline(data, text)

    sys.stdout.write(
        json.dumps(
            {
                "context": data["context"],
                "tree": {
                    "type": "org.osbuild.copy",
                    "inputs": {
                        f"file-{hashsum}": {
                            "type": "org.osbuild.files",
                            "origin": "org.osbuild.source",
                            "references": [
                                {"id": addr},
                            ],
                        }
                    },
                    "options": {
                        "paths": [
                            {
                                "from": f"input://file-{hashsum}/{addr}",
                                "to": f"tree://{dest}",
                                "remove_destination": True,
                            }
                        ]
                    },
                },
            }
        )
    )


def root():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    (subparsers.add_parser("depsolve_dnf4")).set_defaults(func=depsolve_dnf4)
    (subparsers.add_parser("file_from_text")).set_defaults(func=file_from_text)
    (subparsers.add_parser("file_from_path")).set_defaults(func=file_from_path)

    args = parser.parse_args()
    args.func()
