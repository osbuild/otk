"""Support for calling external programs to transform trees. External programs
receive the subtree to operate on in JSON. They are expected to return a new
subtree."""

import json
import logging
import pathlib
import subprocess
import os
from typing import Any

from .constant import PREFIX_EXTERNAL
from .error import ExternalFailedError

log = logging.getLogger(__name__)


def call(directive: str, tree: Any) -> Any:
    exe = exe_from_directive(directive)
    exe = path_for(exe)

    data = json.dumps(
        {
            "tree": tree,
        }
    )

    process = subprocess.run([exe], input=data, encoding="utf8", capture_output=True, check=False)
    if process.returncode != 0:
        msg = f"call: {exe!r} {directive!r} failed: {process.stdout!r}, {process.stderr!r}"
        log.error(msg)
        raise ExternalFailedError(msg)

    res = json.loads(process.stdout)
    return res["tree"]


def exe_from_directive(directive):
    return directive.removeprefix(PREFIX_EXTERNAL)


def path_for(exe):
    paths = [
        "/usr/local/libexec/otk/external",
        "/usr/libexec/otk/external",
        "/usr/local/lib/otk/external",
        "/usr/lib/otk/external",
        # local developer case
        "./externals",
    ]

    env = os.getenv("OTK_EXTERNAL_PATH", None)

    if env is not None:
        paths = [env] + paths

    for pathname in paths:
        path = pathlib.Path(pathname) / exe

        if path.exists() and os.access(path, os.X_OK):
            return path

    raise RuntimeError(f"could not find {exe!r} in any search path {paths!r}")
