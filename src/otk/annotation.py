import copy
import os
import pathlib
from typing import Any, Optional, TypeVar, Generic, Union

# import yaml
# from yaml._yaml import SequenceNode, ScalarNode, MappingNode
# from yaml.resolver import BaseResolver

AnnotatedNodeT = TypeVar('AnnotatedNodeT')


class AnnotatedNode(Generic[AnnotatedNodeT]):

    # to be able to print relative paths
    _basedirs = [os.path.curdir]

    def __init__(self, value: Optional[AnnotatedNodeT] = None, annotations: Optional[dict[str, Any]] = None):
        self.value: AnnotatedNodeT = self.deep_convert(value)
        self.annotations: dict[str, Any] = annotations or {}
        # don't nest Path in Path - sometimes happens in wrapped calls
        if isinstance(self.value, AnnotatedPath) and isinstance(self, AnnotatedPath):
            # type/mypy: TBD fix typing - not sure why mypy has this false positive here
            self.squash_annotations([self.value])  # type: ignore[attr-defined]
            self.value = self.value.value  # type: ignore[attr-defined]

    def __iter__(self):
        return iter(self.value)

    def __getitem__(self, item):
        if not isinstance(self.value, (dict, list, str)):
            raise KeyError
        if isinstance(self.value, dict) and isinstance(item, int):
            return list(self.value.keys())[item]
        return self.value[item]

    def __setitem__(self, key, value):
        if not isinstance(self.value, (dict, list)):
            raise KeyError
        self.value[key] = value

    def get_annotations(self):
        return copy.deepcopy(self.annotations)

    def set_annotations(self, annotations: dict) -> None:
        self.annotations = annotations

    def __eq__(self, other):
        if isinstance(other, AnnotatedNode):
            return self.value == other.value
        return self.value == other

    def __hash__(self):
        return hash(self.value)

    @classmethod
    def get_specific_type(cls, value):
        ret = None
        if isinstance(value, AnnotatedNode):
            ret = value
        elif isinstance(value, dict):
            ret = AnnotatedDict(value)
        elif isinstance(value, list):
            ret = AnnotatedList(value)
        elif isinstance(value, str):
            ret = AnnotatedStr(value)
        elif isinstance(value, int):
            ret = AnnotatedInt(value)
        elif isinstance(value, float):
            ret = AnnotatedFloat(value)
        elif isinstance(value, bool):
            ret = AnnotatedBool(value)
        if ret is None:
            return value
        return ret

    @classmethod
    def deep_convert(cls, data: Any) -> Any:
        """Recursively convert nested dicts and lists into AnnotatedDict and HiddenAttrList."""
        if isinstance(data, AnnotatedNode):
            return data
        if isinstance(data, dict):
            return {key: cls.get_specific_type(value) for key, value in data.items()}
        if isinstance(data, list):
            return [cls.get_specific_type(item) for item in data]

        return data

    def deep_dump(self) -> Any:
        if isinstance(self.value, dict):
            return {key: value.deep_dump() for key, value in self.value.items() if not value is None}
        if isinstance(self.value, list):
            return [item.deep_dump() for item in self.value]

        return self.value

    def __str__(self):
        return str(self.deep_dump())

    def normalize_path(self, path: pathlib.Path) -> pathlib.Path:
        filename = path
        if isinstance(self._basedirs, list):
            for d in self._basedirs:
                filename = pathlib.Path(os.path.relpath(filename, d))
        else:
            filename = os.path.relpath(filename, self._basedirs)
        return filename

    def add_source_attributes(self, key_data, prefix=""):
        line_number = key_data.start_mark.line + 1
        line_number_end = key_data.end_mark.line + 1
        column = key_data.start_mark.column + 1
        column_end = key_data.end_mark.column + 1
        filename = self.normalize_path(key_data.start_mark.name)
        self.annotations[f"{prefix}src"] = f"{filename}:{line_number}"
        self.annotations[f"{prefix}filename"] = filename
        self.annotations[f"{prefix}line_number"] = line_number
        self.annotations[f"{prefix}line_number_end"] = line_number_end
        self.annotations[f"{prefix}column"] = column
        self.annotations[f"{prefix}column_end"] = column_end

    def squash_annotations(self, annotation_list: list) -> None:
        """ just aggregates all annotations in the list.

        new annotation keys get appended to the resulting dict

        duplicate annotations will get converted to string
        (if you need an exception for a key please implement here)

        for "src" there is an exception
        this is expected to be in the form "filename:line_number"
        and will be sanely unified
        """
        ret: dict[str, Any] = {}
        files: dict[str, str] = {}
        for item in [self.annotations] + annotation_list:
            if not isinstance(item, AnnotatedNode):
                continue
            for k in item.annotations.keys():
                if k == "src":
                    src = item.annotations[k].split(":")
                    if src[0] in files:
                        if files[src[0]] != src[1]:
                            files[src[0]] += ", " + src[1]
                    else:
                        files[src[0]] = src[1]
                else:
                    if k in ret:
                        if ret[k] != item.annotations[k]:
                            ret[k] = str(ret[k]) + ", " + str(item.annotations[k])
                    else:
                        ret[k] = item.annotations[k]

        src_ret = "\n".join([f"* {k}:{v}" for k, v in files.items()])
        if len(src_ret) > 0:
            ret["src"] = src_ret

        self.annotations = ret


# for isinstance() we need actual classes
class AnnotatedList(AnnotatedNode[list]):
    pass


class AnnotatedDict(AnnotatedNode[dict]):
    def __init__(self, value: Optional[dict] = None, annotations: Optional[dict[str, Any]] = None):
        super().__init__(value, annotations)
        # default to an empty dictionary on None
        if value is None:
            self.value = {}


class AnnotatedStr(AnnotatedNode[str]):
    pass


class AnnotatedInt(AnnotatedNode[int]):
    pass


class AnnotatedFloat(AnnotatedNode[float]):
    pass


class AnnotatedBool(AnnotatedNode[bool]):
    pass


class AnnotatedPath(AnnotatedNode[pathlib.Path]):
    def __init__(self, value: Optional[Union[pathlib.Path, str]] = None, annotations: Optional[dict[str, Any]] = None):
        if isinstance(value, str):
            value = pathlib.Path(value)
        super().__init__(value, annotations)
        if not isinstance(self.value, pathlib.Path):
            self.value = pathlib.Path(str(self.value))

    def fspath_with_include(self) -> str:
        src = None
        file_name = self.normalize_path(self.value)
        src = self.annotations.get("src")
        if src is not None:
            return f"{file_name} (included from {src})"
        return str(file_name)


# class AnnotatedDumper(yaml.Dumper):
#     verbose = True
#
#     def represent_data(self, data):
#         if isinstance(data, Annotated):
#             sequence = []
#             if isinstance(data.value, dict):
#                 if data.annotations and self.verbose:
#                     sequence.append(self.represent_data(f"### {data.annotations}"))
#                 for key, value in data.value.items():
#                     if (isinstance(value, Annotated)
#                             and not isinstance(value.value, (dict, list))
#                             and value.annotations):
#                         sequence.append(self.represent_data(f"### {key}: {value.annotations}"))
#                     sequence.append(self.represent_data({key: value}))
#             elif isinstance(data.value, list):
#                 if data.annotations and self.verbose:
#                     sequence.append(self.represent_data(f"### {data.annotations}"))
#                 for i, entry in enumerate(data.value):
#                     if (isinstance(entry, Annotated)
#                             and not isinstance(entry.value, (dict, list))
#                             and entry.annotations):
#                         sequence.append(self.represent_data(f"### [{i}] {entry.annotations}"))
#                     sequence.append(self.represent_data(entry))
#             else:
#                 return self.represent_data(data.value)
#             return SequenceNode(tag=BaseResolver.DEFAULT_SEQUENCE_TAG,value=sequence)
#
#         elif isinstance(data, dict):
#             ret_list = []
#             for key, value in data.items():
#                 ret_list.append(
#                     (ScalarNode(tag=BaseResolver.DEFAULT_SCALAR_TAG, value=key),
#                      self.represent_data(value)
#                      )
#                 )
#             return MappingNode(tag=BaseResolver.DEFAULT_MAPPING_TAG, value=ret_list)
#
#         elif isinstance(data, list):
#             ret = SequenceNode(tag=BaseResolver.DEFAULT_SEQUENCE_TAG, value=[self.represent_data(v) for v in data])
#         else:
#             ret = ScalarNode(tag=BaseResolver.DEFAULT_SCALAR_TAG, value=str(data))
#         return ret
