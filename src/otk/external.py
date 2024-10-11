"""Support for calling external programs to transform trees. External programs
receive the subtree to operate on in JSON. They are expected to return a new
subtree."""

import json
import logging
import pathlib
import subprocess
import os
from typing import Any

from .annotation import AnnotatedNode
from .constant import PREFIX_EXTERNAL
from .error import ExternalFailedError
from .traversal import State

log = logging.getLogger(__name__)


def call(state: State, directive: str, tree: AnnotatedNode) -> Any:
    exe = exe_from_directive(directive)
    exe = path_for(exe)

    tree_dump = tree.deep_dump()

    data = json.dumps(
        {
            "tree": tree_dump,
        }
    )

    process = subprocess.run([exe], input=data, encoding="utf8", capture_output=True, check=False)
    if process.returncode != 0:
        msg = f"call {exe} {directive!r} failed: stdout={process.stdout!r}, stderr={process.stderr!r}"
        log.error(msg)
        raise ExternalFailedError(msg, state)

    res = json.loads(process.stdout)
    ret = AnnotatedNode.get_specific_type(res["tree"])

    if all(attr in tree.annotations for attr in ('src',
                                                 'content_filename',
                                                 'content_line_number',
                                                 'content_line_number_end')):
        ret.annotations["src"] = (f"result of {directive} ({tree.annotations['src']})\n"
                                  f"with input from {tree.annotations['content_filename']}:"
                                  f"{tree.annotations['content_line_number']}-"
                                  f"{tree.annotations['content_line_number_end']}")
    return ret


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
