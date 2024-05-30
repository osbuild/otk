from otk.command import parser_create


def test_parse_no_command():
    p = parser_create()

    r = p.parse_args([])

    assert r.command is None
    assert r.verbose == 0
    assert not r.json
    assert r.identifier is None

    r = p.parse_args(["-j"])
    assert r.command is None
    assert r.json
    assert r.verbose == 0
    assert r.identifier is None

    r = p.parse_args(["-j", "-v"])
    assert r.command is None
    assert r.json
    assert r.verbose == 1
    assert r.identifier is None

    r = p.parse_args(["-j", "-vvvv"])
    assert r.command is None
    assert r.json
    assert r.verbose == 4
    assert r.identifier is None

    r = p.parse_args(["--json", "--verbose", "--verbose"])
    assert r.command is None
    assert r.json
    assert r.verbose == 2
    assert r.identifier is None

    r = p.parse_args(["-i", "foo"])
    assert r.command is None
    assert not r.json
    assert r.verbose == 0
    assert r.identifier == "foo"


def test_parse_compile():
    p = parser_create()

    r = p.parse_args(["compile"])
    assert r.command == "compile"
    assert r.output is None

    r = p.parse_args(["compile", "foo"])
    assert r.command == "compile"
    assert r.input == "foo"
    assert r.output is None

    r = p.parse_args(["compile", "-o", "file.yaml"])
    assert r.command == "compile"
    assert r.input is None
    assert r.output == "file.yaml"

    r = p.parse_args(["compile", "-o", "file.yaml", "foo.yaml"])
    assert r.command == "compile"
    assert r.input == "foo.yaml"
    assert r.output == "file.yaml"
