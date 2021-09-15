# rvsfunc

[![Documentation Status](https://readthedocs.org/projects/rvsfunc/badge/?version=latest)](https://rvsfunc.tae.moe/en/latest/?badge=latest)
[![PyPI](https://img.shields.io/pypi/v/rvsfunc?color=green&style=plastic)](https://pypi.org/project/rvsfunc)
[![PyPI - Format](https://img.shields.io/pypi/format/rvsfunc?logo=python&style=plastic)](https://pypi.org/project/rvsfunc)
![GitHub last commit (branch)](https://img.shields.io/github/last-commit/RivenSkaye/rvsfunc/master?logo=github&logoColor=lightblue&style=plastic)
![GitHub (Pre-)Release Date](https://img.shields.io/github/release-date-pre/RivenSkaye/rvsfunc?logo=github&logoColor=lightblue&style=plastic)


A collection of vapoursynth functions I wrote or changed to make life easier.
Most of these were because I'm too lazy for my own good, or out of desperation
and edgecases.
That said, they _were_ written with reusability and flexibility in mind.
Good luck figuring out which functions you need, [docs can be found here](https://rvsfunc.tae.moe/en/latest/#dependencies)

# Recommended use

Like so many other VapourSynth \*func scripts, import it and use the functions inside.
```py
import vapoursynth as vs
import rvsfunc as INOX # Dutch people will get the joke
import literally_any_other_func as laof
```

# Installation

At some point this was a monolithic `.py` file. Delete that if you still have
it lingering on your system. Should be hidden in your `site-packages`.
As for installing this, it's on [PyPI](https://pypi.org/project/rvsfunc/),
so all you need is pip!

Assuming Python 3.8+ is configured as the default, otherwise use `python3`,
`python -3` or `py -3`:
```py
# windows
> py -m pip install rvsfunc

# Unix-like OSes
$ python -m pip install rvsfunc
```

# Requirements not on PyPI

rvsfunc has a couple of dependencies that are not available on PyPI.
I try to keep these to a minimum and as the list grows I expect it to be
mostly VapourSynth plugins. You can usually get these through [VSRepo](https://github.com/vapoursynth/vsrepo),
or perhaps you can find them on [VSDB](https://vsdb.top/).
_When grabbing from VSDB follow the links to the home URL of a project as it's horribly outdated._

The list is not exhaustive however, and doesn't list dependencies of dependencies.
For the full list of requirements not on pip, check [the docs](https://rvsfunc.tae.moe/en/latest/#dependencies)

# Contributing

[Contributing guidelines can be found in the relevant file.](./CONTRIBUTING.md)
