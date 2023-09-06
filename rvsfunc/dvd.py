"""
Functions written specifically for issues common or exclusive to DVDs.

DVDs, ancient as the specs and carriers are, come with their fair share of
typical issues. Some of the more well-known problems are things like getting
telecined before editing, chroma shifts that change from scene to scene and
other grievances that stem from processing the things in several steps or
by several subcontractors. They're generally a pain in the ass and this
module exists to alleviate some of that pain.
"""

from enum import Enum
from functools import partial
from math import floor
from typing import Any, Callable, Dict, Optional

import numpy as np
import vapoursynth as vs
import vsutil

from .errors import VariableFormatError, VariableResolutionError, YUVError
from .masking import eoe_convolution
from .NNEDI3 import ZNEDI3
from .utils import frame_to_array


core = vs.core

__all__ = [
    "Region", "chromashifter", "square43PAR"
]


class Region(Enum):
    """
    An enum for specifying regional coding standards.

    This enum specifies the regional standards used for TV and DVD material.
    The PAL and SECAM systems do not have any notable difference with regards to
    (inverse) telecining, cropping, resizing and other size ratios, but they do
    follow different standards for analog processing and it _might_ mean slightly
    different primaries and an alternate white point as defined in BT.407/601 (BG).

    Will be expanded upon to include variations of the standards like PAL-M and
    NTSC-J at some point. Will also be moved to a utility package at some point.
    """

    UNKNOWN = 0
    NTSC = 1
    PAL = 2
    SECAM = 3


def chromashifter(
    clip: vs.VideoNode, wthresh: int = 31, vertical: bool = False,
    maskfunc: Callable[[vs.VideoNode], vs.VideoNode] = eoe_convolution,
    mask_kwargs: Dict = {},
    shifter: Callable[[vs.VideoNode, Any], vs.VideoNode] = core.resize.Bicubic
) -> vs.VideoNode:
    """
    Automatically fixes chroma shifts, at the very least by approximation.

    This function takes in a clip and scales it to a 4x larger YUV444P clip.
    It then generates edgemasks over all of the planes to be used in distance
    calculations to figure out the proper value to shift chroma with.
    The shift is applied to the otherwise untouched input clip.
    Assumes the shift is the same for the U and V planes.
    Actually fast now thanks to EoE :eoehead:

    :param clip: vs.VideoNode:  The clip to process. This may take a while.
    :param wthresh: int:        The threshold for white values to use in the
                                calculations for proper shifting.
                                Valid values are 1 through 255.
    :param vertical: bool:      Whether or not to perform the shift vertically.
                                This internally calls ``core.std.Transpose`` so
                                that horizontal logic can be applied for speed.
    :param maskfunc: Callable   A custom function or plugin to call for the
                                edgemask. Default ``core.std.Prewitt``.
    :param mask_kwargs: Dict    A dictionary of kwargs to be expanded for
                                mask_func. If defaults are used, this will be
                                padded with Prewitt's planes arg to ensure all
                                planes get a mask generated over them.
    :param shifter: Callable:   The function to perform the chromashift with,
                                defaults to core.resize.Point.
                                This MUST take the clip as its first positional
                                argument and a kwarg named ``src_left``.
                                Wrap your callable if it doesn't meet these
                                requirements to prevent errors.
    :return: vs.VideoNode:      The input clip, but without chroma shift.
    """

    _fname = "rvsfunc chromashifter:"

    if not clip.format:
        raise VariableFormatError(_fname)

    if clip.format.color_family is not vs.YUV:
        raise YUVError(_fname)

    shifted_clips: Dict[float, vs.VideoNode] = {0: clip}

    def get_shifted(n: int, f: vs.VideoFrame) -> vs.VideoNode:
        array = frame_to_array(f)
        array_above = array > wthresh
        row_first = np.argmax(array_above, axis=1)
        shifts = []
        for row, luma_col in enumerate(row_first[:, 0]):
            def _calc_shift(val: int) -> float:
                return 256 / round((wthresh + 1) * (((first - luma_col) + 1) / 8))

            if not array_above[row, luma_col, 0]:
                continue
            try:  # some edgecase frames produce 0 divisions
                first, second = row_first[row, 1], row_first[row, 2]

                if (
                    array_above[row, first, 1] and first <= second
                ):
                    shifts.append(_calc_shift(first))
                    continue
                if array_above[row, second, 2]:
                    shifts.append(_calc_shift(second))
            except ZeroDivisionError:
                continue

        try:
            shift = sum(shifts) / len(shifts)
            if shift > 2 or shift < -2:
                shift = shift - (floor(shift) / 2)
        except ZeroDivisionError:
            shift = 0

        shift = round(shift * 8) / 8
        shifted = shifted_clips.get(shift)

        if shifted is None:
            shifted = shifter(clip, src_left=shift)  # type: ignore
            shifted_clips.update({shift: shifted})

        return shifted

    if vertical:
        clip = core.std.Transpose(clip)

    yuv = clip.resize.Spline36(
        height=clip.height * 4, width=clip.width * 4, format=vs.YUV444P8
    )

    if maskfunc is core.std.Prewitt:
        mask_kwargs["planes"] = [0, 1, 2]

    yuv = maskfunc(yuv, **mask_kwargs)

    out = core.std.FrameEval(clip, get_shifted, yuv)
    out = core.std.ShufflePlanes([clip, out], [0, 1, 2], vs.YUV)

    return out.std.Transpose() if vertical else out


def PAR_43_480(
    clip: vs.VideoNode,
    fractional: bool = False,
    scaler: Optional[Callable[[vs.VideoNode, int, int], vs.VideoNode]] = None
) -> vs.VideoNode:
    """
    Conversion from DVD squeeze to glorious 4:3 by vertically resizing.

    This function is NOT meant to blindly push telecined material into pre-IVTC.
    It also doesn't handle interlaced material. The funcion assumes input to be
    properly (or best effort) restored progressive material. It just resizes the
    input video material to fix the Pixel Aspect Ratio. And instead of downscaling
    any dimension, it stretches video and crops excess video. This *should* also
    take care of removing the typical "dirty lines" on DVDs near the sides.

    This function works on the assumption that the PAR adheres to the MPEG idea
    of digitizing for 480 using a 10/11 ratio for pixel sizes. This results in
    the typical frame dimensions you'd see in NTSC material.
    Numbers used here are the ones from the standard and actual processing is done
    with calculated results from the input video.

    :param clip:        The deinterlaced/IVTC'd video to adjust the PAR on.
    :param fractional:  Whether or not to allow resolutions resulting in fractional
                        results. This will cause very slight under- or overstretching
                        and is therefore disabled by default.
                        Turning this on turns (D)VITC cropping OFF!
    :param scaler:      Optional scaling function to use. Defaults to Catmull-Rom
                        ``(Bicubic, b=0, c=0.5)`` and no custom arguments are
                        supported, so it's recommended to use a wrapped callable.
                        Called as ``scaler(clip, width, height)`` where:

                        - clip: vs.VideoNode
                        - width: int
                        - height: int
                        - returning vs.VideoNode
    """
    fn = "PAR_43_480"
    if not clip.height or not clip.width:
        raise VariableResolutionError(fn)
    if not clip.format:
        raise VariableFormatError(fn)

    # There's sometimes 6 lines of (Digital) Vertical Intercal Timecode data.
    # Most notably on digitized tape and film, DVDs usually don't have it in the
    # final product. That's why DVDs aren't 486i/p but 480i/p usually.
    if not fractional:
        if (clip.height - 6) % 480 == 0:
            clip = clip.std.Crop(0, 0, 6, 0)
        elif clip.height % 486 == 0:
            dvitc = (clip.height // 486) * 6
            clip = clip.std.Crop(0, 0, dvitc, 0)

    newheight = clip.height / (10 / 11)
    if not newheight.is_integer() and not fractional:
        raise ValueError(f"{fn}: Calculated target height ({newheight}) is not an "
                         "integer resolution!")
    vres = newheight.__ceil__() if newheight % 2 > 1.0 else newheight.__floor__()
    if vres % 2 == 1:
        vres += 1
    cropmult = (clip.width / 720).__ceil__()
    cropwidth = 8 * cropmult
    if not scaler:
        scaler = partial(core.resize.Bicubic, filter_param_a=0, filter_param_b=0.5)
    return scaler(clip, clip.width, vres).std.Crop(cropwidth, cropwidth, 0, 0)


def PAR_43_576(
    clip: vs.VideoNode,
    fractional: bool = False,
    scaler: Optional[Callable[[vs.VideoNode, int, int], vs.VideoNode]] = None,
    cscaler: Optional[Callable[[vs.VideoNode, int, int], vs.VideoNode]] = None
) -> vs.VideoNode:
    """
    Conversion from DVD squeeze to glorious 4:3 by horizontally resizing.

    This function is NOT meant to blindly push telecined material into pre-IVTC.
    It also doesn't handle interlaced material. The funcion assumes input to be
    properly (or best effort) restored progressive material. It just resizes the
    input video material to fix the Pixel Aspect Ratio. And instead of downscaling
    any dimension, it stretches video and crops excess video. This *should* also
    take care of removing the typical "dirty lines" on DVDs near the sides.

    This function works on the assumption that the PAR adheres to the MPEG idea
    of digitizing for 576 using a 59/54 ratio for pixel sizes. This results in
    the typical frame dimensions you'd see in PAL material.
    Fractional resolutions are avoided by processing as YUV444, keep this in mind!
    Numbers used here are the ones from the standard and actual processing is done
    with calculated results from the input video.

    :param clip:        The deinterlaced/IVTC'd video to adjust the PAR on.
    :param fractional:  Whether or not to allow resolutions resulting in fractional
                        results. This will cause very slight under- or overstretching
                        and is therefore disabled by default.
                        Turning this on prevents the addition of a 1px black bar,
                        which would otherwise be required to prevent problematic
                        frame dimensions, as the usual way to fix 576 width video
                        involves stretching the width to 786 2/3 and then cropping.
                        The alternative is to crop to 702 first and then resizing
                        to a width of 767, which is where the padding comes in.
    :param scaler:      Optional scaling function to use. Defaults to Catmull-Rom
                        ``(Bicubic, b=0, c=0.5)`` and no custom arguments are
                        supported, so it's recommended to use a wrapped callable.
                        Called as ``scaler(clip, width, height)`` where:

                        - clip: vs.VideoNode
                        - width: int
                        - height: int
                        - returning vs.VideoNode
    :param cscaler:     Only used when ``fractional`` is false. Used for scaling
                        down the chroma back to 420. Same requirements as the
                        ``scaler`` arg. If you wish to get 444 material back,
                        pass ``lambda x, y, z: x``
    """
    fn = "PAR_43_576"
    if not clip.height or not clip.width:
        raise VariableResolutionError(fn)
    if not clip.format:
        raise VariableFormatError(fn)

    if not scaler:
        scaler = partial(core.resize.Bicubic, filter_param_a=0, filter_param_b=0.5)
    if not cscaler:
        cscaler = partial(core.resize.Bicubic, filter_param_a=0, filter_param_b=0)

    if not fractional:
        cropmult = clip.width // 720
        wcrop = 9 * cropmult  # Crop to 702, 720 - 702 = 18, 18 / 2 = 9
        chroma = [
            ZNEDI3.rpow2(p, False, shift=False)
            for p in vsutil.split(clip)[1:]
        ]
        clip = vsutil.join([vsutil.get_y(clip), *chroma])
        cropped = clip.std.Crop(wcrop, wcrop, 0, 0)
        newwidth = clip.width * (59 / 54)
        if not newwidth.is_integer():
            raise ValueError(f"{fn}: Calculated target width ({newwidth}) is not an "
                             "integer resolution!")
        hres = int(newwidth)
        stretched = scaler(cropped, hres, clip.height)
        if stretched.width % 2 == 1:
            stretched = stretched.std.AddBorders(1, 0, 0, 0)
        chroma = [
            cscaler(p, stretched.width // 2, stretched.height // 2)
            for p in vsutil.split(stretched)[1:]
        ]
        return vsutil.join([vsutil.get_y(stretched), *chroma])

    newwidth = clip.width * (59 / 54)
    wres = newwidth.__ceil__() if newwidth % 2 > 1.0 else newwidth.__floor__()
    if wres % 2 == 1:
        wres += 1
    cropmult = (newwidth / (720 * (59 / 54))).__ceil__()
    lcrop = rcrop = 9 * cropmult
    if lcrop % 2 == 1:
        lcrop -= 1
        rcrop += 1
    return scaler(clip, wres, clip.height).std.Crop(lcrop, rcrop, 0, 0)


def square43PAR(
    clip: vs.VideoNode,
    region: Region = Region.UNKNOWN,
    scaler: Optional[Callable[[vs.VideoNode, int, int], vs.VideoNode]] = None,
    ntsc_down: bool = False
) -> vs.VideoNode:
    """
    A function to resize non-square PAR to square PAR in the cleanest way possible.

    Fixing PAR is hell and doing so is *NEVER* recommended! Unless a project has
    constraints that require you to, in which case having a function that follows
    the proper standards is a very nice thing to have.

    This function expects IVTC'd or deinterlaced video that has no other resizing
    or modification applied to it. As such, it does not yet handle input resolutions
    other than 704x480, 720x480, 704x486, 720x486, 768x576, or 720x576.
    Support for arbitrary resolutions will be added soon!

    Resamples video to make sure the resulting PAR is 1:1 again, or as close as
    possible given the circumstances. It does this through **stretching** the
    undersampled dimension rather than squeezing the other, in an attempt
    to prevent loss of data.
    For NTSC with 640x480 resolutions, a boolean flag is available to downsample
    the width instead, although this is not recommended. For reference, media players
    don't honor these resolutions either, they stretch as well.
    If the resulting resolution is fractional, it will be rounded to the
    nearest legal integer value, which means there will never be more than 1px
    difference between a perfect 1:1 PAR and the result.
    If the input video has subsampling applied, odd values are considered the
    same as fractional, and it will be resized to ``Res - 1`` instead.

    :param clip:        Input video node that needs its PAR corrected.
    :param region:      The coding standards region to use, one of the values
                        available in the :class:`Region` enum.
    :param scaler:      Optional scaling function to use. Defaults to Catmull-Rom
                        ``(Bicubic, b=0, c=0.5)`` and no custom arguments are
                        supported, so it's recommended to use a wrapped callable.
                        Called as ``scaler(clip, width, height)`` where:

                        - clip: vs.VideoNode
                        - width: int
                        - height: int
                        - returning vs.VideoNode
    """
    if not clip.width or not clip.height:
        raise VariableResolutionError("square43PAR")

    if clip.width not in [704, 720] or clip.height not in [480, 486, 576]:
        raise ValueError("Resolution is not yet supported! "
                         f"({clip.width}x{clip.height})")

    region = Region(region)
    if region is Region.UNKNOWN:
        region = Region.PAL if clip.height == 576 else Region.NTSC

    cropfirst = region is Region.NTSC

    if scaler is None:
        scaler = partial(core.resize.Bicubic, filter_param_a=0, filter_param_b=0.5)

    if cropfirst:
        if clip.height == 486:
            clip = clip.resize.Point(
                clip.width, clip.height, src_top=3
            ).std.Crop(left=0, right=0, top=0, bottom=6)
        if clip.width == 720:
            clip = clip.std.Crop(left=8, right=8, top=0, bottom=0)

        return scaler(clip,
                      clip.width if not ntsc_down else 640,
                      528 if not ntsc_down else 480)
    elif clip.width == 704:
        clip = clip.std.AddBorders(left=8, right=8, top=0, bottom=0)

    return scaler(clip, 768, clip.height).std.Crop(
        left=32, right=32, top=24, bottom=24
    )
