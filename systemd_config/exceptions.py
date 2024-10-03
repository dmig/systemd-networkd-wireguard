class ParseError(Exception):
    def __init__(self, message: str, line: int, *args: object) -> None:
        super().__init__(message + f" on line {line}", *args)


class SectionlessKeyError(ParseError):
    def __init__(self, line: int, *args: object) -> None:
        super().__init__("Key outside of section", line, *args)


class IncompleteMultilineError(ParseError):
    def __init__(self, line: int, *args: object) -> None:
        super().__init__("Incomplete multiline value", line - 1, *args)


class SyntaxError(ParseError):
    def __init__(self, text: str, line: int, *args: object) -> None:
        super().__init__(f"Syntax error {text!r}", line, *args)
