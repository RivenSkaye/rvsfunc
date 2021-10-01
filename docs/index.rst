Welcome to the documentation for rvsfunc!
=========================================

Modules:

.. toctree::
    :maxdepth: 3

    errors
    edgecase
    dvd
    masking
    NNEDI3
    utils

.. automodule:: rvsfunc
    :members:

Documentation for individual modules can be found to the left.

Dependencies
============

rvsfunc requires a couple other things to work properly:

* `VapourSynth <https://github.com/vapoursynth/vapoursynth/releases>`_

  * rvsfunc *should* be compatible with both APIv3 and APIv4
* `vsutil <https://pypi.org/project/vsutil/>`_
* `numpy <https://pypi.org/project/numpy>`_
* `VapourSynth-descale <https://github.com/Irrational-Encoding-Wizardry/vapoursynth-descale>`_
* `ZNEDI3 <https://github.com/sekrit-twc/znedi3>`_

  * This is only required for :py:meth:`rvsfunc.edgecase.questionable_rescale`,
  * Other NNEDI plugins can be used with the :ref:`NNEDI3` as well.

Each of these dependencies may have their own dependencies, it is not my
responsibility to maintain an exhaustive list. Typically any dependencies
will be available on free platforms like GitHub or GitLab, or they can be found
on the doom9 forums.

Disclaimer
==========

An effort will be made to keep minor updates compatible, though internals and
defaults may change without warning. There are no guarantees being made with
regards to the exposed (sub)modules, functions, names and aliases. In the case
of major and/or breaking changes, the affected versions will be listed on the
relevant `PyPI page <https://pypi.org/project/rvsfunc/>`_ and in the README.md
available on `Github <https://github.com/RivenSkaye/rvsfunc/>`_
One should expect any non-patch upgrade to come with the risk of breakage.
