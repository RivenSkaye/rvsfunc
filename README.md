# rvsfunc
A collection of vapoursynth functions I wrote to make life easier. There's better alternatives, trust me.

Most of these functions were written for edgecases where their normal counterparts don't work.
That said, some of it is actually reusable for the more general use cases as well. Good luck
figuring out which functions you need from this. I feel sorry for you for needing the dependency.

# Recommended use
Like so many other VapourSynth \*func scripts, import it and use the functions inside.
```py
import vapoursynth as vs
import rvsfunc as rvs # realize you must be desperate if you do this
import literally_any_good_func as lagf
```

# Installation
Until this thing grows massive and it deserves to be a package, just
save the `rvsfunc.py` file in your site-packages folder.

Alternatively, to keep the VapourSynth stuff separated from all other Python stuff,
save all of them into `$PYTHONPATH/vsfuncs/`. Or save this specifically to
`$PYTHONPATH/trash/rvsfunc.py` so you can do `from trash import rvsfunc as rvs`.
