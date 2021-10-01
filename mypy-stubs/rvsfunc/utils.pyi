import numpy as np
import vapoursynth as vs
from .errors import VariableFormatError as VariableFormatError
from .masking import detail_mask as detail_mask
from typing import Any, Callable, Dict, List, Optional, Union

core: Any
vs_api_below4: Optional[bool]

def is_topleft(clip: vs.VideoNode) -> bool: ...
def batch_index(paths: Union[List[str], str], source_filter: Callable[..., vs.VideoNode], show_list: bool = ..., **src_args: Dict[str, Any]) -> List[vs.VideoNode]: ...
def nc_splice(source: vs.VideoNode, nc: vs.VideoNode, startframe: int, endframe: int, nc_filterfunc: Optional[Callable[[vs.VideoNode, Any], vs.VideoNode]] = ..., use_internal: bool = ..., ext_mask: Optional[vs.VideoNode] = ..., **kwargs: Dict[str, Any]) -> vs.VideoNode: ...
def copy_credits(source: vs.VideoNode, nc: vs.VideoNode, mask: Optional[vs.VideoNode] = ...) -> vs.VideoNode: ...
def frame_to_array(f: vs.VideoFrame) -> np.ndarray: ...