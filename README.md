# rvsfunc

A collection of vapoursynth functions I wrote or changed to make life easier.
Most of these were because I'm too lazy for my own good, or out of desperation
and edgecases.
That said, most of them were written with reusability and flexibility in mind.
Good luck figuring out which functions you need, docs coming soon&trade;

# Recommended use

Like so many other VapourSynth \*func scripts, import it and use the functions inside.
```py
import vapoursynth as vs
import rvsfunc as rvs
import literally_any_other_func as laof
```

# Installation

If you were one of the unlucky few to get this thing as a monolithic file,
then delete that first.
As for installing this, it's not yet on PyPI, so you'll have to install it using
the git link.

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
or perhaps you can find them on [VSDB](https://vsdb.top/). _When grabbing from VSDB follow the
links to the home URL of a project as it's horribly outdated._
The list is not exhaustive however, and doesn't list dependencies of dependencies.

These will be listed in the docs provided soon&#0153;, as well as being added
to the next release version of rvsfunc in a zip file.

# Contributing

If you wish to contribute by adding new things or improving existing code,
please do make sure to install the requirements for the project.
```bash
$ git clone https://github.com/RivenSkaye/rvsfunc && cd rvsfunc
$ python -m pip install -r requirements-dev.txt
```
If you wish to use virtualenvs or if you have another version of rvsfunc
installed, good luck. I expect contributors to be able to solve this.
If you'd instead like to install a development version so you can both
contribute and use all the latest code, follow the previous steps with
```bash
$ python -m pip uninstall rvsfunc
$ python -m pip install -e rvsfunc
```

Currently in dire need of someone willing to help me with getting the docs
set up and working.
