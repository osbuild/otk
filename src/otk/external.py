"""Support for calling external programs to transform trees. External programs
receive the current context and the subtree to operate on in JSON. They are
expected to return the context and subtree.

Returned subtrees are resolved during tree transformation."""

import json
import logging
import pathlib
import subprocess
import sys
import os
from typing import Any

from .context import Context
from .constant import PREFIX_EXTERNAL

log = logging.getLogger(__name__)


def call(context: Context, directive: str, tree: Any) -> Any:
    exe, args = convert(directive)
    exe = search(exe)

    data = json.dumps(
        {
            "tree": tree,
        }
    )

    process = subprocess.run(
        [exe] + args, input=data, encoding="utf8", capture_output=True
    )

    if process.returncode != 0:
        # TODO exception
        log.error(
            "call: %r %r %r failed: %r, %r",
            exe,
            args,
            directive,
            process.stdout,
            process.stderr,
        )
        sys.exit(1)
        return

    return data["tree"]


def convert(directive):
    exe, *args = directive.removeprefix(PREFIX_EXTERNAL).split(".")
    return (f"otk_external_{exe}", args)


def search(exe):
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

        if path.exists():
            return path

    raise RuntimeError(f"could not find {exe!r} in any search path {paths!r}")
