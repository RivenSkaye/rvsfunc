.. rvsfunc documentation master file, created by
   sphinx-quickstart on Tue Aug 31 12:29:35 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Docs for rvsfunc
===================================

.. toctree::
   :maxdepth: 3
   :caption: Contents:

About
=====

.. automodule:: rvsfunc
   :members:
   :undoc-members:
   :show-inheritance:

Dependencies
============

rvsfunc requires a couple other things to work properly:

* `VapourSynth <https://github.com/vapoursynth/vapoursynth/releases>`_
* `vsutil <https://pypi.org/project/vsutil/>`_
* `numpy <https://pypi.org/project/numpy>`_

Additionally, the rescaling functionality requires:
* `nnedi3_rpow2 <https://gist.github.com/4re/342624c9e1a144a696c6>`_

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

Modules
=======

.. autosummary::
   rvsfunc.utils
   rvsfunc.masking
   rvsfunc.dvd
   rvsfunc.cursed

rvsfunc.utils
=============

.. autosummary::
   rvsfunc.utils.batch_index
   rvsfunc.utils.nc_splice
   rvsfunc.utils.copy_credits

.. automodule:: rvsfunc.utils
   :members:
   :undoc-members:
   :show-inheritance:

rvsfunc.masking
===============

.. autosummary::
   rvsfunc.masking.scradit_mask
   rvsfunc.masking.detail_mask
   rvsfunc.masking.dehalo_mask
   rvsfunc.masking.fineline_mask

.. automodule:: rvsfunc.masking
   :members:
   :undoc-members:
   :show-inheritance:

rvsfunc.dvd
===========

.. autosummary::
   rvsfunc.dvd.eoe_convolution
   rvsfunc.dvd.chromashifter

.. automodule:: rvsfunc.dvd
   :members:
   :undoc-members:
   :show-inheritance:

rvsfunc.voodoo
==============

.. autosummary::
   rvsfunc.voodoo.questionable_rescale

.. automodule:: rvsfunc.cursed
   :members:
   :undoc-members:
   :show-inheritance:

Credits
=======

Shoutout to all the great people that contribute to rvsfunc, if you want your
name on this list, feel free to fork & PR your contributions.

All of them can be seen `on GitHub <https://github.com/RivenSkaye/rvsfunc/graphs/contributors>`_

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
