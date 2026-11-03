class ProcessingError(ValueError):
    """Safe local-processing code; never include source contents or credentials."""

    def __init__(self, code: str) -> None:
        self.code = code
        self.message_key = "processing." + code.lower()
        super().__init__(code)
