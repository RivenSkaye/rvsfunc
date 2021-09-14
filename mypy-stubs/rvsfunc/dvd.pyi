import vapoursynth as vs
from typing import Any, Callable, Dict

core: Any

def eoe_convolution(clip: vs.VideoNode) -> vs.VideoNode: ...
def chromashifter(clip: vs.VideoNode, wthresh: int = ..., vertical: bool = ..., maskfunc: Callable[[vs.VideoNode, Any], vs.VideoNode] = ..., mask_kwargs: Dict = ..., shifter: Callable[[vs.VideoNode, Any], vs.VideoNode] = ...) -> vs.VideoNode: ...
