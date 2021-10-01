.. _errors:

Errors raised in rvsfunc
========================

There's a couple of situations that may occur when using rvsfunc that aren't
quite supported by the functions you might be using. This is a list of errors
that may occur when using some of the functions.

They're generally nothing major to be concerned about and fairly easy to fix.
Especially since they tend to be for situations where special handling is
required like VarRes or variable format video.

.. autosummary::
   :nosignatures:

   rvsfunc.errors.VariableFormatError
   rvsfunc..errors.VariableResolutionError
   rvsfunc.errors.YUVError
