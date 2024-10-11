"""Error types used by `otk`."""

from typing import Optional, TYPE_CHECKING

from .annotation import AnnotatedBase

if TYPE_CHECKING:
    # required to avoid circular import errors
    from .traversal import State


class OTKError(Exception):
    """Any application raised by `otk` inherits from this."""

    def __init__(self, msg: str, state: Optional['State'] = None, annotated: Optional['AnnotatedBase'] = None) -> None:
        if annotated and isinstance(annotated, AnnotatedBase) and annotated.get_annotation("src"):
            super().__init__(f"{annotated.get_annotation('src')} - {msg}")
        elif state:
            super().__init__(f"{state.path}: {msg}")
        else:
            super().__init__(msg)


class ParseError(OTKError):
    """General base exception for any errors related to parsing omnifests."""


class ParseTypeError(ParseError):
    """A wrong type was encountered for a position in the omnifest."""


class ParseKeyError(ParseTypeError):
    """A required key was missing for a position in the omnifest."""


class ParseDuplicatedYamlKeyError(ParseError):
    """A yaml key is duplicated."""


class ParseVersionError(ParseKeyError):
    """The `otk.version` key is missing from an omnifest."""


class ParseTargetError(ParseError):
    """An unknown target or no targets were encountered in the omnifest."""


class ParseValueError(ParseTypeError):
    """A required value was missing for a position in the omnifest."""


class TransformError(OTKError):
    """General base exception for any errors related to transforming
    omnifests."""


class TransformVariableLookupError(TransformError):
    """Failed to look up a variable."""


class TransformVariableTypeError(TransformError):
    """Failed to look up a variable due to a parent variable type."""


class TransformVariableIndexTypeError(TransformError):
    """Failed to look up an index into a variable due to the index contents
    not being a number."""


class TransformVariableIndexRangeError(TransformError):
    """Failed to look up an index into a variable due to it being out of
    bounds."""


class TransformDefineDuplicateError(TransformError):
    """Tried to redefine a variable."""


class TransformDirectiveTypeError(TransformError):
    """A directive received the wrong types."""


class TransformDirectiveArgumentError(TransformError):
    """A directive received the wrong argument(s)."""


class TransformDirectiveUnknownError(TransformError):
    """Unknown directive."""


class CircularIncludeError(OTKError):
    """Cirtcular include detected."""


class IncludeNotFoundError(OTKError):
    """The requested include was not found."""


class NoTargetsError(ParseError):
    """No targets in the otk file found."""


class ExternalFailedError(OTKError):
    """ Call to external failed """
