"""Support for calling external programs to transform trees. External programs
receive the current context and the subtree to operate on in JSON. They are
expected to return the context and subtree.

Returned subtrees are resolved during tree transformation."""

import json
import logging
import subprocess
import sys
from typing import Any

from .context import Context, OSBuildContext

log = logging.getLogger(__name__)


def call(context: Context, directive: str, tree: Any) -> Any:
    if directive not in registry:
        log.fatal("unknown external %r", directive)

        # TODO exception
        sys.exit(1)
        return

    required_context, executable = registry[directive]

    if not isinstance(context, required_context):
        log.fatal("external %r with wrong context %r", directive, context)

        # TODO exception
        sys.exit(1)
        return

    data = json.dumps(
        {
            "context": context.for_external(),
            "tree": tree,
        }
    )

    process = subprocess.run(executable, input=data, encoding="utf8", capture_output=True)

    if process.returncode != 0:
        # TODO exception
        log.error(
            "call: %r %r %r failed: %r, %r",
            executable,
            context,
            directive,
            process.stdout,
            process.stderr,
        )
        sys.exit(1)
        return

    # Otherwise everything is good and we restore
    data = json.loads(process.stdout)

    context.from_external(data["context"])

    # TODO restore context
    return data["tree"]


registry = {
    "otk.external.osbuild.depsolve_dnf4": (
        OSBuildContext,
        ["otk-osbuild", "depsolve_dnf4"],
    ),
    "otk.external.osbuild.depsolve_dnf5": (
        OSBuildContext,
        ["otk-osbuild", "depsolve_dnf5"],
    ),
    "otk.external.osbuild.file_from_text": (
        OSBuildContext,
        ["otk-osbuild", "file-from-text"],
    ),
    "otk.external.osbuild.file_from_path": (
        OSBuildContext,
        ["otk-osbuild", "file-from-path"],
    ),
}
