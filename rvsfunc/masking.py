"""
Different kinds of masking functions I either wrote or "borrowed".
These are generalized as much as possible, but some masking functions just
exist for a very specific purpose.
This is also my playground to mess with Expressions and convolutions, so
expect some stuff to get added and removed infrequently and a fair few commits
that state something along the lines of me complaining about broken code.
"""

from math import floor
import vapoursynth as vs
from typing import Any, Dict, Callable
from vsutil import depth, get_y, iterate


core = vs.core


def scradit_mask(
    src_luma: vs.VideoNode,
    rescaled_luma: vs.VideoNode,
    height: int = 720,
    absthresh: float = 0.060, iters: int = 4
) -> vs.VideoNode:
    """
    Credit masking function borrowed from Scrad.
    Changed it to be used in a more generic manner, but the core stuff and
    math comes from him. Or wherever he got it.
    Returns a 32 bit (GrayS) mask.
    :param luma:        Luma plane of the input video. If it has more planes,
                        the luma plane will be extracted.
    :param b:           b value for the descaler, defaults to 1/3.
    :param c:           c value for the descaler, defaults to 1/3.
    :param height:      The height to descale to for a correct error rate.
    :param absthresh:   The abs threshold for binarizing the mask with.
    :param iters:       How often to iterate Maximum and Inflate calls.
    :param descaler:    The descaling function to use, defaults to Debicubic.
    :param upscaler:    The upscaling function, defaults to Bicubic.
    :param dekwargs:    A dict with extra options for the descaler.
    :param upkwargs:    A dict with extra options for the upscaler.
    """

    luma = depth(get_y(src_luma), 32)

    rescaled = depth(get_y(rescaled_luma), 32)

    mask = core.std.Expr([luma, rescaled], f"x y - abs {absthresh} < 0 1 ?")

    mask = iterate(mask, core.std.Maximum, iters)

    return iterate(mask, core.std.Inflate, iters)


def detail_mask(
  source: vs.VideoNode, rescaled: vs.VideoNode, thresh: float = 0.05
) -> vs.VideoNode:
    """
    Generates a fairly basic detail mask, mostly for descaling purposes.
    This is mostly used to pick up on detail *lost* in
    :py:func:`.cursed.questionable_rescale` as per Zastin's original script.
    Catches most if not all elements in a different native resolution
    :param source:      The clip to generate the mask for.
    :param rescaled:    The descaled and re-upscaled clip where detail was lost.
    :param thresh:      The threshold for binarizing the detail mask
    """

    sy, ry = get_y(source), get_y(rescaled)

    if not (sy.format and ry.format):
        raise ValueError("detail_mask: 'Variable-format clips not supported'")

    if sy.format.id != ry.format.id:
        sy = core.resize.Bicubic(sy, format=ry.format.id)

    mask = core.std.Expr([sy, ry], "x y - abs").std.Binarize(thresh)

    mask = iterate(mask, core.std.Maximum, 4)

    return iterate(mask, core.std.Inflate, 4)


def dehalo_mask(
    clip: vs.VideoNode,
    maskgen: Optional[Callable[[vs.VideoNode], vs.VideoNode]] = None,
    iter_out: int = 2, iter_in: int = -1, inner: bool = False,
    outer: bool = False, **mask_args: Dict[str, Any]
) -> vs.VideoNode:
    """
    Lazy wrapper for making a dehalo mask.
    Expects a YUV clip. No idea what happens when anything else is passed,
    and it's not my issue to figure that out either. Make sure to handle
    any conversions properly before calling this function with a clip.
    :param clip:        The clip to generate the mask for
    :param maskgen:     The masking function to call. Default Prewitt.
    :param iter_out:    Amount of times to iterate expansion for the outer mask
                        Defaults to 2, the standard size
    :param iter_in:     Amount of times to iterate impansion for the inner mask
                        Defaults to ``iter_out+1``.
    :param inner:       Returns the inner mask for checking.
    :param outer:       Returns the outer mask for checking.
    :param mask_args:   Expanded as ``**kwargs`` for ``mask_gen``
    """
    
    maskgen = maskgen if maskgen else lambda c: core.std.Prewitt(c, 0)

    mask = maskgen(clip)

    luma = core.std.ShufflePlanes(mask, 0, colorfamily=vs.GRAY)

    mout = iterate(luma, core.std.Maximum, iter_out)

    if outer:
        return mout

    iter_in = (iter_out + 1) if iter_in < 0 else iter_in

    minn = iterate(mout, core.std.Minimum, iter_in)

    return minn if inner else core.std.Expr([mout, minn], "x y -")


def fineline_mask(clip: vs.VideoNode, thresh: int = 95) -> vs.VideoNode:
    """
    Generates a very fine mask for lineart protection. Not perfect yet
    The generated mask is GRAY8, keep this in mind for conversions.
    :param clip:        The clip to generate the mask for.
    :param thresh:      The threshold for the binarization step.
    """

    prew = core.std.Prewitt(clip, planes=[0])
    thin = core.std.Minimum(prew)

    yp, yt = get_y(prew), get_y(thin)

    maska = core.std.Expr([yp, yt], ["x y < y x ?"])

    bin_mask = core.std.Binarize(maska, threshold=thresh)

    redo = int(floor(thresh / 2.5) * 2)

    return core.std.Expr([bin_mask, maska], [f"x y < y x ? {redo} < 0 255 ?"])


def eoe_convolution(clip: vs.VideoNode) -> vs.VideoNode:
    """ Convolution written by EoE for :py:func:`.dvd.chromashifter`"""
    matrix = [-1] * 4 + [8] + [-1] * 4

    return clip.std.Convolution(matrix, planes=[0, 1, 2], saturate=False)
