"""Support for calling external programs to transform trees. External programs
receive the subtree to operate on in JSON. They are expected to return a new
subtree."""

import json
import logging
import pathlib
import subprocess
import sys
import os
from typing import Any

from .constant import PREFIX_EXTERNAL

log = logging.getLogger(__name__)


def call(directive: str, tree: Any) -> Any:
    exe = exe_from_directive(directive)
    exe = path_for(exe)

    data = json.dumps(
        {
            "tree": {
                directive: tree,
            },
        }
    )

    process = subprocess.run([exe], input=data, encoding="utf8", capture_output=True)

    if process.returncode != 0:
        # TODO exception
        log.error(
            "call: %r %r failed: %r, %r",
            exe,
            directive,
            process.stdout,
            process.stderr,
        )
        sys.exit(1)
        return

    data = json.loads(process.stdout)

    return data["tree"]


def exe_from_directive(directive):
    exe = directive.removeprefix(PREFIX_EXTERNAL)
    return f"otk_external_{exe}"


def path_for(exe):
    paths = [
        "/usr/local/libexec/otk",
        "/usr/libexec/otk",
        "/usr/local/lib/otk",
        "/usr/lib/otk",
    ]

    env = os.getenv("OTK_EXTERNAL_PATH", None)

    if env is not None:
        paths = [env] + paths

    for path in paths:
        path = pathlib.Path(path) / exe

        if path.exists() and os.access(path, os.X_OK):
            return path

    raise RuntimeError(f"could not find {exe!r} in any search path {paths!r}")
