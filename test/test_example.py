import pytest
import pathlib
import json

from otk.context import CommonContext, OSBuildContext
from otk.document import Omnifest
from otk.transform import resolve
from otk.target import OSBuildTarget


@pytest.mark.parametrize("path", (pathlib.Path(__file__).parent / "data/base").glob("*.yaml"))
def test_base(path):
    with open(path) as src, open(path.with_suffix(".json")) as dst:
        ctx = CommonContext(path.parent)
        doc = Omnifest.from_yaml_file(src)

        tree0 = resolve(ctx, doc.tree)

        spc = OSBuildContext(ctx)
        tree0 = resolve(spc, tree0["otk.target.osbuild.name"])
        txt = OSBuildTarget().as_string(spc, tree0)

        tree0 = json.loads(txt)
        tree1 = json.load(dst)

        assert tree0 == tree1
