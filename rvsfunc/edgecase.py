""" Edgecase functions that were generalized for if I ever need them again.

These functions should probably not be used in the general use case. They're
typically written for a very specific edgecase, but generalized for if I ever
need them again. Currently only holds `questionable_rescale` which I mangled
from someone else's code that had a very similar edgecase.
"""

import vapoursynth as vs
from .masking import detail_mask
from .NNEDI3 import ZNEDI3
from .errors import VariableFormatError, VariableResolutionError
from typing import Any, Dict, Callable, Optional
from vsutil import depth, get_depth, get_w, get_y


core = vs.core

_Descaler = Callable[[vs.VideoNode, int, int, Any, Any, Any], vs.VideoNode]
_Scaler = Callable[[vs.VideoNode, int, int, Any], vs.VideoNode]


def chunked_filter(clip: vs.VideoNode,
                   func: Callable[[vs.VideoNode], vs.VideoNode],
                   *, hchunks: int = 3, vchunks: int = 3) -> vs.VideoNode:
    """
    Apply a filter to video in blocks of video smaller than the clip's surface.

    This is a utility function written for certain functions or filters don't
    handle frames or clips over a certain size. It splits the clip into
    grid-based chunks to apply the filter to subsections of the clip.
    Chunks are then stacked into new clips that keep them in the same place as
    the corresponding chunk of the next frame to allow for temporal filters to
    work with the same area of the clip as if it was never split. Spatial
    filters might be impacted near the edges of chunks.

    :param clip:        The clip to chunk and filter.
    :param filter:      The filter to apply to the chunked clips.
                        It's recommended to supply either a function that
                        takes the clip as its only argument, or to supply a
                        partial to supply (kw)args to the filter.
    :param hchunks:     The minimum amount of horizontal chunks to use.
    :param vchunks:     The minimum amount of vertical chunks to use.
    """

    lh, ch = clip.height, clip.height/2
    lw, cw = clip.width, clip.width/2
    while lh % vchunks > 0 and ch % vchunks > 0:
        vchunks += 1

    while lw % hchunks > 0 and cw % hchunks > 0:
        hchunks += 1

    height = int(lh / vchunks)
    width = int(lw / hchunks)
    rows = []

    for x in range(0, vchunks):
        chunks = []
        for y in range(0, hchunks):
            chunk = core.std.CropAbs(clip, width=width, height=height,
                                     left=y*width, top=x*height)
            chunks.append(func(chunk))
        rows.append(core.std.StackHorizontal(clips=chunks))
    return core.std.StackVertical(clips=rows)


def questionable_rescale(
    clip: vs.VideoNode, height: int, b: float = 1 / 3, c: float = 1 / 3,
    descaler: _Descaler = core.descale.Debicubic,
    scaler: Optional[_Scaler] = core.resize.Spline36,
    scale_kwargs: Dict = {"height": None}, correct_shift: bool = True,
    apply_mask: bool = True, mask_thresh: float = 0.05,
    ext_mask: Optional[vs.VideoNode] = None, depth_out: int = -1,
    return_mask: bool = False
) -> vs.VideoNode:
    """
    Rescale function by Zastin for Doga Kobo, edited for reusability.

    It's originally written for Doga Kobo material, since they have some weird
    post-processing going on, making a normal descale impossible. It applies
    some Expression magic for fixing some common Doga Kobo issues.
    USE AT YOUR OWN RISK.

    :param clip:            YUV input clip, integer format. Will be dithered
                            down if required.
    :param height:          The height to descale to.
    :param b:               ``b`` or ``filter_param_a`` arg for the descale.
    :param c:               ``c`` or ``filter_param_b`` arg for the descale.
    :param descaler:        The descaler to use. Will use Debicubic by default.
    :param scaler:          The scaler to use to scale the clip back to the
                            original or provided output resolution. Pass it a
                            function that returns the clip untouched to get the
                            questionably descaled and then doubled clip. Pass
                            None to prevent frame doubling. Default: Spline36.
                            Called as ``scaler(clip, **scaler_kwargs)``.
    :param scaler_kwargs:   A kwargs dict for use with the upscaler. Defaults
                            to an empty dict and sets output width and height
                            to the same values as the input clip. Provide the
                            values for the ``width`` and ``height`` keys to
                            change the output resolution.
    :param correct_shift:   Same as in ``nnedi3_rpow2``.
    :param apply_mask:      Whether or not to apply a detail mask.
    :param mask_thresh:     Threshold for binarizing the default mask.
    :param ext_mask:        Supply your own mask instead of the default.
    :param depth_out:       The output depth. Values below 0 will cause it to
                            use the depth of the input clip, any other values
                            will be passed to ``depth`` the way they are
                            with no regards to what may be raised.
    :param return_mask:     Whether to return the mask used instead of the clip.
                            This requires ``scaler`` to not be None.
    """

    if clip.width == 0 or clip.height == 0:
        raise VariableResolutionError("questionable_rescale")

    if not clip.format:
        raise VariableFormatError("questionable_rescale")

    if scale_kwargs.get("width") is None:
        scale_kwargs["width"] = clip.width

    if scale_kwargs.get("height") is None:
        scale_kwargs["height"] = clip.height

    if depth_out < 0:
        depth_out = get_depth(clip)

    chroma = clip.format.num_planes > 1

    if get_depth(clip) > 16 or clip.format.sample_type == vs.FLOAT:
        clip = depth(clip, 16, sample_type=vs.INTEGER)

    rgv = core.rgvs.RemoveGrain(clip, mode=1)

    clamp, clip = depth(rgv, 32), depth(clip, 32)

    if chroma:
        y, cy = get_y(clip), get_y(clamp)
    else:
        y, cy = clip, clamp

    descy = descaler(y, get_w(height, clip.width / clip.height),
                     height, b, c)  # type: ignore
    desccy = descaler(cy, get_w(height, clip.width / clip.height),
                      height, b, c)  # type: ignore

    def _get_err_diff(y: vs.VideoNode) -> vs.VideoNode:
        err = y.resize.Bicubic(y.width, y.height, filter_param_a=b, filter_param_b=c)
        return core.std.Expr([y, err], "x y - abs")

    diff_a, diff_b = _get_err_diff(descy), _get_err_diff(desccy)

    peak = (1 << 16) - 1

    pre_descale = core.std.Expr(
        [diff_a, diff_b, y, cy],
        f"x y - {1000 / peak} > x {2500 / peak} > and z a ?"
    )

    descaled = descaler(pre_descale,
                        get_w(height, clip.width / clip.height),
                        height, b, c)  # type: ignore

    if not scaler:
        return descaled

    doubled = scaler(ZNEDI3.rpow2(descaled, shift=correct_shift),
                     clip.width, clip.height, None)

    if apply_mask:
        if not ext_mask:
            masky = depth(y, 32)
            dbld = depth(doubled, 32)
            mask = detail_mask(masky, dbld, thresh=mask_thresh)
            mask = depth(mask, 16, sample_type=vs.INTEGER)
        else:
            mask = depth(ext_mask, get_depth(doubled))
        if return_mask:
            return mask
        doubled = core.std.MaskedMerge(doubled, y, mask)

    if chroma:
        doubled = core.std.ShufflePlanes([doubled, clip], [0, 1, 2], vs.YUV)

    return depth(doubled, depth_out)
