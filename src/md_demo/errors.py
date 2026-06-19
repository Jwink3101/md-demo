class MdDemoError(Exception):
    """Base error for user-facing md-demo failures."""


class ExecutionFailed(MdDemoError):
    """Raised after a block fails and the document has been reconstructed."""

    def __init__(self, message: str, document: str):
        super().__init__(message)
        self.document = document
