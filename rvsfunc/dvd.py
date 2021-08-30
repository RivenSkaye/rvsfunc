from typing import Callable, Dict, Any
from math import floor
import numpy as np
import vsutil
import vapoursynth as vs
core = vs.core

def eoe_convolution(clip: vs.VideoNode):
    return clip.std.Convolution(matrix=[-1] * 4 + [8] + [-1] * 4,
                 planes=[0, 1, 2], saturate=False)

def chromashifter(clip: vs.VideoNode, wthresh: int = 31, vertical: bool = False,
                  maskfunc: Callable[[vs.VideoNode, Any], vs.VideoNode]=eoe_convolution,
                  mask_kwargs: Dict={},
                  shifter: Callable[[vs.VideoNode, Any], vs.VideoNode]=core.resize.Point
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
                                This internally calls `core.std.Transpose` so
                                that horizontal logic can be applied for speed.
    :param maskfunc: Callable   A custom function or plugin to call for the
                                edgemask generation. Default `core.std.Prewitt`.
    :param mask_kwargs: Dict    A dictionary of kwargs to be expanded when calling
                                mask_func. If defaults are used, this will be
                                padded with Prewitt's planes arg to ensure all
                                planes get a mask generated over them.
    :param shifter: Callable:   The function to perform the chroma shift with,
                                defaults to core.resize.Point.
                                This MUST take the clip as its first positional
                                argument and a keyword argument named `src_left`.
                                Wrap your callable if it doesn't meet these
                                requirements to prevent errors.
    :return: vs.VideoNode:      The input clip, but without chroma shift.
    """
    _fname = "rvsfunc chromashifter:"
    if not clip.format.color_family is vs.YUV:
        raise vs.Error(f"{_fname} The clip MUST be of the YUV color family. \
                       Please convert it before calling this function.")
    if clip.format.num_planes < 3:
        raise vs.Error(f"{_fname} This function requires all three planes in \
                       order to calculate proper shifts.")

    def frame_to_array(frame: vs.VideoFrame) -> np.ndarray:
        frame_array = []
        for plane in range(frame.format.num_planes):
            plane_array = np.array(frame.get_read_array(plane), copy=False)
            frame_array.append(plane_array.reshape(list(plane_array.shape) + [1]))
        return np.concatenate(frame_array, axis=2)

    def get_shifted(n: int, f: vs.VideoFrame) -> int:
        array = frame_to_array(f)
        array_above = array > wthresh
        row_first = np.argmax(array_above, axis=1)
        shifts = []
        for row, luma_col in enumerate(row_first[:, 0]):
            if not array_above[row, luma_col, 0]:
                continue
            try:  # some edgecase frames produce 0 divisions
                if (
                    array_above[row, row_first[row, 1], 1]
                    and row_first[row, 1] <= row_first[row, 2]
                ):
                    shifts.append(
                        256 / round((wthresh + 1) * (((row_first[row, 1] - luma_col) + 1) / 8))
                    )
                    continue
                if array_above[row, row_first[row, 2], 2]:
                    shifts.append(
                        256 / round((wthresh + 1) * (((row_first[row, 2] - luma_col) + 1) / 8))
                    )
            except ZeroDivisionError:
                continue
        try:
            shift = sum(shifts) / len(shifts)
            if shift > 2 or shift < -2:
                shift = shift - (floor(shift) / 2)
        except ZeroDivisionError:
            shift = 0
        shift = round(shift * 8)/8
        return shifter(clip, src_left=shift)

    if vertical:
        clip = core.std.Transpose(clip)
    yuv = clip.resize.Spline36(height=clip.height * 4, width=clip.width * 4, format=vs.YUV444P8)
    if maskfunc is core.std.Prewitt:
        mask_kwargs["planes"] = [0,1,2]
    yuv = maskfunc(yuv, **mask_kwargs)

    out = core.std.FrameEval(clip, get_shifted, yuv)
    out = core.std.ShufflePlanes([clip, out], [0, 1, 2], vs.YUV)
    if vertical:
        out = core.std.Transpose(out)
    return out
