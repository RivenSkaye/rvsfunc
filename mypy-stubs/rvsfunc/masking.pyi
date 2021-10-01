import vapoursynth as vs
from typing import Any, Callable, Optional

core: Any

def scradit_mask(src_luma: vs.VideoNode, rescaled_luma: vs.VideoNode, absthresh: float = ..., iters: int = ...) -> vs.VideoNode: ...
def detail_mask(source: vs.VideoNode, rescaled: vs.VideoNode, thresh: float = ...) -> vs.VideoNode: ...
def dehalo_mask(clip: vs.VideoNode, maskgen: Optional[Callable[[vs.VideoNode], vs.VideoNode]] = ..., iter_out: int = ..., iter_in: int = ..., inner: bool = ..., outer: bool = ...) -> vs.VideoNode: ...
def fineline_mask(clip: vs.VideoNode, thresh: int = ...) -> vs.VideoNode: ...
def eoe_convolution(clip: vs.VideoNode) -> vs.VideoNode: ...