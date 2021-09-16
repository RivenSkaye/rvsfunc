""" Edgecase functions that were generalized for if I ever need them again.

Most of these functions should not be used in the general use case. They're
typically written for a very specific edgecase, but generalized for if I ever
need them again. Currently only holds `questionable_rescale` which I mangled
from someone else's code that had a very similar edgecase.
"""

from typing import Any, Dict, Callable, Optional
from .masking import detail_mask
import vsutil
import vapoursynth as vs
core = vs.core


def nnedi3_rpow2(clip: vs.VideoNode, rfactor: int = 2, shift: bool = True,
                 cl: bool = False,
                 nnedi: Optional[Callable[[vs.VideoNode, int, Any], vs.VideoNode]] = None,  # noqa: E501
                 nsize: int = 0, nns: int = 3,
                 **kwargs: Dict[str, Any]
                 ) -> vs.VideoNode:

    """ nnedi3_rpow2, increasing frame dimensions by powers of 2 using NNEDI3.

    Aims to replace the old nnedi3_rpow2 by being a resolvable dependency and
    not providing most of the standard NNEDI args due to them remaining default.
    Lists non-default arguments and adds an optional argument to enable use
    of OpenCL.
    Uses ``core.resize.Spline36`` for chroma shift correction, if applicable.

    :param clip:        YUV input clip. You'll get the same depth back.
    :param rfactor:     The factor with which to increase the size, must be
                        a power of 2 or an error will be raised.
    :param shift:       Whether or not to correct the chroma shift caused
                        by NNEDI3.
    :param cl:          Whether or not to use the OpenCL version of NNEDI3.
                        Overrides the ``nnedi`` parameter.
    :param nnedi:       The NNEDI3 plugin or function to use. Tries to default
                        to vanilla NNEDI3, falls back on ZNEDI3.
    :param nsize:       Same as for the NNEDI3 plugins, but defaults to 0.
    :param nns:         Same as for the NNEDI3 plugins, but defaults to 0.
    :param kwargs:      Any other keyword arguments passed to this function
                        will be passed to the NNEDI3 plugin blindly.
                        Uses all of the defaults for the plugins, with the
                        exceptions of:
                        - ``dh`` will always be true.
                        - ``field`` is 1 for horizontal passes, the first pass,
                        and 0 for all others. Always 0 for ``cl`` after
                        the first pass is finished.
                        - ``dw`` when ``cl`` is set to True.
                        - ``opt`` is set to True.
                        *kwargs are used to update the dict after setting
                        these values and can be overwritten. Field is determined
                        when making the call to NNEDI3 and can't be overwritten*
    """

    # Check the clip format to prevent issues and bullshittery.
    if clip.format is not None and clip.format.color_family not in [vs.GRAY, vs.YUV]:  # noqa: E501
        raise vs.Error("rpow2 only takes constant format YUV clips, \
                        please fix your input and try again.")

    # Check if the rfactor is within the legal ranges
    if rfactor < 2 or rfactor > 1024:
        raise vs.Error("The rfactor parameter must be between 2 and 1024")

    # Check if the rfactor is a power of 2. The beauty of this lies in powers
    # of 2 always having exactly one bit that's 1, so a bitwise AND operation
    # will return a non-zero value for anything that isn't a power of 2.
    if rfactor & (rfactor-1) != 0:
        raise vs.Error("The rfactor must be a power of 2!")

    # Select an NNEDI3 plugin
    if cl:
        nnedi = core.nnedi3cl.NNEDI3CL
    elif nnedi is None:
        if hasattr(core, "nnedi3"):
            nnedi = core.nnedi3.nnedi3
        elif hasattr(core, "znedi3"):
            nnedi = core.znedi3.nnedi3
        else:
            raise vs.Error("None of the usual NNEDI3 plugins was found, please \
                            supply one with the 'nnedi' kwarg or install one.")
    # Set up the kwargs dict
    nnedi_kwargs = {
        "clip": clip,
        "dh": True,
        "nsize": nsize,
        "nns": nns,
        "opt": True
    }
    if cl:
        nnedi_kwargs.update(dw=True)
    nnedi_kwargs.update(kwargs)
    depth_in = clip.format.bits_per_sample  # type: ignore
    sample_in = clip.format.sample_type  # type: ignore

    def _double(vid: vs.VideoNode, src_width: int,
                nn: Callable[..., vs.VideoNode], fix: bool, opencl: bool,
                args: Dict
                ) -> vs.VideoNode:
        doubled = nn(vid, field=0, **args)
        if fix:
            shiftval = 0.5+(0.25 - (vid.width/(vid.width*2))) if vid.width == src_width/2 else 0.5  # noqa: E501
            if opencl:
                shift_v = 0.5+(0.25 - (vid.height/(vid.height*2))) if vid.width == src_width/2 else 0.0  # noqa: E501
            else:
                shift_v = 0.0
            return doubled.resize.Spline36(src_left=shiftval, src_top=shift_v)
        return doubled

    # Calulate how many times we have to run this thing
    count = 0
    while 2**count < rfactor:
        count += 1

    for _ in range(count):
        planes = vsutil.split(clip)
        shifted = [_double(p, clip.width, nnedi, shift, cl, nnedi_kwargs) for p in planes]  # noqa: E501
        if not cl:  # Handle width if we're not using NNEDI3CL for it
            shifted = [s.std.Transpose() for s in shifted]
            shifted = [_double(s, clip.width, nnedi, shift, cl, nnedi_kwargs) for s in shifted]  # noqa: E501
            shifted = [s.std.Transpose() for s in shifted]
        clip = vsutil.join(shifted)
    return vsutil.depth(clip, depth_in, sample_type=sample_in)


def questionable_rescale(
    clip: vs.VideoNode, height: int, b: float = 1/3, c: float = 1/3,
    descaler: Callable[[vs.VideoNode, int, int, Any], vs.VideoNode] = core.descale.Debicubic,  # noqa: E501
    scaler: Optional[Callable[[vs.VideoNode, int, int], vs.VideoNode]] = core.resize.Spline36,  # noqa: E501
    scale_kwargs: Dict = {"height": None}, correct_shift: bool = True,
    apply_mask: bool = True, mask_thresh: float = 0.05,
    ext_mask: Optional[vs.VideoNode] = None, depth_out: int = -1,
    return_mask: bool = False) -> vs.VideoNode:  # noqa:E125

    """ Rescale function by Zastin for Doga Kobo, edited for reusability.

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
                            will be passed to ``vsutil.depth`` the way they are
                            with no regards to what may be raised.
    :param return_mask:     Whether to return the mask used instead of the clip.
                            This requires ``scaler`` to not be None.
    """

    if clip.width == 0 or clip.height == 0:
        raise vs.Error("questionable_descale: var-res clips are not supported. \
                       Please slice the clip into several same-res clips or \
                       descale in another way.")
    if scale_kwargs.get("width") is None:
        scale_kwargs["width"] = clip.width
    if scale_kwargs.get("height") is None:
        scale_kwargs["height"] = clip.height
    depth_out = vsutil.get_depth(clip) if depth_out < 0 else depth_out
    if vsutil.get_depth(clip) > 16 or clip.format.sample_type == vs.FLOAT:  # type: ignore  # noqa: E501
        clip = vsutil.depth(clip, 16, sample_type=vs.INTEGER)
    rgv = core.rgvs.RemoveGrain(clip, mode=1)
    clamp = vsutil.depth(rgv, 32, dither_type="none")
    clip = vsutil.depth(clip, 32, dither_type="none")
    chroma = clip.format.num_planes > 1  # type: ignore

    if chroma:
        y, u, v = vsutil.split(clip)
        cy, cu, cv = vsutil.split(clamp)
    else:
        y = clip
        cy = clamp

    descy = descaler(y, width=vsutil.get_w(height, clip.width/clip.height), height=height, b=b, c=c)  # type: ignore  # noqa: E501
    desccy = descaler(cy, width=vsutil.get_w(height, clip.width/clip.height), height=height, b=b, c=c)  # type: ignore  # noqa: E501

    err = descy.resize.Bicubic(clip.width, clip.height, filter_param_a=b, filter_param_b=c)  # noqa: E501
    diff_a = core.std.Expr([y, err], "x y - abs")
    cerr = desccy.resize.Bicubic(clip.width, clip.height, filter_param_a=b, filter_param_b=c)  # noqa: E501
    diff_b = core.std.Expr([cy, cerr], "x y - abs")
    pre_descale = core.std.Expr([diff_a, diff_b, y, cy], f"x y - {1000/(1<<16)-1} > x {2500/(1<<16)-1} > and z a ?")  # noqa: E501

    descaled = descaler(pre_descale, width=vsutil.get_w(height, clip.width/clip.height), height=height, b=b, c=c)  # type: ignore  # noqa: E501
    if not scaler:
        return descaled
    doubled = nnedi3_rpow2(descaled, shift=correct_shift, cl=True)
    doubled = scaler(doubled, **scale_kwargs)  # type: ignore
    if apply_mask:
        mask = detail_mask(y, doubled, thresh=mask_thresh) if not ext_mask else ext_mask  # noqa: E501
        if return_mask:
            return mask
        doubled = core.std.MaskedMerge(doubled, y, mask)
    if chroma:
        doubled = vsutil.join([doubled, u, v])
    return vsutil.depth(doubled, depth_out)
