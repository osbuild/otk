import logging
from copy import deepcopy
from typing import Any

from .constant import PREFIX, PREFIX_TARGET, NAME_VERSION
from .context import CommonContext, OSBuildContext
from .error import NoTargetsError, ParseError, ParseVersionError, OTKError
from .transform import process_include
from .traversal import State
from .target import OSBuildTarget
from .annotation import AnnotatedDict, AnnotatedPath

log = logging.getLogger(__name__)


class Omnifest:
    _tree: AnnotatedDict[str, Any]
    _ctx: CommonContext
    _osbuild_ctx: OSBuildContext
    _target: str

    def __init__(self, path: AnnotatedPath, target: str = "", *, warn_duplicated_defs: bool = False) -> None:
        self._ctx = CommonContext(target_requested=target, warn_duplicated_defs=warn_duplicated_defs)
        self._target = target
        # XXX: redo using a type-safe target registry
        if target:
            if not target.startswith("osbuild"):
                raise OTKError("only target osbuild supported right now")
            self._osbuild_ctx = OSBuildContext(self._ctx)
        state = State()
        tree = process_include(self._ctx, state, path)
        # XXX: review this code, the idea is to find top-level keys that
        # have no targets but that of course only works if there are
        # no targets in the resolving. this means we are currently forced
        # to resolve without target first to get this kind of error checking
        # :(
        if self._target == "":
            Omnifest.ensure(tree)
        self._tree = tree

    @classmethod
    def ensure(cls, deserialized_data: AnnotatedDict[str, Any]) -> None:
        """Take a dictionary and ensure that its keys and values would be
        considered an Omnifest."""

        # And that dictionary needs to contain certain keys to indicate this
        # being an Omnifest.
        if NAME_VERSION not in deserialized_data:
            raise ParseVersionError(f"omnifest must contain a key by the name of {NAME_VERSION!r}")

        # no toplevel keys without a target or an otk directive
        targetless_keys = [
            f" * \"{key}\" in {deserialized_data[key].get_annotation('src')}"
            for key in deserialized_data
            if not key.startswith(PREFIX)
        ]

        if len(targetless_keys):
            targetless_keys_str = '\n'.join(targetless_keys)
            raise ParseError(f"otk file contains top-level keys without a target:\n{targetless_keys_str}")

        target_available = _targets(deserialized_data)
        if not target_available:
            raise NoTargetsError("input does not contain any targets")

    @property
    def tree(self) -> dict[str, Any]:
        return deepcopy(self._tree)

    @property
    def targets(self) -> dict[str, Any]:
        """ Return a dict of target(s) and their subtree(s) """
        return _targets(self._tree)

    def as_target_string(self) -> str:
        # XXX: redo using type-safe target registry
        if not self._target.startswith("osbuild"):
            raise OTKError("only osbuild targets supported right now")
        target = OSBuildTarget()
        target.ensure_valid(self._tree)
        return target.as_string(self._osbuild_ctx, self._tree)


def _targets(tree: dict[str, Any]) -> dict[str, Any]:
    return {
        key.removeprefix(PREFIX_TARGET): val
        for key, val in tree.items() if key.startswith(PREFIX_TARGET)
    }
