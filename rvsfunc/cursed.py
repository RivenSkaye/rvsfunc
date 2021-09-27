"""
Edgecase functions that were generalized for if I ever need them again.
Most of these functions should not be used in the general use case. They're
typically written for a very specific edgecase, but generalized for if I ever
need them again. Currently only holds `questionable_rescale` which I mangled
from someone else's code that had a very similar edgecase.
"""

import vapoursynth as vs
from .masking import detail_mask
from typing import Any, Dict, Callable, Optional
from vsutil import depth, get_depth, get_w, get_y
from nnedi3_rpow2 import nnedi3_rpow2


core = vs.core

_Descaler = Callable[[vs.VideoNode, int, int, Any, Any, Any], vs.VideoNode]
_Scaler = Callable[[vs.VideoNode, int, int, Any], vs.VideoNode]


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
        raise vs.Error(
            "questionable_descale: var-res clips are not supported. \
            Please slice the clip into several same-res clips or \
            descale in another way."
        )
    
    if not clip.format:
        raise ValueError("questionable rescale: no variable format clips!")

    if scale_kwargs.get("width") is None:
        scale_kwargs["width"] = clip.width

    if scale_kwargs.get("height") is None:
        scale_kwargs["height"] = clip.height

    if depth_out < 0:
        depth_out = get_depth(clip)

    if get_depth(clip) > 16 or clip.format.sample_type == vs.FLOAT:
        clip = depth(clip, 16, sample_type=vs.INTEGER)

    rgv = core.rgvs.RemoveGrain(clip, mode=1)

    clamp, clip = depth(rgv, 32), depth(clip, 32)

    chroma = clip.format.num_planes > 1

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

    doubled = scaler(
        nnedi3_rpow2(descaled, shift=correct_shift, cl=True), **scale_kwargs
    )  # type: ignore

    if apply_mask:
        if not ext_mask:
            mask = detail_mask(y, doubled, thresh=mask_thresh)
        else:
            mask = depth(ext_mask, get_depth(doubled))
        if return_mask:
            return mask
        doubled = core.std.MaskedMerge(doubled, y, mask)

    if chroma:
        doubled = core.std.ShufflePlanes([doubled, clip], [0, 1, 2], vs.YUV)

    return depth(doubled, depth_out)
