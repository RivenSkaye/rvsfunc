"""
A collection of VapourSynth stuff I wrote or mangled to make life easier.

Most of these were because I'm too lazy for my own good, some out of
desperation and edgecases.
That said, most of them were written with reusability and flexibility in mind.
The main goal is to make the functions as flexible as possible, while still
trying to keep sane defaults so minimum use should produce nice results.
Good luck figuring out which functions you need, docs came soon™!

If you spot any issues, you can find me on Discord as @Riven Skaye#0042.
You're also more than welcome to create an issue on GitHub,
`or make a PR <https://github.com/RivenSkaye/rvsfunc/blob/master/CONTRIBUTING.md>`_!
"""

from . import utils, masking, dvd, cursed
from .NNEDI3 import NNEDI3, ZNEDI3, NNEDI3CL

# Alias for script compatibility
batchindex = utils.batch_index

# aliases for shits and giggles
voodoo = cursed
