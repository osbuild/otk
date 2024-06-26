PREFIX = "otk."

PREFIX_TARGET = f"{PREFIX}target."
PREFIX_OP = f"{PREFIX}op."

PREFIX_INCLUDE = f"{PREFIX}include"
PREFIX_DEFINE = f"{PREFIX}define"

PREFIX_EXTERNAL = f"{PREFIX}external."

NAME_VERSION = f"{PREFIX}version"

# only allow "simple" variable names to avoid confusion
VALID_VAR_NAME_RE = r"[a-zA-Z][a-zA-Z0-9_]*"
