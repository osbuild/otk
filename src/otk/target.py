import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from .context import CommonContext, OSBuildContext
from .constant import PREFIX_TARGET
from .error import ParseError

log = logging.getLogger(__name__)


class Target(ABC):
    @abstractmethod
    def ensure_valid(self, tree: Any) -> None: ...

    @abstractmethod
    def as_string(self, context: Any, tree: Any, pretty: bool = True) -> str: ...


class OSBuildTarget(Target):
    def ensure_valid(self, tree: Any) -> None:
        if "version" in tree:
            raise ParseError(
                "First level below a 'target' must not contain 'version'. "
                "The key 'version' is added by otk internally.")

    def as_string(self, context: OSBuildContext, tree: Any, pretty: bool = True) -> str:
        log.debug("as string %r!", context.sources)

        osbuild_tree = tree[PREFIX_TARGET + context.target_requested]
        osbuild_tree["version"] = "2"
        osbuild_tree["sources"] = context.sources

        return json.dumps(osbuild_tree, indent=2 if pretty else None)
