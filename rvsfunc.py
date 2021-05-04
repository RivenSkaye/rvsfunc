import vapoursynth as vs
import vsutil
from typing import Any, Dict, Callable, Optional
core = vs.core

def nc_splice(source: vs.VideoNode, nc: vs.VideoNode, startframe: int, endframe: int,
              nc_filterfunc: Optional[Callable[[vs.VideoNode, Any], vs.VideoNode]]=None,
              use_internal: bool=False, ext_mask: Optional[vs.VideoNode]=None, **kwargs) -> vs.VideoNode:
    """ Function for splicing in video from a different source.

    Originally written to splice in NCs whilst keeping the option open to keep
    the episode credits, this function takes an optional callable to perform
    any filtering on the NC. For example merging in the credits from the source
    clip. Assumes that `nc` will be added into the source clip in full. If this
    behavior is undesirable, either use a different function for it or send in
    only the part of the second clip that needs to be spliced in.

    :param source:          The source clip that needs something replaced
    :param nc:              The clip that needs to be spliced into source
    :param startframe:      The frame to start splicing at. This is an inclusive
                            selection value, and in reality 1 is added to it due to
                            how slicing works in Python. The selected range is
                            `source[:startframe+1]`.
    :param endframe:        The first frame that needs to be kept. This is an
                            inclusive selection value, selected as `source[endframe:]`.
    :param nc_filterfunc:   The function to call to perform filering on the NC.
                            For convenience, all additional kwargs will be
                            passed into this function as well. Use this for any
                            arguments that the external function needs.
    :param use_internal:    Whether or not to use internal functions to mask in
                            the difference between source and nc. As this is
                            originally meant to merge in credits, the internal
                            function `copy_credits` which uses some borrowed
                            logic in an attempt to merge in all credits from
                            the target range in the source clip. Using the
                            internal functions or nc_filterfunc are mutually
                            exclusive. Kwargs will not be passed on to this.
                            Defaults to `False`
    :param ext_mask:        For when the internal merging function is good enough
                            but the mask it generates isn't. This will only be
                            used if `use_internal` is set to `True` and will
                            be passed on for use in `copy_credits`
    """
    if nc_filterfunc:
        nc = nc_filterfunc(nc, **kwargs)
    elif use_internal:
        nc = copy_credits(source[startframe:endframe+1], nc, ext_mask)
    out = source[:startframe+1] + nc + source[endframe:]
    return out

def copy_credits(source: vs.VideoNode, nc: vs.VideoNode, mask: Optional[vs.VideoNode]=None) -> vs.VideoNode:
    """ Copy credits from the source to the nc using a diff_mask.

    This function assumes there is no notable difference between the NC and the
    source clip so that the internal mask is gonna catch nothing but
    credits and perhaps a few stray pixels.
    Returns the NC with the credits merged in from the source.

    :param source:      The clip to take the credits from. If you need them from
                        a subsection of the full clip, slice it yourself.
    :param nc:          The NC to copy the credits into
    :param mask:        Optionally an external mask to use for copying over the
                        credits if the detail_mask doesn't do a good enough job.
    """
    def _mask(clipa, clipb):
        clipa = core.resize.Point(clipa, format=clipb.format.id) if not clipa.format.id == clipb.format.id else clipa
        return core.std.Expr([sy, ry], 'x y - abs').std.Binarize()
    mask = _mask(source,nc) if not mask else mask
    return core.std.MaskedMerge(nc, source, mask)

def detail_mask(source: vs.VideoNode, rescaled: vs.VideoNode, thresh: float=0.05) -> vs.VideoNode:
    """ Generates a fairly basic detail mask

    This was originally part of `questionable_descale`'s internal logic, but
    the detail mask can be used in more places as well. The mask is pretty coarse
    and grabs a bit more than it'd strictly need, but you can mess with the thresh
    if you need it to pick up more or less.
    This is mostly used to pick up on detail _lost_ in `questionable_descale` as
    per Zastin's original script. That said, the mask serves other typical uses
    as well. For example grabbing credits and native different res elements in
    the source clip.

    :param source:      The clip to generate the mask for.
    :param rescaled:    The descaled and re-upscaled clip where detail was lost.
    :param thresh:      The threshold for binarizing the detail mask
    """
    sy = vsutil.get_y(source)
    ry = vsutil.get_y(rescaled)
    sy = core.resize.Point(sy, format=ry.format.id) if not sy.format.id == ry.format.id else sy
    mask = core.std.Expr([sy, ry], 'x y - abs').std.Binarize(thresh)
    mask = vsutil.iterate(mask, core.std.Maximum, 4)
    mask = vsutil.iterate(mask, core.std.Inflate, 4)
    return mask

def dehalo_mask(clip: vs.VideoNode,
    maskgen: Callable[[vs.VideoNode, Any], vs.VideoNode]=None,
    iter_out: int=2, iter_in: int=-1, inner: bool=False, outer: bool=False,
    **mask_args) -> vs.VideoNode:
    """ Lazy wrapper for making a dehalo mask.

    Expects a YUV clip. No idea what happens when anything else is passed,
    and it's not my issue to figure that out either. Make sure to handle
    any conversions properly before calling this function with a clip.

    :param clip:        The clip to generate the mask for
    :param maskgen:     The function to call for making the mask,
                        Defaults to `core.std.Prewitt` but any other
                        callable may be used
    :param iter_out:    Amount of times to iterate expansion for the outer mask
                        Defaults to 2, the standard size
    :param iter_in:     Amount of times to iterate impansion for the inner mask
                        Defaults to `iter_out+1`. Negative values make it calculate
                        this default, default value is -1
    :param inner:       Whether or not to return the inner mask, useful for
                        finetuning.
    :param outer:       Whether or not to return the outer mask, useful for
                        finetuning.
    Remaining args will be collected and expanded as args for `maskgen`
    """
    maskgen = core.std.Prewitt if maskgen is None else maskgen
    mask = maskgen(clip, **mask_args) if mask_args else maskgen(clip, 0)
    luma = core.std.ShufflePlanes(mask, 0, colorfamily=vs.GRAY)
    mout = vsutil.iterate(luma, core.std.Maximum, iter_out)
    if outer: return mout
    iter_in = iter_out+1 if iter_in < 0 else iter_in
    minn = vsutil.iterate(mout, core.std.Minimum, iter_in)
    if inner: return minn
    return core.std.Expr([mout, minn], "x y -")

def questionable_rescale(
    clip: vs.VideoNode, height: int, b: float=1/3, c: float=1/3,
    descaler: Callable[[vs.VideoNode, Any], vs.VideoNode]=None,
    correct_shift: bool=True, apply_mask: bool=True, mask_thresh: float=0.05,
    ext_mask: vs.VideoNode=None, return_mask: bool=False) -> vs.VideoNode:
    from nnedi3_rpow2 import nnedi3_rpow2 as rpow2
    """ Descale function originally written by Zastin, edited by me.

    It's originally written for Doga Kobo, since they have some weird post-processing going on
    that may include super dark or super bright pixels in areas they shouldn't be, as well as
    making a normal descale impossible. It applies clamping to pixels with extremely blown up
    values if they seem out of place, as well as some Expr magic for error correction on the
    source. Use at your own risk. Added the descaler as an arg and included the actual descale.

    :param clip:            Input clip, ``vsutil.depth(clip, 16)`` will be called if this is not
                            16 or less bits integer format. Clip must be YUV
    :param height:          The height to descale to. Proper width will be calculated.
    :param b:               The `b` or `filter_param_a` value for the descale
    :param c:               The `c` or `filter_param_b` value for the descale
    :param descaler:        The descaler to use. Will use ``core.descale.Debicubic`` by default
    :param correct_shift:   Same as in ``nnedi3_rpow2``
    :param apply_mask:      Whether or not to apply a detail mask
    :param mask_thresh:     Threshold for binarizing the default mask
    :param ext_mask:        Supply your own instead of the default
    :param return_mask:     Whether to return the mask used instead of the clip

    :return:                An error-corrected clip in the input resolution when pass2=False, or
                            a reupscaled clip in the input resolution when pass2=True.
                            Output depth will be the same as input depth.
    """
    if not descaler:
        descaler = core.descale.Debicubic
    depth_in = vsutil.get_depth(clip)
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
    pre_descale = core.std.Expr([diff_a,diff_b,y,cy], 'x y - 1000 > x 2500 > and z a ?')

    descaled = descaler(pre_descale, width=vsutil.get_w(height, clip.width/clip.height), height=height, b=b, c=c)
    doubled = rpow2(descaled, correct_shift=correct_shift).resize.Spline36(clip.width, clip.height)
    if apply_mask:
        mask = detail_mask(y, doubled, thresh=mask_thresh) if not ext_mask else ext_mask
        if return_mask: return mask
        doubled = core.std.MaskedMerge(doubled, y, mask)
    if chroma: doubled = vsutil.join([doubled,u,v])
    return vsutil.depth(doubled, depth_in)
