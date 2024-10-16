import sys
import time
import threading

from typing import Optional, Type
from types import TracebackType

from . import __version__


class _Spinner:
    """Render a spinner with an optional prompt to stderr, if stderr isn't a
    tty this only prints the prompt."""

    active: bool
    thread: threading.Thread

    def __init__(self, prompt: str) -> None:
        self.prompt = prompt

    def _loop(self):
        sys.stderr.write(self.prompt)
        sys.stderr.flush()

        # No spinner business if we aren't printing to tty's.
        if sys.stderr.isatty():
            while self.active:
                sys.stderr.write(".")
                sys.stderr.flush()
                time.sleep(0.1)

        # Only write a newline if the prompt was actually there
        if self.prompt:
            sys.stderr.write("\n")
            sys.stderr.flush()

    def __enter__(self, prompt: str = "") -> None:
        self.active = True
        self.thread = threading.Thread(target=self._loop)
        self.thread.start()

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        self.active = False
        self.thread.join()

        return True


def spinner(prompt: str) -> _Spinner:
    return _Spinner(prompt)


def print(text: str) -> None:  # pylint: disable=redefined-builtin
    """Write a line of text to stderr if it's attached to a tty."""
    if sys.stderr.isatty():
        sys.stderr.write(text + "\n")
        sys.stderr.flush()


def motd() -> None:
    # Note, this is the local print function
    print(f"otk {__version__} -- https://www.osbuild.org/")
