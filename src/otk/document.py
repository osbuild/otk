import io
import logging
from copy import deepcopy
from typing import Any

import yaml

from .constant import NAME_VERSION
from .error import ParseTypeError, ParseVersionError

log = logging.getLogger(__name__)


class Omnifest:
    # Underlying data is a dictionary containing the validated deserialized
    # contents of the bytes that were used to create this omnifest.
    _underlying_data: dict[str, Any]

    def __init__(self, underlying_data: dict[str, Any]) -> None:
        self._underlying_data = underlying_data

    @classmethod
    def from_yaml_bytes(cls, text: bytes) -> "Omnifest":
        deserialized_data = cls.read(yaml.safe_load(text))
        cls.ensure(deserialized_data)

        return cls(deserialized_data)

    @classmethod
    def from_yaml_file(cls, file: io.IOBase) -> "Omnifest":
        """Read a YAML file into an Omnifest instance."""
        log.debug("reading yaml from path %r", file.name)
        return cls.from_yaml_bytes(file.read())

    @classmethod
    def read(cls, deserialized_data: Any) -> dict[str, Any]:
        """Take any type returned by a deserializer and ensure that it is
        something that could represent an Omnifest."""

        # The top level of the Omnifest needs to be a dictionary
        if not isinstance(deserialized_data, dict):
            log.error(
                "data did not deserialize to a dictionary: type=%r,data=%r",
                type(deserialized_data),
                deserialized_data,
            )
            raise ParseTypeError("omnifest must deserialize to a dictionary")

        return deserialized_data

    @classmethod
    def ensure(cls, deserialized_data: dict[str, Any]) -> None:
        """Take a dictionary and ensure that its keys and values would be
        considered an Omnifest."""

        # And that dictionary needs to contain certain keys to indicate this
        # being an Omnifest.
        if NAME_VERSION not in deserialized_data:
            raise ParseVersionError("omnifest must contain a key by the name of %r" % (NAME_VERSION,))

    @property
    def tree(self) -> dict[str, Any]:
        return deepcopy(self._underlying_data)
