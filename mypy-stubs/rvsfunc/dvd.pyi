import vapoursynth as vs
from .masking import eoe_convolution as eoe_convolution
from .utils import frame_to_array as frame_to_array
from typing import Any, Callable, Dict

core: Any

def chromashifter(clip: vs.VideoNode, wthresh: int = ..., vertical: bool = ..., maskfunc: Callable[[vs.VideoNode], vs.VideoNode] = ..., mask_kwargs: Dict = ..., shifter: Callable[[vs.VideoNode, Any], vs.VideoNode] = ...) -> vs.VideoNode: ...
