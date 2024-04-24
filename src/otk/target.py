import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from .context import Context, OSBuildContext


log = logging.getLogger(__name__)


class Target(ABC):
    @abstractmethod
    def is_valid(self, tree: Any) -> bool: ...

    @abstractmethod
    def as_string(self, context: Context, tree: Any, pretty: bool) -> str: ...


class OSBuildTarget(Target):
    def is_valid(self, tree: Any) -> bool:
        return True

    def as_string(self, context: OSBuildContext, tree: Any, pretty: bool = True) -> str:
        log.debug("as string %r!", context.sources)

        # TODO: test these
        tree["version"] = "2"
        tree["sources"] = context.sources

        return json.dumps(tree, indent=2 if pretty else None)


registry = {
    "osbuild": OSBuildTarget,
}
