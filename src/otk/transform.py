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
from .annotation import AnnotatedDict, AnnotatedList, AnnotatedPath, AnnotatedNode, AnnotatedStr, AnnotatedInt, \
    AnnotatedFloat, AnnotatedBool

log = logging.getLogger(__name__)


# from https://gist.github.com/pypt/94d747fe5180851196eb?permalink_comment_id=4653474#gistcomment-4653474
# pylint: disable=too-many-ancestors
class SafeUniqueKeyLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        mapping = set()
        for key_node, _ in node.value:
            if ':merge' in key_node.tag:
                continue
            if isinstance(key_node, AnnotatedNode):
                key = self.construct_object(key_node.value, deep=deep)
            else:
                key = self.construct_object(key_node, deep=deep)
            if key in mapping:
                if "otk." in key.value:
                    raise ParseDuplicatedYamlKeyError(
                        f"duplicated '{key}' key found, try using "
                        f"{key}.<uniq-tag>, e.g. {key}.foo")
                raise ParseDuplicatedYamlKeyError(f"duplicated '{key}' key found")
            mapping.add(key.value)
        super_map = super().construct_mapping(node, deep)

        # keys should be strings in this case (without annotations)
        super_map = {key.value: v for key, v in super_map.items()}

        return super_map


def _find_data(node_list, key):
    """ Helper function to find the yaml ScalarNode containing
    our context information for HiddenAttrList and AnnotatedDict
    """
    for node in node_list:
        if node[0].value == key:
            return node[0]
    raise KeyError(key)


def annotated_dict_constructor(loader, node):
    data = loader.construct_mapping(node, deep=True)
    annotated_data_dict = AnnotatedDict(data)

    # content_ really are the lines of the content, not the tag.
    annotated_data_dict.add_source_attributes(node, prefix="content_")

    # src will be overwritten if this gets a child node
    annotated_data_dict.add_source_attributes(node)
    for key, _ in annotated_data_dict.value.items():
        key_data = _find_data(node.value, key)
        if annotated_data_dict.value[key]:
            annotated_data_dict.value[key].add_source_attributes(key_data)
    return annotated_data_dict


def annotated_list_constructor(loader, node):
    data = loader.construct_sequence(node, deep=True)
    annotated_data_list = AnnotatedList(data)
    # content_ really are the lines of the content, not the tag.
    annotated_data_list.add_source_attributes(node, prefix="content_")

    # src will be overwritten if this gets a child node
    annotated_data_list.add_source_attributes(node)
    for idx, _ in enumerate(node.value):
        key_data = node.value[idx]
        if annotated_data_list.value[idx]:
            annotated_data_list.value[idx].add_source_attributes(key_data)
    return annotated_data_list


def annotated_scalar_constructor(loader, node):
    data = loader.construct_scalar(node)
    annotated_data = AnnotatedNode.get_specific_type(data)
    # content_ really are the lines of the content, not the tag.
    annotated_data.add_source_attributes(node, prefix="content_")

    # src will be overwritten if this gets a child node
    annotated_data.add_source_attributes(node)
    return annotated_data


def resolve(ctx: Context, state: State, data: Any) -> Any:
    """Resolves a value of any supported type into a new value. Each type has
    its own specific handler to replace the data value."""

    if isinstance(data, AnnotatedDict):
        return resolve_dict(ctx, state, data)
    if isinstance(data, AnnotatedList):
        return resolve_list(ctx, state, data)
    if isinstance(data, AnnotatedStr):
        newstr = resolve_str(ctx, state, data)
        return newstr
    if isinstance(data, (AnnotatedInt, AnnotatedFloat, AnnotatedBool)):
        return data
    if isinstance(data, (int, float, bool, type(None))):
        return AnnotatedNode.get_specific_type(data)

    raise ParseTypeError(f"could not look up {type(data)} in resolvers", state)


# XXX: look into this
# pylint: disable=too-many-branches
def resolve_dict(ctx: Context, state: State, tree: AnnotatedDict) -> Any:
    """
    Dictionaries are iterated through and both the keys and values are processed.
    Keys define how a value is interpreted:
    - otk.include.* loads the file specified by the value.
    - otk.op.* processes the value with the named operation.
    - otk.define.* updates the defines dictionary with all the defined key-value
      pairs.
    - Values under any other key are processed based on their type (see resolve()).
    """

    for key, val in tree.value.copy().items():
        # Replace any variables in a value immediately before doing anything
        # else, so that variables defined in strings are considered in the
        # processing of all directives.
        if isinstance(val, AnnotatedStr):
            val = substitute_vars(ctx, state, val)
        if is_directive(key):
            if key.startswith(PREFIX_DEFINE):
                del tree.value[key]  # remove otk.define from the output tree
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
                if not isinstance(target, AnnotatedDict):
                    raise ParseError(
                        f"First level below a 'target' should be an AnnotatedDict "
                        f"(not a {type(target).__name__})", state, target)

                tree.value[key].value.update(target.value)
                tree.value[key].squash_annotations([target])
                continue

            if key.startswith(PREFIX_INCLUDE):
                include_src = val.get_annotations()
                del tree.value[key]  # replace "otk.include" with resolved included data

                path = AnnotatedPath(val)
                path.annotations = include_src
                included = process_include(ctx, state, path)

                if not isinstance(included, AnnotatedDict):
                    if len(tree.value) > 0:
                        raise ParseValueError(
                            f"otk.include '{val}' overrides non-empty dict {tree.deep_dump()} with '{included}'", state)
                    return included

                if isinstance(included, AnnotatedDict):
                    tree.value.update(included.value)
                    tree.squash_annotations([tree.annotations, included.annotations])
                else:
                    tree.value.update(included)

                continue

            # Other directives do *not* allow siblings
            if len(tree.value) > 1:
                keys = [f"{k} ({tree.value[k].annotations.get('src')})" for k in tree.value.keys()]
                raise ParseError(f"directive {key} should not have siblings: {keys!r}", state, tree.value[key])

            if key.startswith(PREFIX_OP):
                # return is fine, no siblings allowed
                return resolve(ctx, state, op(ctx, state, resolve(ctx, state, val), key))

            if key.startswith("otk.external."):
                # no target, "dry" run
                if not ctx.target_requested:
                    continue
                # return is fine, no siblings allowed
                return resolve(ctx, state, call(state, key, resolve(ctx, state, val)))

        newval = resolve(ctx, state, val)
        tree.value[key] = newval
    return tree


def resolve_list(ctx: Context, state: State, tree: AnnotatedList) -> AnnotatedList:
    """Resolving a list means applying the resolve function to each element in
    the list."""

    log.debug("resolving list %r", tree)
    new_state = AnnotatedList([resolve(ctx, state, val) for val in tree])

    # list comprehension need a separate copy of all annotations
    new_state.annotations = tree.get_annotations()

    return new_state


def resolve_str(ctx: Context, state: State, tree: AnnotatedStr) -> AnnotatedStr:
    """Resolving strings means they are parsed for any variable
    interpolation."""

    log.debug("resolving str %r", tree)
    substr = substitute_vars(ctx, state, tree)
    return substr


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
        ctx.define(state.define_subkey(), AnnotatedDict())
        return

    # Iterate over a copy of the tree so that we can modify it in-place.
    for key, value in tree.value.copy().items():
        if key.startswith("otk.define"):
            # nested otk.define: process the nested values directly
            process_defines(ctx, state, value)
            continue

        if key.startswith("otk.include"):
            raise ParseError(f"otk.include not allowed in an otk.define in {state.path}", state)

        if key.startswith("otk.op"):
            del tree.value[key]
            value = op(ctx, state, value, key)
            ctx.define(state.define_subkey(), value)
            continue

        if key.startswith("otk.external."):
            new_vars = resolve(ctx, state, call(state, key, resolve(ctx, state, value)))
            ctx.merge_defines(state.define_subkey(), new_vars)
            continue

        if isinstance(value, AnnotatedDict):
            new_state = state.copy(subkey_add=key)
            process_defines(ctx, new_state, value)

        elif isinstance(value, AnnotatedStr):
            # value is a string: run it through substitute_vars() to resolve any variables and set the define
            ctx.define(state.define_subkey(key), substitute_vars(ctx, state, value))
        else:
            # for any other type, just set the value to the key
            ctx.define(state.define_subkey(key), value)


overridden_constructors = [
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    yaml.resolver.BaseResolver.DEFAULT_SEQUENCE_TAG,
    yaml.resolver.BaseResolver.DEFAULT_SCALAR_TAG
]


def save_yaml_constructors():
    """ Mainly for testcases, save our constructors not to
        pollute other yaml imports
    """
    return {k: yaml.SafeLoader.yaml_constructors[k] for k in overridden_constructors}


def restore_yaml_constructors(data):
    """ Mainly for testcases, remove our constructors not to
        pollute other yaml imports
    """
    for k, v in data.items():
        yaml.SafeLoader.yaml_constructors[k] = v


def process_include(ctx: Context, state: State, path: AnnotatedPath) -> AnnotatedDict:
    """
    Load a yaml file and send it to resolve() for processing.
    """
    # resolve 'path' relative to 'state.path'
    if not path.value.is_absolute():
        cur_path = state.path.value.parent
        try:
            origin = path.get_annotations()
        except KeyError:
            origin = None
        path = AnnotatedPath((cur_path / pathlib.Path(str(path))).resolve())
        if origin:
            path.set_annotations(origin)
    log.info("resolving %s", path)

    # callbacks to store information about the source of all data in the yaml files
    saved_constructors = save_yaml_constructors()
    yaml.SafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, annotated_dict_constructor)
    yaml.SafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_SEQUENCE_TAG, annotated_list_constructor)
    yaml.SafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_SCALAR_TAG, annotated_scalar_constructor)

    try:
        with path.value.open(encoding="utf8") as fp:
            data = yaml.load(fp, Loader=SafeUniqueKeyLoader)
    except FileNotFoundError as fnfe:
        prefix = pathlib.Path(os.path.commonprefix([path.value, state.path.value]))
        if not prefix.is_dir():
            prefix_str = str(prefix.parent) + "/"
        else:
            prefix_str = str(prefix) + "/"
        cleaned_path = os.fspath(path.value).removeprefix(prefix_str)
        restore_yaml_constructors(saved_constructors)
        raise IncludeNotFoundError(f"file '{cleaned_path}' was not found", state, path) from fnfe
    except ParseDuplicatedYamlKeyError as err:
        restore_yaml_constructors(saved_constructors)
        raise ParseDuplicatedYamlKeyError(f"{err}", state.copy(path=path)) from err

    restore_yaml_constructors(saved_constructors)

    if data is not None:
        return resolve(ctx, state.copy(path=path), data)
    return AnnotatedDict()


def op(ctx: Context, state: State, tree: Any, key: str) -> Any:
    """Dispatch the various `otk.op` directives while handling unknown
    operations."""
    if key == "otk.op.join":
        return op_join(ctx, state, tree)
    raise TransformDirectiveUnknownError(f"nonexistent op {key!r}", state)


@tree.must_be(AnnotatedDict)
@tree.must_pass(tree.has_keys(["values"]))
def op_join(_: Context, state: State, tree: AnnotatedDict) -> Any:
    """Join a map/seq."""

    values = tree["values"]
    if not isinstance(values, AnnotatedList):
        raise TransformDirectiveTypeError(
            f"seq join received values of the wrong type, was expecting a list of lists but got {values!r}", state)

    if all(isinstance(sl, AnnotatedList) for sl in values):
        ret: AnnotatedList = AnnotatedList([v.value for v in list(itertools.chain.from_iterable(values.value))])
        ret.squash_annotations(list(values.value))
        return ret

    if all(isinstance(sl, AnnotatedDict) for sl in values):
        result: AnnotatedDict = AnnotatedDict()
        for value in values:
            result.value.update(value.value)
            result.squash_annotations([value.annotations])
        return result
    raise TransformDirectiveTypeError(f"cannot join {values}", state)


@tree.must_be(AnnotatedStr)
def substitute_vars(ctx: Context, state: State, data: AnnotatedStr) -> AnnotatedStr:
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
    if m := re.fullmatch(pattern, data.value):
        validate_var_name(m.group("name"))
        try:
            var = ctx.variable(m.group("name"))
        except OTKError as exc:
            raise exc.__class__(str(exc), state)
        return var

    if matches := re.finditer(pattern, data.value):
        for m in matches:
            name = m.group("name")
            validate_var_name(m.group("name"))

            value = ctx.variable(name)
            # We know how to turn ints and floats into str's
            if isinstance(value, (AnnotatedInt, AnnotatedFloat)):
                # TBD find out why the __str__() implementation of AnnotatedInt doesn't work
                # so "origin" is not necessary
                origin = value.get_annotations()
                value = AnnotatedStr(str(value.value))
                value.set_annotations(origin)

            # Any other type we do not
            if not isinstance(value, AnnotatedStr):
                raise TransformDirectiveTypeError(
                    f"expected int, float, or str. Can not use {type(value.value).__name__} "
                    f"to resolve string {data.value!r} ({data.annotations['src']})", state, value)

            # Replace all occurences of this name in the str
            data_origin = None
            if "src" in value.annotations and "src" in data.annotations:
                data_origin = f"variable from {value.annotations['src']} applied to {data.annotations['src']}"

            data = AnnotatedStr(re.sub(bracket % re.escape(name), value.value, data.value))
            if data_origin:
                data.annotations["src"] = data_origin
            log.debug("substituting %r as substring to %r", name, data.value)

    return data
