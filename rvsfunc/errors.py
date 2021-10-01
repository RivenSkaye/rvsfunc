"""
Descriptive and useful errors, made with ease of use in mind.

The error classes described here are to be used when erroneous or otherwise
undesirable things are happening, like passing unsupported types of video.
Mostly they exist to not throw a generic error and instead provide clear
information about what went wrong. All they should need is the name of the
function raising the error unless stated otherwise.
"""

from typing import Optional
import vapoursynth as vs
core = vs.core


class VariableFormatError(TypeError):
    """Raised for functions that only operate on constant format VideoNodes."""

    def __init__(self, fn_name: Optional[str] = None) -> None:
        self.fn = f" in {fn_name}" if fn_name else ""

    def __str__(self) -> str:
        return f"Variable format clips are not supported{self.fn}"


class VariableResolutionError(ValueError):
    """Raised for functions that don't handle VarRes clips"""

    def __init__(self, fn_name: Optional[str] = None) -> None:
        self.fn = f" in {fn_name}" if fn_name else ""

    def __str__(self) -> str:
        return f"VarRes clips are not supported{self.fn}"


class YUVError(ValueError):
    """Raised for functions that only process YUV input"""

    def __init__(self, fn_name: Optional[str] = None) -> None:
        self.fn = f" to {fn_name}" if fn_name else ""

    def __str__(self) -> str:
        return f"YUV input was expected, but something else was given{self.fn}"
