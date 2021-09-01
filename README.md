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

Assuming Python 3.8+ is configured as the default, otherwise use `python3`:
```py
# windows
py -m pip install rvsfunc

# Unix-like OSes
python -m pip install rvsfunc
```
