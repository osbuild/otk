"""To transform trees `otk` recursively modifies them. Trees are visited depth
first from left-to-right (top-to-bottom in omnifests).

Each type we can encounter in the tree has its own resolver. For many types
this would be the `dont_resolve`-resolver which leaves the value as is. For
collection types we want to recursively resolve the elements of the collection.

In the dictionary case we apply our directives. Directives are based on the
keys in the dictionaries."""

# Enables postponed annotations on older snakes (PEP-563)
from __future__ import annotations

import itertools
import logging
import os.path
import pathlib
import re
from typing import Any

import yaml

from . import tree
from .constant import NAME_VERSION, PREFIX, PREFIX_DEFINE, PREFIX_INCLUDE, PREFIX_OP, PREFIX_TARGET
from .context import Context, validate_var_name
from .error import (
    IncludeNotFoundError, OTKError,
    ParseError, ParseTypeError, ParseValueError, ParseDuplicatedYamlKeyError,
    TransformDirectiveTypeError, TransformDirectiveUnknownError,
)
from .external import call
from .traversal import State
from .utils import HiddenAttrDict, HiddenAttrList

log = logging.getLogger(__name__)


# from https://gist.github.com/pypt/94d747fe5180851196eb?permalink_comment_id=4653474#gistcomment-4653474
# pylint: disable=too-many-ancestors
class SafeUniqueKeyLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        mapping = set()
        for key_node, _ in node.value:
            if ':merge' in key_node.tag:
                continue
            key = self.construct_object(key_node, deep=deep)
            if key in mapping:
                if "otk." in key:
                    raise ParseDuplicatedYamlKeyError(
                        f"duplicated {key!r} key found, try using "
                        f"{key}.<uniq-tag>, e.g. {key}.foo")
                raise ParseDuplicatedYamlKeyError(f"duplicated {key!r} key found")
            mapping.add(key)
        return super().construct_mapping(node, deep)


def _find_data(node_list, key):
    """ Helper function to find the yaml ScalarNode containing
    our context information for HiddenAttrList and HiddenAttrDict
    """
    for node in node_list:
        if node[0].value == key:
            return node[0]
    raise KeyError(key)


def _add_hidden_attributes(obj, key, key_data):
    line_number = key_data.start_mark.line + 1
    column = key_data.start_mark.column + 1
    filename = os.path.relpath(key_data.start_mark.name, os.path.curdir)
    obj.set_attribute(key, "src", f"{filename}:{line_number}")
    obj.set_attribute(key, "filename", filename)
    obj.set_attribute(key, "linenumber", line_number)
    obj.set_attribute(key, "column", column)


def hidden_attr_dict_constructor(loader, node):
    data = loader.construct_mapping(node, deep=True)
    hidden_data_node = HiddenAttrDict(data)
    for key, _ in hidden_data_node.items():
        key_data = _find_data(node.value, key)
        _add_hidden_attributes(hidden_data_node, key, key_data)
    return hidden_data_node


def hidden_attr_list_constructor(loader, node):
    data = loader.construct_sequence(node, deep=True)
    hidden_data_node = HiddenAttrList(data)
    _add_hidden_attributes(hidden_data_node, "self", node)
    return hidden_data_node


def resolve(ctx: Context, state: State, data: Any) -> Any:
    """Resolves a value of any supported type into a new value. Each type has
    its own specific handler to replace the data value."""

    if isinstance(data, dict):
        return resolve_dict(ctx, state, data)
    if isinstance(data, list):
        return resolve_list(ctx, state, data)
    if isinstance(data, str):
        return resolve_str(ctx, state, data)
    if isinstance(data, (int, float, bool, type(None))):
        return data

    raise ParseTypeError(f"could not look up {type(data)} in resolvers", state)


# XXX: look into this
# pylint: disable=too-many-branches
def resolve_dict(ctx: Context, state: State, tree: dict[str, Any]) -> Any:
    """
    Dictionaries are iterated through and both the keys and values are processed.
    Keys define how a value is interpreted:
    - otk.include.* loads the file specified by the value.
    - otk.op.* processes the value with the named operation.
    - otk.define.* updates the defines dictionary with all the defined key-value
      pairs.
    - Values under any other key are processed based on their type (see resolve()).
    """

    for key, val in tree.copy().items():
        # Replace any variables in a value immediately before doing anything
        # else, so that variables defined in strings are considered in the
        # processing of all directives.
        if isinstance(val, str):
            val = substitute_vars(ctx, state, val)
        if is_directive(key):
            if key.startswith(PREFIX_DEFINE):
                del tree[key]  # remove otk.define from the output tree
                process_defines(ctx, state, val)
                continue

            if key == NAME_VERSION:
                continue

            if key.startswith(PREFIX_TARGET):
                # no target, "dry" run
                if not ctx.target_requested:
                    continue
                # wrong target
                if not key.startswith(PREFIX_TARGET + ctx.target_requested):
                    continue
                target = resolve(ctx, state, val)
                if not isinstance(target, dict):
                    raise ParseError(
                        f"First level below a 'target' should be a dictionary (not a {type(target).__name__})", state)

                tree.update(target)
                continue

            if key.startswith(PREFIX_INCLUDE):
                del tree[key]  # replace "otk.include" with resolved included data

                included = process_include(ctx, state, pathlib.Path(val))
                if not isinstance(included, dict):
                    if len(tree) > 0:
                        raise ParseValueError(
                            f"otk.include '{val}' overrides non-empty dict {tree} with '{included}'", state)
                    return included

                tree.update(included)
                continue

            # Other directives do *not* allow siblings
            if len(tree) > 1:
                keys = list(tree.keys())
                raise ParseError(f"directive {key} should not have siblings: {keys!r}", state)

            if key.startswith(PREFIX_OP):
                # return is fine, no siblings allowed
                return resolve(ctx, state, op(ctx, state, resolve(ctx, state, val), key))

            if key.startswith("otk.external."):
                # no target, "dry" run
                if not ctx.target_requested:
                    continue
                # return is fine, no siblings allowed
                return resolve(ctx, state, call(state, key, resolve(ctx, state, val)))

        tree[key] = resolve(ctx, state, val)
    return tree


def resolve_list(ctx: Context, state: State, tree: list[Any]) -> list[Any]:
    """Resolving a list means applying the resolve function to each element in
    the list."""

    log.debug("resolving list %r", tree)

    return [resolve(ctx, state, val) for val in tree]


def resolve_str(ctx: Context, state: State, tree: str) -> Any:
    """Resolving strings means they are parsed for any variable
    interpolation."""

    log.debug("resolving str %r", tree)

    return substitute_vars(ctx, state, tree)


def is_directive(needle: Any) -> bool:
    """Is a given needle a directive identifier?"""
    return isinstance(needle, str) and needle.startswith(PREFIX)


def process_defines(ctx: Context, state: State, tree: Any) -> None:
    """
    Processes tree for new defines, resolving any references to other variables,
    and update the global context. The State holds a reference to the nested
    defines block the function is working in. New defines are added to the
    nested block but references are resolved from the global ctx.defines.
    """
    if tree is None:
        log.warning("empty otk.define in %s", state.path)
        return
    if tree == {}:
        ctx.define(state.define_subkey(), {})
        return

    # Iterate over a copy of the tree so that we can modify it in-place.
    for key, value in tree.copy().items():
        if key.startswith("otk.define"):
            # nested otk.define: process the nested values directly
            process_defines(ctx, state, value)
            continue

        if key.startswith("otk.include"):
            raise ParseError(f"otk.include not allowed in an otk.define in {state.path}", state)

        if key.startswith("otk.op"):
            del tree[key]
            value = op(ctx, state, value, key)
            ctx.define(state.define_subkey(), value)
            continue

        if key.startswith("otk.external."):
            new_vars = resolve(ctx, state, call(state, key, resolve(ctx, state, value)))
            ctx.merge_defines(state.define_subkey(), new_vars)
            continue

        if isinstance(value, dict):
            new_state = state.copy(subkey_add=key)
            process_defines(ctx, new_state, value)

        elif isinstance(value, str):
            # value is a string: run it through substitute_vars() to resolve any variables and set the define
            ctx.define(state.define_subkey(key), substitute_vars(ctx, state, value))
        else:
            # for any other type, just set the value to the key
            ctx.define(state.define_subkey(key), value)


def process_include(ctx: Context, state: State, path: pathlib.Path) -> HiddenAttrDict:
    """
    Load a yaml file and send it to resolve() for processing.
    """
    # resolve 'path' relative to 'state.path'
    if not path.is_absolute():
        cur_path = state.path.parent
        path = (cur_path / pathlib.Path(path)).resolve()
    log.info("resolving %s", path)

    # callbacks to store information about the source of all data in the yaml files
    yaml.SafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, hidden_attr_dict_constructor)
    yaml.SafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_SEQUENCE_TAG, hidden_attr_list_constructor)

    try:
        with path.open(encoding="utf8") as fp:
            data = yaml.load(fp, Loader=SafeUniqueKeyLoader)
    except FileNotFoundError as fnfe:
        cleaned_path = os.fspath(path).removeprefix(
            os.path.commonprefix([path, state.path]))
        raise IncludeNotFoundError(f"file {cleaned_path} was not found", state) from fnfe
    except ParseDuplicatedYamlKeyError as err:
        raise ParseDuplicatedYamlKeyError(f"{err}", state.copy(path=path)) from err

    if data is not None:
        return resolve(ctx, state.copy(path=path), data)
    return HiddenAttrDict()


def op(ctx: Context, state: State, tree: Any, key: str) -> Any:
    """Dispatch the various `otk.op` directives while handling unknown
    operations."""
    if key == "otk.op.join":
        return op_join(ctx, state, tree)
    raise TransformDirectiveUnknownError(f"nonexistent op {key!r}", state)


@tree.must_be(dict)
@tree.must_pass(tree.has_keys(["values"]))
def op_join(_: Context, state: State, tree: dict[str, Any]) -> Any:
    """Join a map/seq."""

    values = tree["values"]
    if not isinstance(values, list):
        raise TransformDirectiveTypeError(
            f"seq join received values of the wrong type, was expecting a list of lists but got {values!r}", state)

    if all(isinstance(sl, list) for sl in values):
        return list(itertools.chain.from_iterable(values))
    if all(isinstance(sl, dict) for sl in values):
        result = {}
        for value in values:
            result.update(value)
        return result
    raise TransformDirectiveTypeError(f"cannot join {values}", state)


@tree.must_be(str)
def substitute_vars(ctx: Context, state: State, data: str) -> Any:
    """Substitute variables in the `data` string.

    If `data` consists only of a single `${name}` value then we return the
    object that `name` refers to by looking it up in the context variables. The
    value can be of any supported type (str, int, float, dict, list).

    If `data` contains one or more variable references as substrings, such as
    `foo${name}-${bar}` the function will replace the values for each variable
    named (`name` and `bar`, in the example). In this case, the type of the
    value in the names variables must be primitive types, either str, int, or
    float."""

    bracket = r"\$\{%s\}"
    pattern = bracket % r"(?P<name>[^}]+)"
    # If there is a single match and its span is the entire haystack then we
    # return its value directly.
    if m := re.fullmatch(pattern, data):
        validate_var_name(m.group("name"))
        try:
            var = ctx.variable(m.group("name"))
        except OTKError as exc:
            raise exc.__class__(str(exc), state)
        return var

    if matches := re.finditer(pattern, data):
        for m in matches:
            name = m.group("name")
            validate_var_name(m.group("name"))

            value = ctx.variable(name)
            # We know how to turn ints and floats into str's
            if isinstance(value, (int, float)):
                value = str(value)

            # Any other type we do not
            if not isinstance(value, str):
                raise TransformDirectiveTypeError(
                    f"string {data!r} resolves to an incorrect type, "
                    f"expected int, float, or str but got {type(value).__name__}", state)

            # Replace all occurences of this name in the str
            data = re.sub(bracket % re.escape(name), value, data)
            log.debug("substituting %r as substring to %r", name, data)

    return data
