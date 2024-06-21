import argparse
import json
import pathlib

import pytest
from otk import command


@pytest.mark.parametrize("src_yaml",
                         [str(path) for path in (pathlib.Path(__file__).parent / "data/base").glob("*.yaml")])
def test_command_compile_on_base_examples(tmp_path, src_yaml):
    src_yaml = pathlib.Path(src_yaml)
    dst = tmp_path / "out.json"

    ns = argparse.Namespace(input=src_yaml, output=dst, target="osbuild")

    command.compile(ns)

    expected = json.load(src_yaml.with_suffix(".json").open())
    actual = json.load(dst.open())
    assert expected == actual
