"""
Descriptive and useful errors, made with ease of use in mind.

The error classes described in this file are to be used wheb erroneous or
otherwise undesirable things are happening.
Basically they exist to not throw a generic error and instead provide clear
information about what went wrong. All they should need is the name of the
function raising the error unless stated otherwise.
"""

import vapoursynth as vs
core = vs.core


class VariableFormatError(TypeError):
    """
    Raised when a function only processes one type of VideoFormat at a time.
    """

    def __init__(self, fn_name: str):
        self.fn = f" in {fn_name}" if fn_name else ""

    def __str__(self) -> str:
        return f"Variable format clips are not supported{self.fn}"
