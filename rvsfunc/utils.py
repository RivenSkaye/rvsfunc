"""
Easy livin' functions, utilities that don't match a category.

The functions in this module are mostly things that don't fit in with the
other categories but aren't really worth making a new module over.
This module will end up mostly containing things like batch utilities and
project setup stuff. This should spawn some ease of use functions that I think
are missing from the well known collections like ``vsutil``.
"""

from typing import Any, Callable, Dict, List, Optional, Sequence, Union

import numpy as np
import vapoursynth as vs

from .errors import VariableFormatError, VariableResolutionError
from .masking import detail_mask


core = vs.core
vs_api_below4: Optional[bool] = None

__all__ = [
    "vs_api_below4", "is_topleft", "batch_index", "replace", "replace_ranges",
    "copy_credits", "frame_to_array"
]


def is_topleft(clip: vs.VideoNode) -> bool:
    """
    Simple function that checks if chroma is top-left aligned or not.

    In any other case it's fairly safe to assume the chroma is aligned to the
    center-left as was the default before 4K UHD BDs and Bt.2020 were a thing.
    This is basically a more complex check for BT.2020 material.
    """
    if not clip.format:
        raise VariableFormatError("is_topleft")

    if clip.format.subsampling_h != 1 or clip.format.subsampling_w != 1:
        return False

    props = clip.get_frame(0).props

    # If chromalocation is set, use it and return if it's left.
    cloc = props.get("_ChromaLocation")
    # If it exists, we just need to check if it's 2 or not
    if cloc is not None:
        return cloc == 2

    # If the primaties are set (they should be) then return if it's BT.2020
    prims = props.get("_Primaries")
    if prims not in [None, 2]:
        return prims == 9

    # These should be the minimum 4:3 and 21:9 dimensions after cropping 4K
    # with letter- and/or pillarboxing.
    return clip.width >= 2880 and clip.height >= 1645


def batch_index(
    paths: Union[List[str], str],
    source_filter: Callable[..., vs.VideoNode], show_list: bool = False,
    **src_args: Dict[str, Any]
) -> List[vs.VideoNode]:
    """
    Index sources in batch, provide a list of files to index.

    Simple lazy function. Takes a path or a list of paths, indexes them and
    then frees the memory before returning on success. If you happen to get any
    errors or exceptions, this will just raise the same thing again.

    :param paths:           A single path as a string or a List of paths.
    :param source_filter:   The source filter or indexer method to call. If it
                            doesn't write, make sure to get the list of indexes
                            using show_list.
    :param show_list:       If this is set to True, this function returns the
                            results of ``source_filter(path)`` for every path in
                            paths. Might be useful for batches as well as it
                            would just return every ``vs.VideoNode`` returned by
                            the calls to source_filter.
    :param src_args:        Any additional keyword args will be forwarded to
                            to the source filter as provided.
    """

    if not src_args:
        src_args = {}

    if isinstance(paths, str):
        paths = [paths]

    sauces = []

    try:
        for p in paths:
            sauces.append(source_filter(p, **src_args))
        if not show_list:
            del sauces
    except Exception:
        raise

    return [] if not show_list else sauces


def replace(
    clip_a: vs.VideoNode, clip_b: vs.VideoNode, range: Sequence[int],
    mismatch: bool = False
) -> vs.VideoNode:
    """
    A simple and probably underoptimized RFS implementation, because why not.

    :param clip_a:      The clip to replace frames in.
    :param clip_b:      The clip to replace frames from ``clip_a`` with.
    :param range:       A sequence containing exactly 2 ints. Any more will be
                        ignored without warning. User error is not my problem.
    :param mismatch:    A bool whether or not to allow splicing variable
                        resolutions or formats together.
    """
    if (
        not clip_a.format
        or not clip_b.format
        or clip_a.format != clip_b.format
    ):
        raise VariableFormatError("replace / rfs")

    if not mismatch and (
            not clip_a.width or not clip_b.width
            or not clip_a.height or not clip_b.height
            or clip_a.width != clip_b.width
            or clip_a.height != clip_b.height
    ):
        raise VariableResolutionError("replace / rfs")

    ra = range[0]
    rb = range[1]
    if ra > rb:
        raise ValueError("replace / rfs: The start can't be after the end!")

    clips = [clip_a[:ra], clip_b[ra:rb]]
    if rb < (clip_a.num_frames - 1):
        clips.append(clip_a[rb:])

    return core.std.Splice(clips, mismatch=mismatch)


def replace_ranges(
    clip_a: vs.VideoNode, clip_b: vs.VideoNode,
    ranges: Union[Sequence[Sequence[int]], Sequence[int]],
    mismatch: bool = False
) -> vs.VideoNode:
    """
    Replace frames in bulk, mostly useful for scenefiltering.

    :param clip_a:      The clip to replace frames in.
    :param clip_b:      The clip to replace frames from ``clip_a`` with.
    :param ranges:      Either a ``Sequence`` of ``int``, or a ``Sequence`` of
                        ``Sequence`` of ``int``. Ranges to replace.
    :param mismatch:    Whether or not to allow mismatched formats and resolutions.
    """
    if isinstance(ranges, Sequence):
        if isinstance(ranges[0], int) and isinstance(ranges[1], int):
            return replace(clip_a, clip_b, (ranges[0], ranges[1]), mismatch)

    for range in ranges:
        assert isinstance(range, Sequence)
        clip_a = replace(clip_a, clip_b, range, mismatch)

    return clip_a


def copy_credits(
    source: vs.VideoNode, nc: vs.VideoNode,
    mask: Optional[vs.VideoNode] = None
) -> vs.VideoNode:
    """
    Copy credits from source to the nc using a mask.

    This function internally calls :py:func:`.masking.detail_mask` which is
    meant for descales. As such, it assumes the NC doesn't have major
    differences with the source as they are provided.
    Assumes both inputs have the same length.

    :param source:      The clip to take the credits from.
    :param nc:          The NC to copy the credits into.
    :param mask:        Optional, an external mask to use.
    """

    mask = detail_mask(source, nc) if not mask else mask

    return core.std.MaskedMerge(nc, source, mask)


def frame_to_array(f: vs.VideoFrame) -> np.ndarray:
    """
    Simple wrapper to turn a video frame into an numpy array
    """
    global vs_api_below4
    if vs_api_below4 is None:
        vs_api_below4 = vs.__api_version__.api_major < 4  # type: ignore
    return np.dstack([
        f.get_read_array(p) for p in range(f.format.num_planes)  # type: ignore
    ] if vs_api_below4 else f)
