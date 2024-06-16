"""Implements the directives. Directives are named transformations that can be
used in omnifests to perform actions on the tree.

In the tree directives are always (part of) a dictionary, they can return any
type back for their value. Directives cannot have sibling keys in their
dictionary. A directive with sibling keys is an error.

As an example on how this works:

```python
{
    "section": {
        "otk.include": "file.yml"
    }
}
```

Then the entire dictionary will be replaced with the returned value from the
directive (in this case `file.yml` contains `[1, 2]`):

```python
{
    "section": [1, 2]
}

If a directive is found that has sibling elements:

```python
{
    "section": "a",
    "otk.include": "file.yml",
}```

It is an error.

Directives are applied through Contexts. Certain directives might only be
allowed inside (some) subtrees.
```"""

# Enables postponed annotations on older snakes (PEP-563)
from __future__ import annotations

import itertools
import logging
import pathlib
import re
from typing import Any, List

import yaml

from . import tree
from .constant import PREFIX
from .context import Context
from .error import IncludeError, TransformDirectiveTypeError, TransformDirectiveUnknownError
from .parserstate import ParserState

log = logging.getLogger(__name__)


def is_directive(needle: Any) -> bool:
    """Is a given needle a directive identifier?"""
    return isinstance(needle, str) and needle.startswith(PREFIX)


@tree.must_be(str)
def include(ctx: Context, state: ParserState, rel_path: str) -> (Any, pathlib.Path):
    """Include a separate file."""

    tree = desugar(ctx, state, rel_path)

    file = state.path.parent / pathlib.Path(rel_path)

    # TODO str'ed for json log, lets add a serializer for posixpath
    # TODO instead
    log.info("otk.include=%s", str(file))

    # TODO
    content = file.read_text()
    try:
        return yaml.safe_load(content), file
    except Exception as exc:
        raise IncludeError(f"cannot include {file}") from exc


def op(ctx: Context, state: ParserState, tree: Any, key: str) -> Any:
    """Dispatch the various `otk.op` directives while handling unknown
    operations."""

    if key == "otk.op.join":
        return op_join(ctx, state, tree)
    else:
        raise TransformDirectiveUnknownError("nonexistent op %r in %s" % (key, state.path))


@tree.must_be(dict)
@tree.must_pass(tree.has_keys(["values"]))
def op_join(ctx: Context, state: ParserState, tree: dict[str, Any]) -> Any:
    """Join a map/seq."""

    values = tree["values"]
    if not isinstance(values, list):
        raise TransformDirectiveTypeError(
            "seq join received values of the wrong type, was expecting a list of lists but got %r in %s" %
            (values,
             state.path),
        )
    if all(isinstance(sl, list) for sl in values):
        return _op_seq_join(ctx, state, values)
    elif all(isinstance(sl, dict) for sl in values):
        return _op_map_join(ctx, state, values)
    else:
        raise TransformDirectiveTypeError(f"cannot join {values} in {state.path}")


def _op_seq_join(ctx: Context, state: ParserState, values: List[list]) -> Any:
    """Join to sequences by concatenating them together."""

    if not all(isinstance(sl, list) for sl in values):
        raise TransformDirectiveTypeError(
            "seq join received values of the wrong type, was expecting a list of lists but got %r in %s" % (
                values,
                state.path,
            )
        )

    return list(itertools.chain.from_iterable(values))


def _op_map_join(ctx: Context, state: ParserState, values: List[dict]) -> Any:
    """Join two dictionaries. Keys from the second dictionary overwrite keys
    in the first dictionary."""

    if not all(isinstance(sl, dict) for sl in values):
        raise TransformDirectiveTypeError(
            "map join received values of the wrong type, was expecting a list of dicts but got %r in %s" % (
                values,
                state.path,
            )
        )

    result = {}

    for value in values:
        result.update(value)

    return result


@tree.must_be(str)
def desugar(ctx: Context, state: ParserState, tree: str) -> Any:
    """Desugar a string. If the string consists of a single `${name}` value
    then we return the object it refers to by looking up its name in the
    variables.

    If the string has anything around a variable such as `foo${name}-${bar}`
    then we replace the values inside the string. This requires the type of
    the variable to be replaced to be either str, int, or float."""

    bracket = r"\$\{%s\}"
    pattern = bracket % r"(?P<name>[a-zA-Z0-9-_\.]+)"

    # If there is a single match and its span is the entire haystack then we
    # return its value directly.
    if match := re.fullmatch(pattern, tree):
        return ctx.variable(match.group("name"))

    # Let's find all matches if there are any. We use `list(re.finditer(...))`
    # to get a list of match objects instead of `re.findall` which gives a list
    # of matchgroups.

    # If there are multiple matches then we always interpolate strings.
    if matches := list(re.finditer(pattern, tree)):
        for match in matches:
            name = match.group("name")
            data = ctx.variable(name)

            # We now how to turn ints and floats into str's
            if isinstance(data, (int, float)):
                data = str(data)

            # Any other type we do not
            if not isinstance(data, str):
                raise TransformDirectiveTypeError(
                    "string sugar resolves to an incorrect type, expected int, float, or str but got %r in %s" % (
                        data,
                        state.path,
                    )
                )

            # Replace all occurences of this name in the str

            # NOTE: this means we can recursively replace names, do we want
            # that?
            tree = re.sub(bracket % re.escape(name), data, tree)

        log.debug("desugaring %r as substring to %r", name, tree)

        return tree

    return tree
