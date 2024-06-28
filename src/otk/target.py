import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from .context import CommonContext, OSBuildContext
from .constant import PREFIX_TARGET

log = logging.getLogger(__name__)


class Target(ABC):
    @abstractmethod
    def is_valid(self, tree: Any) -> bool: ...

    @abstractmethod
    def as_string(self, context: Any, tree: Any, pretty: bool = True) -> str: ...


# NOTE this common target is a bit weird, we probably shouldn't always assume JSON but
# NOTE it makes development a tad easier until we figure out all our targets
class CommonTarget(Target):
    def is_valid(self, tree: Any) -> bool:
        return True

    def as_string(self, context: CommonContext, tree: Any, pretty: bool = True) -> str:
        return json.dumps(tree, indent=2 if pretty else None)


class OSBuildTarget(Target):
    def is_valid(self, tree: Any) -> bool:
        if "version" in tree:
            log.fatal("First level below a 'target' must not contain 'version'.")
            log.fatal("The key 'version' is added by otk internally.")
            return False

        return True

    def as_string(self, context: OSBuildContext, tree: Any, pretty: bool = True) -> str:
        log.debug("as string %r!", context.sources)

        osbuild_tree = tree[PREFIX_TARGET + context.target_requested]
        osbuild_tree["version"] = "2"
        osbuild_tree["sources"] = context.sources

        return json.dumps(osbuild_tree, indent=2 if pretty else None)
