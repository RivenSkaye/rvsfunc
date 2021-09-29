from .errors import VariableFormatError
from .utils import is_topleft
from abc import ABCMeta, abstractmethod
from typing import Any, Type, TypeVar
import vsutil
import vapoursynth as vs

core = vs.core


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
    def nnedi(self, clip: vs.VideoNode, field: int,
              *args: Any, **kwargs: Any) -> vs.VideoNode:
        """
        A simple wrapper function for calling a NNEDI3 implementation.

        This abstractmethod and all concrete implementations only make the
        call to the NNEDI3 implementation a subclass wraps around. Any other
        logic being applied such as using NNEDI3 for AA must be a different
        function that calls this method instead of the actual plugin.
        ``*args`` should be blindly passed to the plugin and ``*kwargs``
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
        if not 1 <= iterations <= 10:
            raise ValueError("The amount of iterations for rpow2 may not "
                             "be lower than 1 or higher than 9")

        if not clip.format:
            raise VariableFormatError("rpow2")

        if clip.format.num_planes == 1:
            chroma = False
            planes = [clip]
        else:
            amnt = 3 if chroma else 1
            tl = is_topleft(clip) if chroma else False
            planes = vsutil.split(clip)[:amnt]

        powd = []
        planenum = 0

        for plane in planes:
            plane_iters = iterations
            while plane_iters > 0:
                # No fuckery with field since we're splitting planes
                # Always use field 0 to keep center alignment
                # Which is how luma and gray are aligned and should be handled
                plane = self.nnedi(plane, 0, **self.kwargs).std.Transpose()
                plane = self.nnedi(plane, 0, **self.kwargs).std.Transpose()
                plane_iters -= 1

            if self.shift and planenum > 0:
                sh = clip.format.subsampling_h not in [0, 2] and tl
                sw = clip.format.subsampling_w not in [0, 2]
                shift = 0.25 - (0.25 * (clip.width / planes[0].width))
                plane = plane.resize.Spline36(src_left=shift if sw else 0.0,
                                              src_top=shift if sh else 0.0)
            powd.append(plane)
            planenum += 1

        if not chroma or len(powd) == 1:
            return powd[0]
        else:
            return core.std.ShufflePlanes(clips=powd, planes=[0, 0, 0],
                                          colorfamily=clip.format.color_family)

    @classmethod
    def rpow2(cls: Type[NB], clip: vs.VideoNode, chroma: bool = True,
              iterations: int = 1, shift: bool = True,
              **nnedi_kwargs: Any) -> vs.VideoNode:
        """
        nnedi3_rpow2 as a classmethod for easy use.

        **THIS FUNCTION IS NOT API-COMPATIBLE WITH 4re's ``nnedi3_rpow2``!**
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
                                See the ``nnedi`` function for more information.
        """
        nn = cls(shift=shift, **nnedi_kwargs)
        return nn.double_size(clip, chroma, iterations)


class ZNEDI3(NNEDI3Base):
    """
    A wrapper for the znedi3 plugin, also available as ``rvsfunc.znedi3``.
    """
    def __init__(self, shift: bool = True, **nnedi_kwargs: Any):
        super().__init__(shift, **nnedi_kwargs)

    def nnedi(self, clip: vs.VideoNode, field: int,
              *args: Any, **kwargs: Any) -> vs.VideoNode:
        nnkw = {
            "dh": True,
            "planes": 0,
            "nsize": 0,
            "nns": 3,
            "opt": True
        }
        nnkw.update(self.kwargs)
        nnkw.update(kwargs)

        return core.znedi3.nnedi3(clip, field=field, **nnkw)  # type: ignore


class NNEDI3(NNEDI3Base):
    """
    A wrapper for the nnedi3 plugin, also available as ``rvsfunc.nnedi3``.
    """
    def __init__(self, shift: bool = True, **nnedi_kwargs: Any):
        super().__init__(shift, **nnedi_kwargs)

    def nnedi(self, clip: vs.VideoNode, field: int,
              *args: Any, **kwargs: Any) -> vs.VideoNode:
        nnkw = {
            "dh": True,
            "planes": 0,
            "nsize": 0,
            "nns": 3,
            "opt": True
        }
        nnkw.update(self.kwargs)
        nnkw.update(kwargs)

        return core.nnedi3.nnedi3(clip, field=field, **nnkw)


class NNEDI3CL(NNEDI3Base):
    """
    A wrapper for the NNEDI3CL plugin, also available as ``rvsfunc.nnedi3cl``.
    """
    def __init__(self, shift: bool = True, **nnedi_kwargs: Any):
        super().__init__(shift, **nnedi_kwargs)

    def nnedi(self, clip: vs.VideoNode, field: int,
              *args: Any, **kwargs: Any) -> vs.VideoNode:
        nnkw = {
            "dh": True,
            "dw": False,
            "planes": 0,
            "nsize": 0,
            "nns": 3,
            "opt": True
        }
        nnkw.update(self.kwargs)
        nnkw.update(kwargs)

        return core.nnedi3cl.NNEDI3CL(clip, field=field, **nnkw)
