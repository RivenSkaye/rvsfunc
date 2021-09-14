from enum import Enum
from typing import TypeVar

E = TypeVar('E', bound=Enum)

class Dither(str, Enum):
    NONE: str
    ORDERED: str
    RANDOM: str
    ERROR_DIFFUSION: str

class Range(int, Enum):
    LIMITED: int
    FULL: int
