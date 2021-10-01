from typing import Any

core: Any

class VariableFormatError(TypeError):
    fn: Any
    def __init__(self, fn_name: str) -> None: ...
