import vapoursynth as vs
from .NNEDI3 import ZNEDI3 as ZNEDI3
from .masking import detail_mask as detail_mask
from typing import Any, Callable, Dict, Optional

core: Any

def chunked_filter(clip: vs.VideoNode, func: Callable[[vs.VideoNode], vs.VideoNode], *, hchunks: int = ..., vchunks: int = ...) -> vs.VideoNode: ...
def questionable_rescale(clip: vs.VideoNode, height: int, b: float = ..., c: float = ..., descaler: _Descaler = ..., scaler: Optional[_Scaler] = ..., scale_kwargs: Dict = ..., correct_shift: bool = ..., apply_mask: bool = ..., mask_thresh: float = ..., ext_mask: Optional[vs.VideoNode] = ..., depth_out: int = ..., return_mask: bool = ...) -> vs.VideoNode: ...
