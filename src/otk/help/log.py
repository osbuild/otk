import logging
import json


class _JSONFormatter(logging.Formatter):
    def __init__(
        self,
        identifier: str | None = None,
    ) -> None:
        super().__init__()
        self.identifier = identifier

    def format(self, record: logging.LogRecord) -> str:
        if self.identifier:
            if hasattr(record, "identifier"):
                raise ValueError("identifier already in log record")

            record.identifier = self.identifier

        return json.dumps(record.__dict__)


class JSONSequenceHandler(logging.StreamHandler):
    def __init__(self, identifier: str | None = None, stream=None) -> None:
        super().__init__(stream)

        self.formatter = _JSONFormatter(identifier)

    def emit(self, record: logging.LogRecord) -> None:
        self.acquire()

        self.stream.write("\x1e")
        self.stream.write(self.format(record))
        self.stream.write("\n")
        self.flush()

        self.release()
