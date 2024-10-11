import json
import os
import pathlib
import textwrap
import yaml

import pytest

from otk.command import run

TEST_DATA_PATH = pathlib.Path(__file__).parent / "data"
TEST_EXAMPLE_PATH = pathlib.Path(__file__).parent.parent / "example"
OTK_EXTERNAL_PATH = pathlib.Path(__file__).parent.parent / "external"


class _TestCase:
    def __init__(self, base, ref_yaml_path):
        self.ref_yaml_path = ref_yaml_path
        rel = self.ref_yaml_path.relative_to(base)
        # dir structure is <distro_name>/<disro_ver>/<arch>/<type>/<customizations>
        self.distro_name, self.distro_ver, self.arch, self.img_type, self.customizations, _ = rel.as_posix().split("/")

    def as_example_yaml(self):
        # keep in sync with our "example" folder
        return (f"{TEST_EXAMPLE_PATH}/{self.distro_name}/"
                f"{self.distro_name}-{self.distro_ver}-{self.arch}-{self.img_type}.yaml")

    def __str__(self):
        return f"{self.distro_name}-{self.distro_ver}-{self.arch}-{self.img_type}-{self.customizations}"


def reference_manifests(customizations: str) -> list:
    tc = []
    base = TEST_DATA_PATH / "images-ref"
    for path in base.glob(f"*/*/*/*/{customizations}/*.yaml"):
        tc.append(_TestCase(base, path))
    return tc


def normalize_rpm_refs(manifest):
    """Normalize the rpm references, i.e. sort and remove duplicationed
    hashes.
    """
    for pipeline in manifest["pipelines"]:
        for stage in pipeline["stages"]:
            if stage["type"] == "org.osbuild.rpm":
                # sort file hashes/remove duplicated hashes ("images will
                # write duplicated hashes if a package appears multiple
                # times in it's inputs)
                ids = set(x["id"]
                          for x in stage["inputs"]["packages"]["references"])
                refs = sorted([{"id": i}
                               for i in ids], key=lambda x: x["id"])
                stage["inputs"]["packages"]["references"] = refs


def test_normalize_rpm_refs():
    fake_manifest = {
        "pipelines": [
            {
                "name": "foo",
                "stages": [
                    {
                        "type": "org.osbuild.rpm",
                        "inputs": {
                            "packages": {
                                "references": [
                                    {"id": "sha256:222"},
                                    {"id": "sha256:222"},
                                    {"id": "sha256:111"},
                                ]
                            }
                        }
                    }
                ]
            }
        ]
    }
    normalize_rpm_refs(fake_manifest)
    assert fake_manifest["pipelines"][0]["stages"][0]["inputs"]["packages"]["references"] == [
        {"id": "sha256:111"}, {"id": "sha256:222"}]


@pytest.mark.parametrize("tc", reference_manifests("empty"))
def test_images_ref_no_customizations(tmp_path, monkeypatch, tc):
    monkeypatch.setenv("OSBUILD_TESTING_RNG_SEED", "0")
    monkeypatch.setenv("OTK_EXTERNAL_PATH", str(OTK_EXTERNAL_PATH))
    monkeypatch.setenv("OTK_UNDER_TEST", "1")

    with tc.ref_yaml_path.open() as fp:
        ref_manifest = yaml.safe_load(fp)
        normalize_rpm_refs(ref_manifest)

    otk_json = tmp_path / "manifest-otk.json"
    run(["compile",
         "-o", os.fspath(otk_json),
         os.fspath(tc.as_example_yaml()),
         ])
    with otk_json.open() as fp:
        manifest = json.load(fp)
        normalize_rpm_refs(manifest)

    assert manifest == ref_manifest


@pytest.mark.parametrize("tc", reference_manifests("full"))
def test_images_ref_full_customizations(tmp_path, monkeypatch, tc):
    monkeypatch.setenv("OSBUILD_TESTING_RNG_SEED", "0")
    monkeypatch.setenv("OTK_EXTERNAL_PATH", "./external")
    monkeypatch.setenv("OTK_UNDER_TEST", "1")

    input_otk_path = tmp_path / "input.otk"
    # keep in sync with "gen-images-ref"
    with input_otk_path.open("w") as fp:
        fp.write(textwrap.dedent(f"""
        otk.define:
          user:
           modifications:
            locale: nl_NL.UTF-8
        otk.include: {tc.as_example_yaml()}
        """))

    with tc.ref_yaml_path.open() as fp:
        ref_manifest = yaml.safe_load(fp)
        normalize_rpm_refs(ref_manifest)

    otk_json = tmp_path / "manifest-otk.json"
    run(["compile",
         "-o", os.fspath(otk_json),
         os.fspath(input_otk_path),
         ])
    with otk_json.open() as fp:
        manifest = json.load(fp)
        normalize_rpm_refs(manifest)

    assert manifest == ref_manifest
