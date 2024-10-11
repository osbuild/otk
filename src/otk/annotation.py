import copy
import os
import pathlib
from typing import TypeVar, Generic, Any


class AnnotatedBase:
    """ Implements a base class for annotated objects.
    The annotations are basically a dict[str, any] of properties to attach to the class.
    """

    # base directory to calculate relative paths (easier to read)
    _basedir = os.path.curdir

    def __init__(self) -> None:
        self._otk_annotations: dict[str, Any] = {}
        if isinstance(self, list):
            for idx, value in enumerate(self):
                self[idx] = self.deep_convert(value)
        elif isinstance(self, dict):
            for key, value in self.items():
                self[key] = self.deep_convert(value)

    def get_annotation(self, key: str, default: Any | None = None) -> Any | None:
        if key in self._otk_annotations:
            return self._otk_annotations[key]
        return default

    def set_annotation(self, key: str, val: Any) -> Any:
        self._otk_annotations[key] = val

    def get_annotations(self) -> dict[str, Any]:
        """Returns all annotations"""
        return self._otk_annotations

    def set_annotations(self, annotations: dict[str, Any]) -> None:
        """ set all annotations """
        self._otk_annotations = annotations

    @classmethod
    def deep_convert(cls, data: Any) -> Any:
        """Recursively convert nested dicts and lists into AnnotatedDict and HiddenAttrList."""
        ret = data
        if isinstance(data, AnnotatedBase):
            return ret
        if isinstance(data, dict):
            ret = AnnotatedDict({key: cls.deep_convert(value) for key, value in data.items()})
        elif isinstance(data, list):
            ret = AnnotatedList([cls.deep_convert(item) for item in data])
        elif isinstance(data, str):
            ret = AnnotatedStr(data)
        elif isinstance(data, bool):
            ret = AnnotatedBool(data)
        elif isinstance(data, int):
            ret = AnnotatedInt(data)
        elif isinstance(data, float):
            ret = AnnotatedFloat(data)

        # note: "complex" is not implemented as it's not used in YAML

        return ret

    @classmethod
    def deep_dump(cls, data: Any) -> Any:
        """ Converting to builtin types is usually not necessary.
            This special conversion is mainly for json.dumps(). json library needs "bool" to pass the
            condition "<var> is True" which does not apply to AnnotatedBool,
            so we'll just convert all
        """
        ret = data
        if isinstance(data, AnnotatedDict):
            ret = {key: cls.deep_dump(value) for key, value in data.items()}
        elif isinstance(data, AnnotatedList):
            ret = [cls.deep_dump(item) for item in data]
        elif isinstance(data, AnnotatedBool):
            ret = data.value
        elif isinstance(data, AnnotatedFloat):
            ret = float(data)
        elif isinstance(data, AnnotatedInt):
            ret = int(data)
        elif isinstance(data, AnnotatedStr):
            ret = str(data)

        return ret

    def add_source_attributes(self, key_data, prefix=""):
        line_number = key_data.start_mark.line + 1
        line_number_end = key_data.end_mark.line + 1
        column = key_data.start_mark.column + 1
        column_end = key_data.end_mark.column + 1
        filename = os.path.relpath(key_data.start_mark.name, self._basedir)
        self.set_annotation(f"{prefix}src", f"{filename}:{line_number}")
        self.set_annotation(f"{prefix}filename", filename)
        self.set_annotation(f"{prefix}line_number", line_number)
        self.set_annotation(f"{prefix}line_number_end", line_number_end)
        self.set_annotation(f"{prefix}column", column)
        self.set_annotation(f"{prefix}column_end", column_end)

    def __add__(self, o):
        ret = self.deep_convert(super().__add__(o))  # pylint: disable=E1101
        ret.set_annotations(self.squash_annotations([self, o]))
        return ret

    def __iadd__(self, o):
        return self.__add__(o)

    def __radd__(self, o):
        return self.deep_convert(o).__add__(self)

    def __deepcopy__(self, memo):
        if isinstance(self, AnnotatedDict):
            cls = self.__class__
            result = cls.__new__(cls)
            memo[id(self)] = result

            for k, v in self.items():
                result[k] = copy.deepcopy(v, memo)

        elif isinstance(self, AnnotatedList):
            cls = self.__class__
            result = cls.__new__(cls)
            memo[id(self)] = result

            for v in self:
                result.append(copy.deepcopy(v, memo))
        elif isinstance(self, (AnnotatedStr, AnnotatedInt, AnnotatedFloat, AnnotatedBool, AnnotatedPath)):
            result = copy.copy(self)
        else:
            result = None  # just for the linter - that should never happen

        result.set_annotations(self.get_annotations().copy())

        return result

    @classmethod
    def squash_annotations(cls, annotation_list: list) -> dict:
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
        for item in annotation_list:
            if not isinstance(item, AnnotatedBase):
                continue
            annotations = item.get_annotations()
            for k in annotations.keys():
                if k == "src":
                    src = annotations[k].split(":")
                    if src[0] in files:
                        files[src[0]] += ", " + src[1]
                    else:
                        files[src[0]] = src[1]
                else:
                    if k in ret:
                        ret[k] = str(ret[k]) + str(annotations[k])
                    else:
                        ret[k] = annotations[k]

        ret["src"] = "\n".join([f"* {k}:{v}" for k, v in files.items()])

        return ret


AnnotatedDictKeyT = TypeVar('AnnotatedDictKeyT')
AnnotatedDictVarT = TypeVar('AnnotatedDictVarT')

AnnotatedListT = TypeVar('AnnotatedListT')


class AnnotatedList(Generic[AnnotatedListT], AnnotatedBase, list):
    def __init__(self, seq: list[Any] | None = None) -> None:
        if seq is None:
            seq = []
        list.__init__(self, seq)
        AnnotatedBase.__init__(self)


class AnnotatedDict(Generic[AnnotatedDictKeyT, AnnotatedDictVarT], AnnotatedBase, dict):
    def __init__(self, seq: dict[Any, Any] | None = None, **kwargs: dict[Any, Any]) -> None:
        if seq is None:
            seq = {}
        dict.__init__(self, seq, **kwargs)
        AnnotatedBase.__init__(self)


class AnnotatedPath(AnnotatedBase, pathlib.Path):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pathlib.Path.__init__(self, *args, **kwargs)
        AnnotatedBase.__init__(self)

    def fspath_with_include(self) -> str:
        src = None
        filename = os.path.relpath(os.fspath(self), self._basedir)
        try:
            src = self.get_annotation("src")
        except KeyError:
            pass
        if src is not None:
            return f"{filename} (included from {src})"
        return filename


class AnnotatedStr(AnnotatedBase, str):
    def __init__(self, *args: str) -> None:  # pylint: disable=W0613
        str.__init__(self)
        AnnotatedBase.__init__(self)


class AnnotatedInt(AnnotatedBase, int):
    def __init__(self, *args: int) -> None:  # pylint: disable=W0613
        int.__init__(self)
        AnnotatedBase.__init__(self)

    def __str__(self):  # pylint: disable=E0307
        ret = AnnotatedStr(int.__str__(self))
        ret.set_annotations(self.get_annotations())
        return ret


class AnnotatedFloat(AnnotatedBase, float):
    def __init__(self, *args: float) -> None:  # pylint: disable=W0613
        float.__init__(self)
        AnnotatedBase.__init__(self)

    def __str__(self):  # pylint: disable=E0307
        ret = AnnotatedStr(float.__str__(self))
        ret.set_annotations(self.get_annotations())
        return ret


class AnnotatedBool(AnnotatedBase):
    """ only bool can't be "subclassed" """

    def __init__(self, value: Any) -> None:
        self.value: bool = bool(value)
        AnnotatedBase.__init__(self)

    def __str__(self):  # pylint: disable=E0307
        ret = AnnotatedStr(bool.__str__(self))
        ret.set_annotations(self.get_annotations())
        return ret

    @property  # type: ignore[misc]
    def __class__(self):
        return bool
