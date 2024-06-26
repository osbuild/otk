"""Error types used by `otk`."""


class OTKError(Exception):
    """Any application raised by `otk` inherits from this."""


class ParseError(OTKError):
    """General base exception for any errors related to parsing omnifests."""


class ParseTypeError(ParseError):
    """A wrong type was encountered for a position in the omnifest."""


class ParseKeyError(ParseTypeError):
    """A required key was missing for a position in the omnifest."""


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


class CircularIncludeError(ParseError):
    """Cirtcular include detected."""


class NoTargetsError(ParseError):
    """No targets in the otk file found."""


class ExternalFailedError(OTKError):
    """ Call to external failed """
