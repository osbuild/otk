from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("otk")
except PackageNotFoundError:
    __version__ = "unknown"
