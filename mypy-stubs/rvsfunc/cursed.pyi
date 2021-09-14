import vapoursynth as vs
from .masking import detail_mask as detail_mask
from typing import Any, Callable, Dict, Optional

core: Any

def questionable_rescale(clip: vs.VideoNode, height: int, b: float = ..., c: float = ..., descaler: Callable[[vs.VideoNode, Any], vs.VideoNode] = ..., scaler: Callable[[vs.VideoNode, Any], vs.VideoNode] = ..., scale_kwargs: Dict = ..., correct_shift: bool = ..., apply_mask: bool = ..., mask_thresh: float = ..., ext_mask: Optional[vs.VideoNode] = ..., depth_out: int = ..., return_mask: bool = ...) -> vs.VideoNode: ...
