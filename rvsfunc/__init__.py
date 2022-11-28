"""
A collection of VapourSynth stuff I wrote or mangled to make life easier.

Most of these were because I'm too lazy for my own good, some out of
desperation and edgecases.
That said, most of them were written with reusability and flexibility in mind.
The main goal is to make the functions as flexible as possible, while still
trying to keep sane defaults so minimum use should produce nice results.
Good luck figuring out which functions you need, docs arrived!

If you spot any issues, you can find me on Discord as @Riven Skaye#0042.
You're also more than welcome to create an issue on GitHub,
`or make a PR <https://github.com/RivenSkaye/rvsfunc/blob/master/CONTRIBUTING.md>`_!
"""

from . import NNEDI3, dvd, edgecase, errors, masking, utils

__all__ = [
    "batchindex", "dvd", "edgecase", "errors", "masking",
    "nnedi3", "nnedi3cl", "utils", "znedi3"
]

# Alias for script compatibility
batchindex = utils.batch_index

# Utility aliases
znedi3 = NNEDI3.ZNEDI3
nnedi3 = NNEDI3.NNEDI3
nnedi3cl = NNEDI3.NNEDI3CL


def _get_ver() -> str:
    from pathlib import Path
    fdir = Path(__file__).absolute().parent
    with open(f"{fdir}/.version") as v:
        return v.read().strip()


__version__ = _get_ver()
