import json
import os
import pathlib
import yaml

import pytest

from otk.command import run

TEST_DATA_PATH = pathlib.Path(__file__).parent / "data"


class _TestCase:
    def __init__(self, base, ref_yaml_path):
        self.ref_yaml_path = ref_yaml_path
        rel = self.ref_yaml_path.relative_to(base)
        # dir structure is <distro_name>/<disro_ver>/<arch>/<type>
        self.distro_name, self.distro_ver, self.arch, self.img_type, _ = rel.as_posix().split("/")

    def as_example_yaml(self):
        # keep in sync with our "example" folder
        return f"example/{self.distro_name}/{self}.yaml"

    def __str__(self):
        return f"{self.distro_name}-{self.distro_ver}-{self.arch}-{self.img_type}"


def reference_manifests():
    tc = []
    base = TEST_DATA_PATH / "images-ref"
    for path in base.glob("*/*/*/*/*.yaml"):
        tc.append(_TestCase(base, path))
    return tc


@pytest.mark.parametrize("tc", reference_manifests())
def test_images_ref(tmp_path, monkeypatch, tc):
    monkeypatch.setenv("OSBUILD_TESTING_RNG_SEED", "0")
    monkeypatch.setenv("OTK_EXTERNAL_PATH", "./external")

    with tc.ref_yaml_path.open() as fp:
        ref_manifest = yaml.safe_load(fp)

    otk_json = tmp_path / "manifest-otk.json"
    run(["compile",
         "-o", os.fspath(otk_json),
         tc.as_example_yaml(),
         ])
    with otk_json.open() as fp:
        manifest = json.load(fp)

    assert manifest == ref_manifest
