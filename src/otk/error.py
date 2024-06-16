"""Error types used by `otk`."""


class OTKError(Exception):
    """Any application raised by `otk` inherits from this."""

    pass


class ParseError(OTKError):
    """General base exception for any errors related to parsing omnifests."""

    pass


class ParseTypeError(ParseError):
    """A wrong type was encountered for a position in the omnifest."""

    pass


class ParseKeyError(ParseTypeError):
    """A required key was missing for a position in the omnifest."""

    pass


class ParseVersionError(ParseKeyError):
    """The `otk.version` key is missing from an omnifest."""

    pass


class ParseTargetError(ParseError):
    """An unknown target or no targets were encountered in the omnifest."""

    pass


class ParseValueError(ParseTypeError):
    """A required value was missing for a position in the omnifest."""

    pass


class TransformError(OTKError):
    """General base exception for any errors related to transforming
    omnifests."""

    pass


class TransformVariableLookupError(TransformError):
    """Failed to look up a variable."""

    pass


class TransformVariableTypeError(TransformError):
    """Failed to look up a variable due to a parent variable type."""

    pass


class TransformVariableIndexTypeError(TransformError):
    """Failed to look up an index into a variable due to the index contents
    not being a number."""

    pass


class TransformVariableIndexRangeError(TransformError):
    """Failed to look up an index into a variable due to it being out of
    bounds."""

    pass


class TransformDefineDuplicateError(TransformError):
    """Tried to redefine a variable."""

    pass


class TransformDirectiveTypeError(TransformError):
    """A directive received the wrong types."""

    pass


class TransformDirectiveArgumentError(TransformError):
    """A directive received the wrong argument(s)."""

    pass


class TransformDirectiveUnknownError(TransformError):
    """Unknown directive."""

    pass


class IncludeError(OTKError):
    pass
