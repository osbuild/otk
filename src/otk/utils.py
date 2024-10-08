import json
from typing import TypeVar, Generic


def _deep_convert(data):
    """Recursively convert nested dicts and lists into HiddenAttrDict and HiddenAttrList."""
    if isinstance(data, (HiddenAttrDict, HiddenAttrList)):
        return data
    if isinstance(data, dict):
        return HiddenAttrDict({key: _deep_convert(value) for key, value in data.items()})
    if isinstance(data, list):
        return HiddenAttrList([_deep_convert(item) for item in data])
    return data


class HiddenAttrList(list):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._otk_hidden_attributes = {}

        for idx, value in enumerate(self):
            self[idx] = _deep_convert(value)

    def set_attribute(self, idx, attr_key, value):
        if idx not in self._otk_hidden_attributes:
            self._otk_hidden_attributes[idx] = {}
        self._otk_hidden_attributes[idx][attr_key] = value

    def get_attribute(self, idx, attr_key):
        if idx in self._otk_hidden_attributes and attr_key in self._otk_hidden_attributes[idx]:
            return self._otk_hidden_attributes[idx][attr_key]
        return None


HiddenAttrKeyT = TypeVar('HiddenAttrKeyT')
HiddenAttrVarT = TypeVar('HiddenAttrVarT')


class HiddenAttrDict(Generic[HiddenAttrKeyT, HiddenAttrVarT], dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        object.__setattr__(self, '_otk_hidden_attributes', {})

        for key, value in self.items():
            self[key] = _deep_convert(value)

    def set_attribute(self, key, attr_key, value):
        """ Set a hidden attribute for a key. """
        if key not in self._otk_hidden_attributes:
            self._otk_hidden_attributes[key] = {}
        self._otk_hidden_attributes[key][attr_key] = value

    def get_attribute(self, key, attr_key):
        """ Get a hidden attribute for a key. """
        if key in self._otk_hidden_attributes and attr_key in self._otk_hidden_attributes[key]:
            return self._otk_hidden_attributes[key][attr_key]
        raise KeyError(f"Attribute '{attr_key}' for key '{key}' not found")

    def __setattr__(self, key, value):
        self[key] = self._convert_value(value)

    def __getattr__(self, item):
        return self[item]


class HiddenAttrDictJSONEncoder(json.JSONEncoder):
    def encode(self, o):
        """ Encode method to handle custom HiddenAttrDict and HiddenAttrList serialization. """
        return super().encode(self._enrich_with_comment(o))

    def _enrich_with_comment(self, obj):
        if isinstance(obj, HiddenAttrDict):
            return self._add_comments_to_dict(obj)
        if isinstance(obj, HiddenAttrList):
            return self._add_comments_to_list(obj)
        return obj

    def _add_comments_to_dict(self, obj):
        """ Add comments, ready to be encoded """
        ret = {}
        # Serialize the dictionary items
        for key, value in obj.items():
            comment = obj.get_attribute(key, "src")
            if comment:
                ret[f"# source of {key}"] = comment
            ret[key] = self._enrich_with_comment(value)

        return ret

    def _add_comments_to_list(self, obj):
        """ Add comments, ready to be encoded """
        ret = []

        for index, value in enumerate(obj):
            src = obj.get_attribute("self", "src")
            comment = f"# source of index {index}: {src}"
            if comment:
                ret.append(comment)
            ret.append(self._enrich_with_comment(value))

        return ret
