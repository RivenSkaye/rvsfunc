from typing import Any, Dict, Callable, Optional
from .masking import detail_mask
import vsutil
import vapoursynth as vs
core = vs.core

def questionable_rescale(
    clip: vs.VideoNode, height: int, b: float=1/3, c: float=1/3,
    descaler: Callable[[vs.VideoNode, Any], vs.VideoNode]=core.descale.Debicubic,
    scaler: Callable[[vs.VideoNode, Any], vs.VideoNode]=core.resize.Spline36,
    scale_kwargs: Dict={}, correct_shift: bool=True, apply_mask: bool=True,
    mask_thresh: float=0.05, ext_mask: Optional[vs.VideoNode]=None,
    depth_out: int=-1, return_mask: bool=False) -> vs.VideoNode:
    from nnedi3_rpow2 import nnedi3_rpow2 as rpow2
    """ Descale function originally written by Zastin, edited by me.

    It's originally written for Doga Kobo material, since they have some weird
    post-processing going on, making a normal descale impossible. It applies
    some Expression magic for fixing some common Doga Kobo issues.
    USE AT YOUR OWN RISK.

    :param clip:            YUV input clip, integer format. Will be dithered
                            down if required.
    :param height:          The height to descale to.
    :param b:               The `b` or `filter_param_a` value for the descale.
    :param c:               The `c` or `filter_param_b` value for the descale.
    :param descaler:        The descaler to use. Will use Debicubic by default.
    :param scaler:          The scaler to use to scale the clip back to the
                            original or provided output resolution. Pass it a
                            function that returns the clip untouched to get the
                            questionably descaled and then doubled clip. Pass
                            None to prevent frame doubling. Defaults to Spline36.
                            Will be called as `scaler(clip, **scaler_kwargs)`.
    :param scaler_kwargs:   A kwargs dict for use with the upscaler. Defaults
                            to an empty dict and sets output width and height
                            to the same values as the input clip. Provide the
                            values for the `width` and `height` keys to change
                            the output resolution.
    :param correct_shift:   Same as in `nnedi3_rpow2`.
    :param apply_mask:      Whether or not to apply a detail mask.
    :param mask_thresh:     Threshold for binarizing the default mask.
    :param ext_mask:        Supply your own mask instead of the default.
    :param depth_out:       The output depth. Values below 0 will cause it to
                            use the depth of the input clip, any other values
                            will be passed to `vsutil.depth` the way they are
                            with no regards to what may be raised.
    :param return_mask:     Whether to return the mask used instead of the clip.
                            This requires `scaler` to not be None.
    """
    if clip.width == 0 or clip.height == 0:
        raise vs.Error("questionable_descale: var-res clips are not supported. \
                       Please slice the clip into several same-res clips or \
                       descale in another way.")
    if scale_kwargs.get("width") == None:
        scale_kwargs['width'] = clip.width
    if scale_kwargs.get("height") == None:
        scale_kwargs['height'] = clip.height
    depth_out = vsutil.get_depth(clip) if depth_out < 0 else depth_out
    if vsutil.get_depth(clip) > 16 or clip.format.sample_type == vs.FLOAT:
        clip = vsutil.depth(clip, 16, sample_type=vs.INTEGER)
    clamp = vsutil.depth(core.rgvs.RemoveGrain(clip, mode=1), 32, dither_type='none')
    clip = vsutil.depth(clip, 32, dither_type='none')
    chroma = clip.format.num_planes > 1

    if chroma:
        y,u,v = vsutil.split(clip)
        cy,cu,cv = vsutil.split(clamp)
    else:
        y = clip
        cy = clamp

    descy = descaler(y, width=vsutil.get_w(height, clip.width/clip.height), height=height, b=b, c=c)
    desccy = descaler(cy, width=vsutil.get_w(height, clip.width/clip.height), height=height, b=b, c=c)

    err = descy.resize.Bicubic(clip.width, clip.height, filter_param_a=b, filter_param_b=c)
    diff_a = core.std.Expr([y, err], 'x y - abs')
    cerr = desccy.resize.Bicubic(clip.width, clip.height, filter_param_a=b, filter_param_b=c)
    diff_b = core.std.Expr([cy, cerr], 'x y - abs')
    pre_descale = core.std.Expr([diff_a,diff_b,y,cy], f'x y - {1000/(1<<16)-1} > x {2500/(1<<16)-1} > and z a ?')

    descaled = descaler(pre_descale, width=vsutil.get_w(height, clip.width/clip.height), height=height, b=b, c=c)
    if not scaler: return descaled
    doubled = rpow2(descaled, correct_shift=correct_shift)
    doubled = scaler(doubled, **scale_kwargs)
    if apply_mask:
        mask = detail_mask(y, doubled, thresh=mask_thresh) if not ext_mask else ext_mask
        if return_mask: return mask
        doubled = core.std.MaskedMerge(doubled, y, mask)
    if chroma: doubled = vsutil.join([doubled,u,v])
    return vsutil.depth(doubled, depth_out)
