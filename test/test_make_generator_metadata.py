import json

import otk
from otk_external_osbuild.command.make_generator_metadata import root


def test_make_inline_source(capsys):
    root()
    output = json.loads(capsys.readouterr().out)
    assert output == {
        "tree": f"otk {otk.__version__}",
    }
