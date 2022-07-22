"""
A module for functions built on NNEDI3 plugins in a more modern fashion.

This module defines a few classes that have been set up to wrap around NNEDI3
implementations. They allow for using them in a streamlined fashion with sane
defaults. The main objective is to provide a collection of NNEDI3-based functions
in a central place, as well as modernizing them.
"""


from abc import ABCMeta, abstractmethod
from typing import Any, List, Type, TypeVar

import vapoursynth as vs
import vsutil

from .errors import VariableFormatError


core = vs.core

__all__ = [
    "NNEDI3", "NNEDI3CL", "ZNEDI3"
]


class NNEDI3Base(metaclass=ABCMeta):
    """
    Abstract Base Class for NNEDI3 wrappers.

    This is currently mainly in use for a modernized and properly functional
    version of nnedi3_rpow2, which is available as a classmethod for all of
    the implementing classes.

    This is a generalized base class that aims to implement generic functions
    that can be performed with every NNEDI3 plugin. To define plugin-specific
    functionality and behavior, the implementing subclasses are used.
    Documentation in this class applies to *all* subclasses as well.

    :param shift:           Whether or not to fix the chroma shift caused by the
                            upsampling of subsampled chroma.
    :param nnedi_kwargs:    Additional kwargs to pass on to the NNEDI3 plugin.
    """

    NB = TypeVar("NB", bound="NNEDI3Base")

    def __init__(self, shift: bool = True, **nnedi_kwargs: Any):
        self.shift = shift
        self.kwargs = nnedi_kwargs

    @abstractmethod
    def nnedi(self, clip: vs.VideoNode, field: int, **kwargs: Any) -> vs.VideoNode:
        """
        A simple wrapper function for calling a NNEDI3 implementation.

        This abstractmethod and all concrete implementations only make the
        call to the NNEDI3 implementation a subclass wraps around. Any other
        logic being applied such as using NNEDI3 for AA must be a different
        function that calls this method instead of the actual plugin.
        ``*args`` should be blindly passed to the plugin and ``**kwargs``
        should be used to update a predefined dict of defaults defined in the
        implementations of this method.

        :param clip:        The clip to call the NNEDI3 plugin with.
        :param field:       The ``field`` parameter for NNEDI3.
        """
        ...

    def double_size(self, clip: vs.VideoNode, chroma: bool = True,
                    iterations: int = 1) -> vs.VideoNode:
        """
        nnedi3_rpow2, except not bad. This does the acual rpow2'ing.

        Uses a much simpler API than the original that assumes kwargs were
        passed during instantiation of the class.

        :param clip:        The clip to grow by powers of two.
        :param chroma:      Whether or not to process chroma.
        :param iterations:  How often to double frame sizes.
                            This growth is exponential (2x, 4x, 8, ...)
        """

        # The amount of iterations has to be at least 1 and no more than 10.
        if not 1 <= iterations <= 11:
            raise ValueError("The amount of iterations for rpow2 may not "
                             "be lower than 1 or higher than 10")

        if not clip.format:
            raise VariableFormatError("rpow2")

        if clip.format.num_planes == 1:
            chroma = False
            planes = [clip]
        else:
            amnt = 3 if chroma else 1
            planes = vsutil.split(clip)[:amnt]

        powd: List[vs.VideoNode] = []

        for plane in planes:
            plane_iters = iterations
            src_left = 0.0
            src_top = 0.0
            while plane_iters > 0:
                sx = sy = 0.0
                # Setting field=1 ends up with a smaller shift
                plane = self.nnedi(plane, 1, **self.kwargs).std.Transpose()
                plane = self.nnedi(plane, 1, **self.kwargs).std.Transpose()
                # Apply chroma shift only if wanted AND needed
                # Apply the chroma shift formula:
                # 0.25 - (0.25 * (src.width / dst.width)) = 0.25 - (0.25 * 0.5)
                # = 0.25 - 0.125 = 0.125 and the NNEDI doubling shift is 0.5 - field
                # Y: shift + 0 = shift
                # U & V: shift + 0.125 -> -0.5 + 0.125 = -0.375
                sx = -0.375 if self.shift and len(powd) > 0 else -0.5
                sy = -0.5
                src_left += src_left + sx
                src_top += src_top + sy
                plane_iters -= 1

            plane = plane.resize.Bicubic(src_left=src_left, src_top=src_top)
            powd.append(plane)

        if not chroma or len(powd) == 1:
            return powd[0]
        else:
            return vsutil.join(powd, family=clip.format.color_family)

    @classmethod
    def rpow2(cls: Type[NB], clip: vs.VideoNode, chroma: bool = True,
              iterations: int = 1, shift: bool = True,
              **nnedi_kwargs: Any) -> vs.VideoNode:
        """
        nnedi3_rpow2 as a classmethod for easy use.

        **This function is NOT a drop-in replacement for 4re's**
        `nnedi3_rpow2 <https://gist.github.com/4re/342624c9e1a144a696c6>`_

        Having gotten that out of the way, the function signature is heavily
        simplified compared to the old one and so is the ``iterations`` argument
        that replaces the old ``rfactor``.

        :param clip:            The clip to exponentially double in size.
        :param chroma:          Whether or not to process chroma.
        :param iterations:      How often to double the clip's sizes.
                                This is exponential growth (2x, 4x, 8x, ...)
        :param shift:           Whether or not to fix the chroma shift caused by
                                upsampling video.
        :param nnedi_kwargs:    Additional kwargs to pass to NNEDI3.
                                See :py:meth:`nnedi` for more information.
        """
        nn = cls(shift=shift, **nnedi_kwargs)
        return nn.double_size(clip, chroma, iterations)


class ZNEDI3(NNEDI3Base):
    """
    A wrapper for the znedi3 plugin.
    """
    def __init__(self, shift: bool = True, **nnedi_kwargs: Any):
        super().__init__(shift, **nnedi_kwargs)

    def nnedi(self, clip: vs.VideoNode, field: int, **kwargs: Any) -> vs.VideoNode:
        nnkw = {
            "dh": True,
            "planes": 0,
            "nsize": 0,
            "nns": 3,
            "qual": 2,
            "opt": True
        }
        nnkw.update(self.kwargs)
        nnkw.update(kwargs)

        return core.znedi3.nnedi3(clip, field=field, **nnkw)  # type: ignore


class NNEDI3(NNEDI3Base):
    """
    A wrapper for the nnedi3 plugin.
    """
    def __init__(self, shift: bool = True, **nnedi_kwargs: Any):
        super().__init__(shift, **nnedi_kwargs)

    def nnedi(self, clip: vs.VideoNode, field: int, **kwargs: Any) -> vs.VideoNode:
        nnkw = {
            "dh": True,
            "planes": 0,
            "nsize": 0,
            "nns": 3,
            "qual": 2,
            "opt": True
        }
        nnkw.update(self.kwargs)
        nnkw.update(kwargs)

        return core.nnedi3.nnedi3(clip, field=field, **nnkw)


class NNEDI3CL(NNEDI3Base):
    """
    A wrapper for the NNEDI3CL plugin.
    """
    def __init__(self, shift: bool = True, **nnedi_kwargs: Any):
        super().__init__(shift, **nnedi_kwargs)

    def nnedi(self, clip: vs.VideoNode, field: int, **kwargs: Any) -> vs.VideoNode:
        nnkw = {
            "dh": True,
            "dw": False,
            "planes": 0,
            "nsize": 0,
            "nns": 3,
            "qual": 2
        }
        nnkw.update(self.kwargs)
        nnkw.update(kwargs)

        return core.nnedi3cl.NNEDI3CL(clip, field=field, **nnkw)
