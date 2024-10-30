"""Support for calling external programs to transform trees. External programs
receive the subtree to operate on in JSON. They are expected to return a new
subtree."""

import json
import logging
import pathlib
import subprocess
import os
from typing import Any

from . import ui

from .constant import PREFIX_EXTERNAL
from .error import ExternalFailedError
from .traversal import State


log = ui.Terminal(logging.getLogger(__name__))


def call(state: State, directive: str, tree: Any) -> Any:
    exe = exe_from_directive(directive)
    exe = path_for(exe)

    data = json.dumps(
        {
            "tree": tree,
        }
    )

    with log.spinner(f"Executing external {os.path.basename(exe)}"):
        process = subprocess.run([exe], input=data, encoding="utf8", capture_output=True, check=False)

    if process.returncode != 0:
        msg = f"call {exe} {directive!r} failed: stdout={process.stdout!r}, stderr={process.stderr!r}"
        log.error(msg)
        raise ExternalFailedError(msg, state)

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
    ]

    env = os.getenv("OTK_EXTERNAL_PATH", None)

    if env is not None:
        paths = env.split(":") + paths

    for pathname in paths:
        path = pathlib.Path(pathname) / exe

        if path.exists() and os.access(path, os.X_OK):
            return path

    raise RuntimeError(f"could not find {exe!r} in any search path {paths!r}")
