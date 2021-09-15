""" Functions written specifically for issues common or exclusive to DVDs.

DVDs, ancient as the specs and carriers are, come with their fair share of
typical issues. Some of the more well-known problems are things like getting
telecined before editing, chroma shifts that change from scene to scene and
other grievances that stem from processing the things in several steps or
by several subcontractors. They're generally a pain in the ass and this
module exists to alleviate some of that pain.
"""

from .masking import eoe_convolution
from typing import Callable, Dict, Any
from math import floor
import numpy as np
import vapoursynth as vs
core = vs.core


def chromashifter(clip: vs.VideoNode, wthresh: int = 31, vertical: bool = False,
                  maskfunc: Callable[[vs.VideoNode], vs.VideoNode] = eoe_convolution,  # noqa: E501
                  mask_kwargs: Dict = {},
                  shifter: Callable[[vs.VideoNode, Any], vs.VideoNode] = core.resize.Point  # noqa: E501
                  ) -> vs.VideoNode:
    """ Automatically fixes chroma shifts, at the very least by approximation.

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
        raise vs.Error(f"{_fname} The clip must have a constant format. \
                        Please convert or split the clip.")
    if clip.format.color_family is not vs.YUV:
        raise vs.Error(f"{_fname} The clip MUST be of the YUV color family. \
                       Please convert it before calling this function.")
    if clip.format.num_planes < 3:
        raise vs.Error(f"{_fname} This function requires all three planes in \
                       order to calculate proper shifts.")

    def frame_to_array(frame: vs.VideoFrame) -> np.ndarray:
        frame_array = []
        for plane in range(frame.format.num_planes):
            plane_array = np.array(frame.get_read_array(plane), copy=False)
            frame_array.append(plane_array.reshape(list(plane_array.shape) + [1]))  # noqa: E501
        return np.concatenate(frame_array, axis=2)

    shifted_clips: Dict[float, vs.VideoNode] = {0: clip}

    def get_shifted(n: int, f: vs.VideoFrame) -> vs.VideoNode:
        array = frame_to_array(f)
        array_above = array > wthresh
        row_first = np.argmax(array_above, axis=1)
        shifts = []
        for row, luma_col in enumerate(row_first[:, 0]):
            if not array_above[row, luma_col, 0]:
                continue
            try:  # some edgecase frames produce 0 divisions
                if (
                    array_above[row, row_first[row, 1], 1] and
                    row_first[row, 1] <= row_first[row, 2]
                ):
                    shifts.append(
                        256 / round((wthresh + 1) * (((row_first[row, 1] - luma_col) + 1) / 8))  # noqa: E501
                    )
                    continue
                if array_above[row, row_first[row, 2], 2]:
                    shifts.append(
                        256 / round((wthresh + 1) * (((row_first[row, 2] - luma_col) + 1) / 8))  # noqa: E501
                    )
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
    yuv = clip.resize.Spline36(height=clip.height * 4, width=clip.width * 4,
                               format=vs.YUV444P8)
    if maskfunc is core.std.Prewitt:
        mask_kwargs["planes"] = [0, 1, 2]
    yuv = maskfunc(yuv, **mask_kwargs)  # type: ignore

    out = core.std.FrameEval(clip, get_shifted, yuv)
    out = core.std.ShufflePlanes([clip, out], [0, 1, 2], vs.YUV)
    return out.std.Transpose() if vertical else out
