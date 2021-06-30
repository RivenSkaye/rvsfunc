import vapoursynth as vs
from functools import partial
import vsutil
from typing import Any, Dict, Callable, Optional
from math import floor
core = vs.core

def nc_splice(source: vs.VideoNode, nc: vs.VideoNode, startframe: int, endframe: int,
              nc_filterfunc: Optional[Callable[[vs.VideoNode, Any], vs.VideoNode]]=None,
              use_internal: bool=False, ext_mask: Optional[vs.VideoNode]=None, **kwargs) -> vs.VideoNode:
    """ Function for splicing in video from a different source.

    The intended purpose is to splice NCs into an episode when they look better
    or when they're easier to filter. Allows for copying over the credits.

    :param source:          The source clip that needs something replaced
    :param nc:              The clip that needs to be spliced into source
    :param startframe:      The frame to start splicing at. This is an inclusive
                            selection value. The selected range is `source[:startframe+1]`.
    :param endframe:        The first frame that needs to be kept. This is an
                            inclusive selection value, selected as `source[endframe:]`.
    :param nc_filterfunc:   Optional function to call on the input video for
                            filtering before splicing it in.
    :param use_internal:    Whether or not to use `copy_credits` from this script.
                            Mutually exclusive with `nc_filterfunc`.
    :param ext_mask:        For when the internal merging function is good enough
                            but the mask it generates isn't. This is only used
                            if `use_internal` applies.
    """
    if nc_filterfunc:
        nc = nc_filterfunc(nc, **kwargs)
    elif use_internal:
        nc = copy_credits(source[startframe:endframe+1], nc, ext_mask)
    out = source[:startframe+1] + nc + source[endframe:]
    return out

def copy_credits(source: vs.VideoNode, nc: vs.VideoNode, mask: Optional[vs.VideoNode]=None) -> vs.VideoNode:
    """ Copy credits from source to the nc using a mask.

    This function internally calls `detail_mask` which is meant for descales.
    As such, it assumes the NC doesn't have major differences with the source
    as they are provided. Assumes both inputs have the same length.

    :param source:      The clip to take the credits from.
    :param nc:          The NC to copy the credits into.
    :param mask:        Optional, an external mask to use.
    """
    mask = detail_mask(source, nc) if not mask else mask
    return core.std.MaskedMerge(nc, source, mask)

# Immediately make a credit mask
def Scradit_mask(luma: vs.VideoNode, b: float=1/3, c: float=1/3,
                 height: int=720, absthresh: float=0.060, iters: int=4,
                 descaler: Callable[[vs.VideoNode, Any], vs.VideoNode]=None,
                 upscaler: Callable[[vs.VideoNode, Any], vs.VideoNode]=None,
                 dekwargs: dict={}, upkwargs: dict={}) -> vs.VideoNode:
    """ Credit masking function borrowed from Scrad.

    Changed it to be used in a more generic manner, but the core stuff and
    math comes from him. Or wherever he got it.
    Returns a 32 bit (GrayS) mask.

    :param luma:        Luma plane of the input video. If it has more planes,
                        the luma plane will be extracted.
    :param b:           b value for the descaler, defaults to 1/3.
    :param c:           c value for the descaler, defaults to 1/3.
    :param height:      The height to descale to for a correct error rate.
    :param absthresh:   The abs threshold for binarizing the mask with.
    :param iters:       How often to iterate Maximum and Inflate calls on the mask.
    :param descaler:    The descaling function to use, defaults to Debicubic.
    :param upscaler:    The upscaling function, defaults to Bicubic.
    :param dekwargs:    A dict with extra options for the descaler.
    :param upkwargs:    A dict with extra options for the upscaler.
    """
    luma = vsutil.get_y(luma)
    luma = vsutil.depth(luma, 32)
    descaler = core.descale.Debicubic if not descaler else descaler
    upscaler = core.resize.Bicubic if not upscaler else upscaler
    descaled = descaler(luma, vsutil.get_w(height, luma.width/luma.height), height, b=b, c=c, **dekwargs)
    rescaled = upscaler(descaled, luma.width, luma.height, **upkwargs)
    mask = core.std.Expr([luma, rescaled], f'x y - abs {absthresh} < 0 1 ?')
    mask = vsutil.iterate(mask, core.std.Maximum, iters)
    mask = vsutil.iterate(mask, core.std.Inflate, iters)
    return mask

def detail_mask(source: vs.VideoNode, rescaled: vs.VideoNode, thresh: float=0.05) -> vs.VideoNode:
    """ Generates a fairly basic detail mask, mostly for descaling purposes.

    This is mostly used to pick up on detail _lost_ in `questionable_descale` as
    per Zastin's original script. Catches most if not all elements in a different
    native resolution

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
    :param maskgen:     The function to call for making the mask, default Prewitt.
    :param iter_out:    Amount of times to iterate expansion for the outer mask
                        Defaults to 2, the standard size
    :param iter_in:     Amount of times to iterate impansion for the inner mask
                        Defaults to `iter_out+1`.
    :param inner:       Returns the inner mask for checking.
    :param outer:       Returns the outer mask for checking.
    :param mask_args:   Expanded as **kwargs for `mask_gen`
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

def fineline_mask(clip: vs.VideoNode, thresh: int=95):
    """ Generates a very fine mask for lineart protection. Not perfect yet
    The generated mask is GRAY8, keep this in mind for conversions.

    :param clip:        The clip to generate the mask for.
    :param thresh:      The threshold for the binarization step.
    """
    prew = core.std.Prewitt(clip, planes=[0])
    thin = core.std.Minimum(prew)
    yp = vsutil.get_y(prew)
    yt = vsutil.get_y(thin)
    maska = core.std.Expr([ys, yt], ["x y < y x ?"])
    bin_mask = core.std.Binarize(maska, threshold=thresh)
    redo = int(floor(thresh/2.5)*2)
    mask_out = core.std.Expr([bin_mask, mask_a], [f"x y < y x ? {pass2} < 0 255 ?"])
    return mask_out

def questionable_rescale(
    clip: vs.VideoNode, height: int, b: float=1/3, c: float=1/3,
    descaler: Callable[[vs.VideoNode, Any], vs.VideoNode]=None,
    correct_shift: bool=True, apply_mask: bool=True, mask_thresh: float=0.05,
    ext_mask: vs.VideoNode=None, return_mask: bool=False) -> vs.VideoNode:
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
    :param correct_shift:   Same as in `nnedi3_rpow2`.
    :param apply_mask:      Whether or not to apply a detail mask.
    :param mask_thresh:     Threshold for binarizing the default mask.
    :param ext_mask:        Supply your own mask instead of the default.
    :param return_mask:     Whether to return the mask used instead of the clip.
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

def chromashifter(clip: vs.VideoNode, horizontal: bool=True, vertical: bool=False, diagonal: bool=False) -> vs.VideoNode:
    """ Automatically fixes chroma shifts, at the very least by approximation.

    This function takes in a clip and first upscales chroma to YUV444P8, then
    it proceeds to supersample the clip x4. Then edgemasks are generated over
    the separated planes. Then the shifts are calculated on a frame by frame
    basis and applied on the original input clip. The rest of the video remains
    completely untouched.
    Assumes the shift is the same for the U and V planes.

    :param clip: vs.VideoNode:  The clip to process. This may take a while.
    :return: vs.VideoNode:      The input clip, but without chroma shift.
    """
    def _getWhiteRows(frameArr):
        whites = {}
        r = 0
        for row in frameArr:
            p = 0
            for pixel in row:
                if pixel > 31:
                    whites[r] = p
                    break # We only want the first white in the row
                p += 1
            r += 1
        return whites

    def _getWhiteInRow(frameArr, row):
        p = 0
        for pixel in frameArr[row]:
            if pixel > 31: return p
            p += 1
        return -1

    def _eval(n, f, yOG, uOG, vOG):
        print(f"Frame {n+1}")
        ya = f[0].get_read_array(0)
        ua = f[1].get_read_array(0)
        va = f[2].get_read_array(0)
        yWC = _getWhiteRows(ya)
        rows = yWC.keys()
        shifts = []
        for r in rows:
            uWC = _getWhiteInRow(ua, r)
            vWC = _getWhiteInRow(va, r)
            try: # some edgecase frames produce 0 divisions
                if uWC > -1:
                    shifts.append(256/round(32*(((uWC-yWC[r])+1)/8)))
                elif vWC > -1:
                    shifts.append(256/round(32*(((uWC-yWC[r])+1)/8)))
            except:
                continue
        try:
            shift = (sum(shifts)/len(shifts))
            if shift > 2 or shift < -2:
                corr = round(shift)/1
                shift = shift-corr
        except:
            shift = 0
        thisY = yOG
        thisU = uOG.resize.Point(src_left=shift)
        thisV = vOG.resize.Point(src_left=shift)
        thisFrame = vsutil.join([thisY, thisU, thisV])
        return thisFrame

    yOG, uOG, vOG = vsutil.split(clip)
    yuv = clip.resize.Spline36(height=clip.height*4, width=clip.width*4, format=vs.YUV444P8)
    y, u, v = vsutil.split(yuv)
    ymask = y.std.Prewitt()
    umask = u.std.Prewitt()
    vmask = v.std.Prewitt()

    if diagonal:
        raise vs.Error("chromashifter: Finding diagonal shifts is hell, so no way!")
    if horizontal and vertical:
        print("There is no guarantee that bidirectional will work. \
                       You'd be best off doing one direction manually first.")

    if horizontal:
        out = clip.std.FrameEval(partial(_eval, yOG=yOG, uOG=uOG, vOG=vOG),
                                 prop_src=[ymask, umask, vmask])
    else: out = clip
    if vertical:
        out = out.std.Transpose()
        out = out.std.FrameEval(partial(_eval, yOG=yOG, uOG=uOG, vOG=vOG),
                                 prop_src=[ymask, umask, vmask]).std.Transpose()
    return out
