import argparse
import json
import pathlib
import textwrap

import pytest

import otk
from otk import command


@pytest.mark.parametrize("src_yaml", (pathlib.Path(__file__).parent / "data/base").glob("*.yaml"))
def test_command_compile_on_base_examples(tmp_path, src_yaml):
    dst = tmp_path / "out.json"

    ns = argparse.Namespace(input=src_yaml, output=dst, target="osbuild")
    command.compile(ns)

    expected = json.load(src_yaml.with_suffix(".json").open())
    actual = json.load(dst.open())
    assert expected == actual


# XXX: switch to parameterized test
def test_error_from_include(tmp_path):
    base_yaml = tmp_path / "base.yaml"
    base_yaml.write_text(textwrap.dedent("""
    otk.version: 1
    otk.target.foo.bar:
      otk.include: "subdir/bad.yaml"
    """))
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir/bad.yaml").write_text("otk.op.does-not-exist:")
    
    ns = argparse.Namespace(input=base_yaml, output=None, target="osbuild")
    with pytest.raises(otk.error.TransformDirectiveUnknownError) as exc:
        command.compile(ns)
    assert f"nonexistent op 'otk.op.does-not-exist' in {tmp_path}/subdir/bad.yaml" == str(exc.value)


def test_error_from_include_after(tmp_path):
    base_yaml = tmp_path / "base.yaml"
    base_yaml.write_text(textwrap.dedent("""
    otk.version: 1
    otk.target.foo.bar:
      otk.include: "subdir/good.yaml"
    otk.target.foo.bar:
      otk.op.does-not-exist:
    """))
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir/good.yaml").write_text("foo: bar")
    
    ns = argparse.Namespace(input=base_yaml, output=None, target="osbuild")
    with pytest.raises(otk.error.TransformDirectiveUnknownError) as exc:
        command.compile(ns)
    assert f"nonexistent op 'otk.op.does-not-exist' in {tmp_path}/base.yaml" == str(exc.value)
