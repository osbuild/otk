import json
import os
import pathlib
import yaml

import pytest

from otk.command import run


@pytest.mark.parametrize("ref_yaml",
                         [str(path) for path in (pathlib.Path(__file__).parent / "data/images-ref").glob("*.yaml")])
def test_images_ref(tmp_path, ref_yaml):
    os.environ["OSBUILD_TESTING_RNG_SEED"] = "0"

    ref_yaml_path = pathlib.Path(ref_yaml)
    with ref_yaml_path.open() as fp:
        ref_manifest = yaml.safe_load(fp)

    src_yaml = pathlib.Path("example/centos") / ref_yaml_path.name
    manifest_json = tmp_path / "manifest.json"
    run(["compile",
         "-o", os.fspath(manifest_json),
         os.fspath(src_yaml),
         ])
    with manifest_json.open() as fp:
        manifest = json.load(fp)
    # XXX: filter rpm/curl stage before comparing

    assert manifest == ref_manifest

