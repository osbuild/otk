import json
import os
import pathlib
import yaml

import pytest

from otk.command import run


def test_images_ref(tmp_path):
    os.environ["OSBUILD_TESTING_RNG_SEED"] = "0"

    # XXX: use pytest.parameterize and load all ref images automatically
    # and compare
    ref_yaml = pathlib.Path("test/data/images-ref/centos-9-x86_64-qcow2.ref.yaml")
    with ref_yaml.open() as fp:
        ref_manifest = yaml.safe_load(fp)
        
    manifest_json = tmp_path / "manifest.json"
    run(["compile",
         "-o", os.fspath(manifest_json),
         "example/centos/centos-9-x86_64-qcow2.yaml"])
    with manifest_json.open() as fp:
        manifest = json.load(fp)
    # XXX: filter rpm/curl stage before comparing

    assert manifest == ref_manifest

