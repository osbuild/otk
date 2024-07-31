import os
import textwrap

import pytest


@pytest.fixture()
def mirror(tmp_path):
    os.environ["OTK_EXTERNAL_PATH"] = os.fspath(tmp_path)
    fake_external_path = tmp_path / "mirror"
    fake_external_path.write_text(
        textwrap.dedent("""\
    #!/usr/bin/python3
    import json,sys
    tree=json.loads(sys.stdin.read())
    print(json.dumps({"tree": tree["tree"]}))
    """)
    )
    os.chmod(fake_external_path, 0o755)

    yield tmp_path

    del os.environ["OTK_EXTERNAL_PATH"]
