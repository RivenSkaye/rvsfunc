from typing import Union, Optional, Callable, Any, List, Dict
import vsutil
import vapoursynth as vs
core = vs.core

def batch_index(paths: Union[List[str],str], source_filter: Callable[[str], Any],
               show_list: bool=False, **src_args: Any) -> List[Any]:
    """ Index sources in batch, provide a list of files to index.

    Simple lazy function. Takes a path or a list of paths, indexes them and
    then frees the memory again before returning on success. If you happen
    to get any errors or exceptions, this will just raise the same thing again.

    :param paths:           A single path as a string or a List of paths.
    :param source_filter:   The source filter or indexer method to call. If it
                            doesn't write, make sure to get the list of indexes
                            using show_list.
    :param show_list:       If this is set to True, this function returns the
                            results of `source_filter(path)` for every path in
                            paths. Might be useful for batches as well as it
                            would just return the `vs.VideoNode`s returned by
                            the calls to source_filter.
    :param **src_args:      Any additional keyword args will be forwarded to
                            to the source filter as provided.
    """
    src_args = {} if not src_args else src_args
    paths = [paths] if isinstance(paths, str) else paths
    sauces = []
    try:
        for p in paths:
            sauces.append(source_filter(p, **src_args))
        if not show_list: del sauces
    except Error as e:
        raise e
    return [] if not show_list else sauces

def nc_splice(source: vs.VideoNode, nc: vs.VideoNode, startframe: int, endframe: int,
              nc_filterfunc: Optional[Callable[[vs.VideoNode, Any], vs.VideoNode]]=None,
              use_internal: bool=False, ext_mask: Optional[vs.VideoNode]=None, **kwargs) -> vs.VideoNode:
    """ Function for splicing in video from a different source.

    The intended purpose is to splice NCs into an episode when they look better
    or when they're easier to filter. Allows for copying over the credits.

    :param source:          The source clip that needs something replaced
    :param nc:              The clip that needs to be spliced into source
    :param startframe:      The frame to start splicing at. This is an inclusive
                            selection value. The selected range is `source[:startframe]`.
    :param endframe:        The first frame that needs to be kept. This is an
                            inclusive selection value, selected as `source[endframe+1:]`.
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
    out = source[:startframe] + nc + source[endframe+1:]
    return out

def copy_credits(source: vs.VideoNode, nc: vs.VideoNode,
                 mask: Optional[vs.VideoNode]=None) -> vs.VideoNode:
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
