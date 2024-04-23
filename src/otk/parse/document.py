import logging
import pathlib
from typing import Any, Self

import yaml

from ..constant import NAME_VERSION, PREFIX, PREFIX_TARGET
from ..error import ParseTargetError, ParseTypeError, ParseVersionError
from ..target import registry as target_registry

log = logging.getLogger(__name__)


class Omnifest:
    # Underlying data is a dictionary containing the validated deserialized
    # contents of the bytes that were used to create this omnifest.
    _underlying_data: dict[str, Any]

    def __init__(self, underlying_data: dict[str, Any]) -> None:
        self._underlying_data = underlying_data

    @classmethod
    def from_yaml_bytes(cls, text: bytes, ensure: bool = True) -> Self:
        deserialized_data = cls.read(yaml.safe_load(text), ensure)

        if ensure:
            cls.ensure(deserialized_data)

        return cls(deserialized_data)

    @classmethod
    def from_yaml_path(cls, path: pathlib.Path, ensure: bool = True) -> Self:
        """Read a YAML file into an Omnifest instance."""

        log.debug("reading yaml from path %r", str(path))

        # This is an invariant that should be handled at the calling side of
        # this function
        assert path.exists(), "path to exist"

        with path.open("rb") as file:
            return cls.from_yaml_bytes(file.read(), ensure)

    @classmethod
    def read(cls, deserialized_data: Any, ensure: bool = True) -> dict[str, Any]:
        """Take any type returned by a deserializer and ensure that it is
        something that could represent an Omnifest."""

        if ensure:
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
            raise ParseVersionError(
                "omnifest must contain a key by the name of %r" % (NAME_VERSION,)
            )

        # Make sure that the omnifest contains targets. Without targets we
        # can't do much.
        if not any(key.startswith(PREFIX_TARGET) for key in deserialized_data):
            raise ParseTargetError(
                "omnifest must contain at least one key by the name of `%s.*`"
                % (PREFIX_TARGET,)
            )

    def to_tree(self) -> dict[str, Any]:
        return self._underlying_data
