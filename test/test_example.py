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

    # pylint: disable=consider-using-with
    expected = json.load(src_yaml.with_suffix(".json").open(encoding="utf8"))
    actual = json.load(dst.open(encoding="utf8"))
    assert expected == actual


@pytest.mark.parametrize("src_yaml",
                         [str(path) for path in (pathlib.Path(__file__).parent / "data/error").glob("*.yaml")])
def test_errors(src_yaml):
    src_yaml = pathlib.Path(src_yaml)
    expected = src_yaml.with_suffix(".err").read_text(encoding="utf8").strip()
    ns = argparse.Namespace(input=src_yaml, output="/dev/null", target="osbuild")
    with pytest.raises(Exception) as exception:
        command.compile(ns)
    assert expected in str(exception.value)
