import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from .annotation import AnnotatedBase
from .context import CommonContext, OSBuildContext
from .constant import PREFIX_TARGET
from .error import ParseError

log = logging.getLogger(__name__)


class Target(ABC):
    @abstractmethod
    def ensure_valid(self, tree: Any) -> None: ...

    @abstractmethod
    def as_string(self, context: Any, tree: Any, pretty: bool = True) -> str: ...


# NOTE this common target is a bit weird, we probably shouldn't always assume JSON but
# NOTE it makes development a tad easier until we figure out all our targets
class CommonTarget(Target):
    def ensure_valid(self, _tree: Any) -> None:
        pass

    def as_string(self, context: CommonContext, tree: Any, pretty: bool = True) -> str:
        return json.dumps(tree, indent=2 if pretty else None)


class OSBuildTarget(Target):
    def ensure_valid(self, tree: Any) -> None:
        if "version" in tree:
            raise ParseError(
                "First level below a 'target' must not contain 'version'. "
                "The key 'version' is added by otk internally.")

    def as_string(self, context: OSBuildContext, tree: Any, pretty: bool = True) -> str:
        osbuild_tree = AnnotatedBase.deep_dump(tree[PREFIX_TARGET + context.target_requested])
        osbuild_tree["version"] = "2"

        return json.dumps(osbuild_tree, indent=2 if pretty else None)
